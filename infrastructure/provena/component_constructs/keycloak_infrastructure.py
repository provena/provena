from aws_cdk import (
    Duration,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_secretsmanager as sm,
    RemovalPolicy,
    aws_elasticloadbalancingv2 as elb
)
from constructs import Construct
from provena.custom_constructs.db_instance_from_snapshot import DBInstanceFromSnapshot
from provena.custom_constructs.load_balancers import SharedBalancers
from provena.custom_constructs.ecs_cluster import Cluster as CustomCluster
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.custom_constructs.db_instance import DBInstance
from provena.custom_constructs.oidc_provider import KeycloakOIDCProvider
from provena.custom_constructs.storage_bucket import StorageBucket
from provena.config.config_class import KeycloakConfiguration
from typing import Any, Optional, Union, Dict, List, Tuple
import json

# Path to the build dir for keycloak relative to top level of cdk infra
KC_BASE_PATH = "provena/keycloak"

KeycloakReplacementList = List[Tuple[str, str]]


def replace_keycloak_vars(input: str, targets: KeycloakReplacementList) -> str:
    for k, v in targets:
        # replace ${k} (double escape {{ for braces }})
        input = input.replace(f"${{{k}}}", v)
    return input


def customise_realm_config(
    stage: str,
    realm_name: str,
    custom_theme_name: str,
    configuration: KeycloakConfiguration
) -> str:
    """

    Performs the replacement process from a base realm config into a customised
    config.

    TODO

    Investigate if there is a less hacky approach to replace the env
    variables in the file - KC should do this but apparently only when run at
    'startup'. I thought the docker entrypoint would do this but apparently not
    (or maybe not in v16)

    e.g. https://github.com/keycloak/keycloak/issues/12069

    Args:
        stage (str): The application stage realm_name (str): The name of the kc
        realm configuration (KeycloakConfiguration): The kc configuration

    Returns:
        str: Returns the name of the outputted path relative to the kc build
        root
    """
    # source
    source_json_path = f"{KC_BASE_PATH}/realms/{stage}-realm.json"

    # dest
    dest_json_name = "customised-realm.json"
    dest_json_path = f"{KC_BASE_PATH}/{dest_json_name}"

    # read source base config
    with open(source_json_path, 'r') as f:
        source_json = f.read()

    # replacement list - these replace in the format ${name} values in the realm jsons
    replacement_list: KeycloakReplacementList = [
        ("KC_REALM_NAME", realm_name),
        ("KC_ROOT_DOMAIN", configuration.base_url),
        ("KC_DISPLAY_NAME", configuration.display_name),
        ("KC_THEME_NAME", custom_theme_name),
    ]

    # replace all mentions of realm name, root domain or display name
    output_json = replace_keycloak_vars(
        input=source_json,
        targets=replacement_list
    )

    # now write out the updated file contents
    with open(dest_json_path, 'w') as f:
        f.write(output_json)

    return dest_json_name


class KeycloakConstruct(Construct):

    def __init__(self, scope: Construct, construct_id: str,
                 stage: str,
                 vpc: ec2.Vpc,
                 realm_name: str,
                 custom_theme_name: str,
                 bucket_arn: str,
                 cert_arn: str,
                 allocator: DNSAllocator,
                 kc_db_instance_snapshot_arn: Optional[str],
                 kc_domain: str,
                 balancers: SharedBalancers,
                 https_listener_priority: int,
                 http_listener_priority: int,
                 rds_removal_policy: RemovalPolicy,
                 initial_configuration: Optional[KeycloakConfiguration],
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Should we restore from snapshot
        snapshot_mode = bool(kc_db_instance_snapshot_arn)

        db_instance: Optional[Union[DBInstance, DBInstanceFromSnapshot]]

        # Create the DB instance
        # This will be used for keycloak
        if snapshot_mode:
            # Make sure snapshot was provided
            assert kc_db_instance_snapshot_arn
            # Already have snapshot ARN
            db_instance = DBInstanceFromSnapshot(
                scope=self,
                id="dbinstance",
                service_name="db",
                stage=stage,
                vpc=vpc,
                snapshot_arn=kc_db_instance_snapshot_arn,
                public=False,
                removal_policy=rds_removal_policy
            )
        else:
            # If you don't have cluster yet and need to populate
            # This database won't have any data in it
            # Make it private
            # Will have user keycloak and default DB keycloak

            if initial_configuration is None:
                raise ValueError(
                    f"No keycloak snapshot defined, require initial configuration parameters.")

            db_instance = DBInstance(
                self,
                "dbinstance",
                "db",
                vpc=vpc,
                public=False,
                removal_policy=rds_removal_policy
            )

        # Extract endpoint
        endpoint = db_instance.instance.instance_endpoint
        db_instance_address = endpoint.hostname

        # Extract password automatically associated
        user_password_secret = db_instance.secret
        # make sure the secret is available
        assert user_password_secret

        # API map port 8080
        kc_port = 8080

        # Make sure https balancer is setup
        if balancers.alb is None:
            balancers.setup_alb(
                vpc=vpc
            )

        # Make sure https listener is setup
        if balancers.https_listener is None:
            balancers.setup_https_listener(
                certificates=[]
            )

        # Make sure http listener is setup
        if balancers.http_listener is None:
            balancers.setup_http_listener()

        # add required cert for https traffic
        balancers.add_https_certificates(
            id='kc-certs',
            certificates=[elb.ListenerCertificate.from_arn(cert_arn)]
        )

        tg = elb.ApplicationTargetGroup(
            self,
            f"tg",
            port=kc_port,
            protocol=elb.ApplicationProtocol.HTTP,
            target_type=elb.TargetType.IP,
            health_check=elb.HealthCheck(
                enabled=True,
                healthy_http_codes="200",
                protocol=elb.Protocol.HTTP,
                port=str(kc_port),
                timeout=Duration.seconds(10),
                healthy_threshold_count=5,
                unhealthy_threshold_count=5,
                interval=Duration.seconds(45)
            ),
            vpc=vpc,
            # Make sessions sticky
            stickiness_cookie_duration=Duration.days(1)
        )

        balancers.add_http_redirected_conditional_https_target(
            action_id='keycloak',
            target_group=tg,
            conditions=[elb.ListenerCondition.host_headers(
                [f"{kc_domain}.{allocator.root_domain}"]
            )],
            priority=https_listener_priority,
            http_redirect_priority=http_listener_priority
        )

        # KC admin username
        kc_admin_user_name = "admin"

        # Environment

        # Make sure these parameters match deployment
        # requirements
        kc_environment = {
            "KEYCLOAK_USER": kc_admin_user_name,
            "DB_VENDOR": "postgres",
            "DB_ADDR": db_instance_address,
            "DB_DATABASE": "keycloak",
            "DB_USER": "keycloak",
            "PROXY_ADDRESS_FORWARDING": "true",
            # Set debug log level for non production
            "KEYCLOAK_LOGLEVEL": "DEBUG"
        }

        build_args: Dict[str, str] = {
            # This specifies the folder to copy - injected for initial config
            # later
            "KC_THEME_NAME": custom_theme_name
        }

        if not snapshot_mode:
            assert initial_configuration is not None

            # slightly hacky way to perform env variable replacement as KC
            # v16.0.0 doesn't seem to support environment variables in the realm
            # config

            # source
            relevant_stage = initial_configuration.stage_override or stage
            dest_json_name = customise_realm_config(
                stage=relevant_stage,
                realm_name=realm_name,
                custom_theme_name=custom_theme_name,
                configuration=initial_configuration
            )

            kc_environment.update({
                # in the dockerfile we always copy to this path - this tells the
                # entrypoint to perform an initial import of the realm config
                "KEYCLOAK_IMPORT": "/realm-export.json",
            })
            # This specifies which stage's base config is copied
            build_args.update({
                "REALM_CONFIG_SOURCE_PATH": dest_json_name,
                # in the dockerfile we always copy to this path - this tells the
                # entrypoint to perform an initial import of the realm config
                "KEYCLOAK_IMPORT": "/realm-export.json",
            })

        kc_container = ecs.ContainerImage.from_asset(
            directory=KC_BASE_PATH,
            # We use a different build process if spinning up brand new
            file="Dockerfile" if snapshot_mode else "NewDBDockerfile",
            build_args=build_args
        )

        # Create port mappings
        kc_port_mappings = [ecs.PortMapping(
            container_port=kc_port,
            host_port=kc_port,
            protocol=ecs.Protocol.TCP
        )]

        # Create secret password for admin username
        string_template = json.dumps({
            "username": kc_admin_user_name
        })

        # Create a secret for authenticating
        secret_generator = sm.SecretStringGenerator(
            include_space=False,
            exclude_punctuation=True,
            password_length=30,
            require_each_included_type=True,
            secret_string_template=string_template,
            generate_string_key="password"
        )

        # Create secret manager admin secret
        kc_admin_secret = sm.Secret(
            scope=self,
            id="kc_admin_secret",
            description="Dynamically generated login password to admin console of keycloak cluster.",
            removal_policy=RemovalPolicy.DESTROY,
            generate_secret_string=secret_generator
        )

        # Set env and secrets
        # Secrets
        kc_secrets = {
            "DB_PASSWORD": ecs.Secret.from_secrets_manager(
                # The secret
                user_password_secret,
                # the json field containing password
                "password"
            ),
            "KEYCLOAK_PASSWORD": ecs.Secret.from_secrets_manager(
                # The secret
                kc_admin_secret,
                # the json field containing password
                "password"
            )
        }

        if stage in ['DEV', 'STAGE', 'TEST']:
            cpu = 512
            memory = 1024
        else:
            cpu = 1024
            memory = 2048

        # Create the API fargate service
        kc_service = CustomCluster(
            self,
            "kc_cluster_service",
            service_name=stage + "_kc",
            vpc=vpc,
            cpu=cpu,
            memory=memory,
            # TODO enable clustering properly
            # probably need something like
            # this https://github.com/deadlysyn/terraform-keycloak-aws/blob/main/build/keycloak/Dockerfile
            desired_count=1
        )

        # Add the container to service
        kc_service.add_container_to_service(
            service_name=stage + "_kc",
            port_mappings=kc_port_mappings,
            container=kc_container,
            environment_variables=kc_environment,
            secret_environment_variables=kc_secrets
        )

        # Allow connection to database (since db is private)
        conn = kc_service.service.connections
        db_instance.give_connectable_access(conn)

        # Attach the services to the load balancer target groups
        # and grant access
        assert balancers.alb
        tg.add_target(kc_service.service)
        kc_service.service.connections.allow_from(
            balancers.alb.connections, port_range=ec2.Port.tcp_range(
                start_port=8080, end_port=8080),
            description="Allowing balancer connection to fargate service.")

        # Setup auto scaling capacity
        min_instances = 1
        max_instances = 1
        requests_per_instance = 10
        scale_in_cooldown = 60
        scale_out_cooldown = 30

        scaling = kc_service.service.auto_scale_task_count(
            min_capacity=min_instances,
            max_capacity=max_instances
        )

        scaling.scale_on_request_count(
            id=f"scaling",
            target_group=tg,
            requests_per_target=requests_per_instance,
            scale_in_cooldown=Duration.seconds(scale_in_cooldown),
            scale_out_cooldown=Duration.seconds(scale_out_cooldown)
        )

        # Add the load balancer address
        # for the API
        record = allocator.add_load_balancer(
            "kc_dns_record",
            domain_prefix=kc_domain,
            load_balancer=balancers.alb,
            comment=stage + " KC Load Balancer DNS target"
        )

        # entity ID for OIDC
        entity_id_full_url = f"https://{kc_domain}.{allocator.root_domain}/auth/realms/{realm_name}"
        entity_id_qualified_domain = f"{kc_domain}.{allocator.root_domain}/auth/realms/{realm_name}"

        self.keycloak_auth_endpoint = entity_id_full_url

        # Client ids from keycloak
        # These are not IAM roles just client

        # These are no longer used DEPRECATED
        # oidc_read_only_client_id = "read_only_oidc_aws"
        # oidc_read_write_client_id = "read_write_oidc_aws"
        # oidc_admin_client_id = "admin_oidc_aws"

        oidc_service_client_id = "service_account_oidc_aws"

        client_ids = [
            # oidc_read_only_client_id,
            # oidc_read_write_client_id,
            # oidc_admin_client_id,
            oidc_service_client_id]

        # Setup the service provider for keycloak

        # DEPRECATED - OIDC is used now
        # saml_provider = KeycloakSAMLProvider(
        #    scope=self,
        #    construct_id="kc_saml_provider",
        #    stage=stage,
        #    provider_name=stage + "-keycloak-saml-provider"
        # )

        oidc_provider = KeycloakOIDCProvider(
            self, "kc_oidc_provider", entity_id_full_url, entity_id_qualified_domain, client_ids, record)

        # Create read only roles
        # saml_read_role = saml_provider.add_role(stage + "-saml_read_only")
        # oidc_read_role = oidc_provider.add_role(
        #    "oidc_read_only", oidc_read_only_client_id)

        # Create read-write roles
        # saml_read_write_role = saml_provider.add_role(
        #    stage + "-saml_read_write")
        # oidc_read_write_role = oidc_provider.add_role(
        #    "oidc_read_write", oidc_read_write_client_id)

        # Create admin roles
        # saml_admin_role = saml_provider.add_role(stage + "-saml_bucket_admin")
        # oidc_admin_role = oidc_provider.add_role(
        #    "oidc_bucket_admin", oidc_admin_client_id)

        # Create OIDC special service role
        oidc_service_role = oidc_provider.add_role(
            "oidc_bucket_service", oidc_service_client_id, role_name=stage + "-oidc_bucket_service", max_session_duration=Duration.hours(12))
        self.oidc_bucket_service_role: iam.Role = oidc_service_role

        # Setup storage bucket
        storage_bucket = StorageBucket(self, "provena-storage-bucket",
                                       bucket_arn=bucket_arn)

        # Add permissions

        # saml
        # storage_bucket.add_read_only(saml_read_role)
        # storage_bucket.add_read_write(saml_read_write_role)
        # storage_bucket.add_bucket_admin(saml_admin_role)

        # oidc
        # storage_bucket.add_read_only(oidc_read_role)
        # storage_bucket.add_read_write(oidc_read_write_role)
        # storage_bucket.add_bucket_admin(oidc_admin_role)
        storage_bucket.add_bucket_admin(oidc_service_role)

        # expose the instance
        self.db_instance_construct = db_instance
