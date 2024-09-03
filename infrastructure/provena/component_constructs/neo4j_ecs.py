from aws_cdk import (
    aws_ecs as ecs,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_secretsmanager as sm,
    aws_logs as logs,
    aws_efs as efs,
    RemovalPolicy,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions
)

from constructs import Construct
from typing import Any
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.custom_constructs.load_balancers import *

class Neo4jECS(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            stage: str,
            http_instance_domain: str,
            bolt_instance_domain: str,
            vpc: ec2.Vpc,
            allocator: DNSAllocator,
            balancers: SharedBalancers,
            http_priority: int, 
            efs_root_path: str,
            neo4j_auth_arn: str,
            neo4j_cpu_size: int, 
            neo4j_memory_size: int,
            efs_service_instance_required: bool = True,
            service_instance_role_arn: Optional[str] = None,
            efs_removal_policy: RemovalPolicy = RemovalPolicy.RETAIN,
            **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # Networking
        tcp_port = 7687
        http_port = 7474

        # make sure http and tcp setup on shared balancers
        if balancers.http_listener is None:
            if balancers.alb is None:
                balancers.setup_alb(
                    vpc=vpc
                )
            balancers.setup_http_listener()
        if balancers.nlb is None:
            balancers.setup_nlb(vpc=vpc)

        # everything good to go for balancers

        # EFS (for persistence)
        file_system = efs.FileSystem(
            scope=self,
            id='Neo4jEFS',
            vpc=vpc,

            # We are going to backup "manually" with AWS Backup
            enable_automatic_backups=False,
            encrypted=True,

            # Currently no lifecycle policy i.e. no IA transition
            # lifecycle_policy

            # General purpose performance, don't need MAX IO (yet)
            # Note - changing this requires replacement
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,

            # Take a snapshot if removed
            # Snapshot is not supported
            # removal_policy=RemovalPolicy.SNAPSHOT,

            # Performance scales as required
            throughput_mode=efs.ThroughputMode.BURSTING,

            # Put into private part of vpc - we can allow inbound traffic as
            # required
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),

            # Depending on specified removal policy
            removal_policy=efs_removal_policy
        )

        if efs_service_instance_required:
            # Create a small EFS service EC2 instance

            # Dev role
            assert service_instance_role_arn is not None
            dev_role = iam.Role.from_role_arn(
                self, 'ec2-dev-role', service_instance_role_arn)

            # Create instance

            efs_service_instance = ec2.Instance(
                scope=self,
                id='efs-service-instance',
                instance_type=ec2.InstanceType.of(instance_class=ec2.InstanceClass.T3,
                                                  instance_size=ec2.InstanceSize.MICRO),
                # use latest amazon linux - cache in context to avoid recreation
                machine_image=ec2.MachineImage.latest_amazon_linux(
                    cached_in_context=True),

                vpc_subnets=ec2.SubnetSelection(
                    # Allows outbound without NAT - not to be used for sensitive data at this point
                    subnet_type=ec2.SubnetType.PUBLIC
                ),
                allow_all_outbound=True,
                vpc=vpc,
                role=dev_role
            )

            # Connections for file system
            file_system.connections.allow_from(
                efs_service_instance, port_range=ec2.Port.all_traffic())

            # Create SSH security group
            ssh_group = ec2.SecurityGroup(self, 'ssh-sc', vpc=vpc, allow_all_outbound=True,
                                          description="Security group to allow inbound SSH access for whitelisted CSIRO addresses.")

            # Add rules
            rules = [
                ("140.79.64.0", 20, "VPN VIC"),
                ("130.155.0.0", 16, "NSW"),
                ("138.194.0.0", 16, "VIC"),
                ("144.110.0.0", 16, "SA/NT"),
                ("140.79.0.0", 16, "TAS"),
                ("130.116.0.0", 16, "WA"),
                ("140.253.224.0", 20, "ACT VPN"),
                ("130.116.192.0", 19, "WA VPN"),
                ("140.253.0.0", 16, "QLD"),
                ("152.83.0.0", 16, "ACT")
            ]

            for ip, mask, desc in rules:
                ssh_group.add_ingress_rule(peer=ec2.Peer.ipv4(
                    f"{ip}/{mask}"), connection=ec2.Port.tcp(22), description=desc)

            # Add ssh group
            efs_service_instance.add_security_group(ssh_group)

            # Retrieve metric
            cpu_usage_metric = cloudwatch.Metric(
                # Metrics here
                # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/viewing_metrics_with_cloudwatch.html
                namespace="AWS/EC2",
                metric_name="CPUUtilization",
                dimensions_map={
                    'InstanceId': efs_service_instance.instance_id
                },
                period=Duration.minutes(5),
                statistic='Maximum'
            )

            # Create alarm
            alarm = cloudwatch.Alarm(
                self,
                'alarm',
                metric=cpu_usage_metric,
                threshold=5,
                # How many 5 minutes in a row?
                # 1 hour of < 5% cpu
                evaluation_periods=int(90 / 5),
                actions_enabled=True,
                alarm_description="CPU is not being utilized on provisioned instance.",
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,
                treat_missing_data=cloudwatch.TreatMissingData.BREACHING
            )

            # Stop ec2
            alarm.add_alarm_action(
                # Stop instance
                cloudwatch_actions.Ec2Action(
                    cloudwatch_actions.Ec2InstanceAction.STOP)
            )

        # create the ECS task definition
        data_efs_volume_name = 'data-efs'
        # This path needs to exist - it depends on if you are using restored point
        # or working in a new
        root_neo4j_directory = efs_root_path
        # On docker image - base path is root directory
        instance_neo4j_path = ""
        self.task_definition = ecs.FargateTaskDefinition(
            scope=self,
            id='task-definition',
            cpu=neo4j_cpu_size,
            memory_limit_mib=neo4j_memory_size,
            # Add EFS file system as volume - need to reference in container
            # definition
            volumes=[ecs.Volume(
                name=data_efs_volume_name,
                efs_volume_configuration=ecs.EfsVolumeConfiguration(
                    file_system_id=file_system.file_system_id,
                    # no custom authorization required right now
                    # authorization_config=

                    # The container looks into /neo4j-data
                    root_directory=root_neo4j_directory,

                    # enable transit encryption
                    transit_encryption="ENABLED"
                )
            )]
        )

        # add the neo4j container
        self.container_definition = self.task_definition.add_container(
            id='neo4j',
            image=ecs.ContainerImage.from_registry(
                name='neo4j:4.4.12-community'
            ),
            port_mappings=[
                ecs.PortMapping(container_port=7474),
                ecs.PortMapping(container_port=7473),
                ecs.PortMapping(container_port=7687),
            ],
            secrets={
                "NEO4J_AUTH": ecs.Secret.from_secrets_manager(
                    sm.Secret.from_secret_complete_arn(
                        scope=self,
                        id='auth',
                        secret_complete_arn=neo4j_auth_arn,
                    )
                )
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix='neo4j-prototype',
                log_retention=logs.RetentionDays.ONE_MONTH
            ),
        )

        # add the efs volume mount points
        self.container_definition.add_mount_points(
            ecs.MountPoint(
                # mount the /data -> [ecs] at restored path
                # this will catch data - but not binaries/conf etc

                # binaries come from installation/image
                # conf should come from container setup/definition
                container_path=instance_neo4j_path + "/data",
                read_only=False,
                source_volume=data_efs_volume_name
            )
        )

        container_name = self.container_definition.container_name

        # Create ECS cluster
        self.cluster = ecs.Cluster(
            scope=self,
            id='cluster',
            vpc=vpc
        )

        # Create the fargate service
        self.service = ecs.FargateService(
            scope=self,
            id='neo4j-db',
            task_definition=self.task_definition,
            assign_public_ip=True,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            cluster=self.cluster,
            desired_count=1,
        )

        # Enable connection from/to EFS on all ports
        file_system.connections.allow_from(
            self.service,
            port_range=ec2.Port.all_traffic()
        )

        # Register this fargate service as application target
        atg = elb.ApplicationTargetGroup(
            self,
            f"application-tg",
            port=http_port,
            protocol=elb.ApplicationProtocol.HTTP,
            vpc=vpc
        )
        
        http_fargate_target = self.service.load_balancer_target(
            container_name=container_name,
            container_port=http_port,
        )
        tcp_fargate_target = self.service.load_balancer_target(
            container_name=container_name,
            container_port=tcp_port,
        )
        
        atg.add_target(http_fargate_target)

        balancers.add_conditional_http_route(
            id='neo4j-http-route',
            target_group=atg,
            conditions=[
                elb.ListenerCondition.host_headers(
                    [f"{http_instance_domain}.{allocator.root_domain}"]
                )
            ],
            priority=http_priority
        )
        
        # setup tcp route 
        ntg = elb.NetworkTargetGroup(
            self,
            f"network-tg",
            port=tcp_port,
            protocol=elb.Protocol.TCP,
            target_type=elb.TargetType.IP,
            vpc=vpc
        )
        ntg.add_target(tcp_fargate_target)
        
        # add tcp route 
        balancers.add_tcp_route(
            id='neo4j-tcp',
            source_port=tcp_port,
            target_group=ntg
        )

        # Allow ingress traffic on VPC routes
        rules = [
            ("140.79.64.0", 20, "VPN VIC"),
            ("130.155.0.0", 16, "NSW"),
            ("138.194.0.0", 16, "VIC"),
            ("144.110.0.0", 16, "SA/NT"),
            ("140.79.0.0", 16, "TAS"),
            ("130.116.0.0", 16, "WA"),
            ("140.253.224.0", 20, "ACT VPN"),
            ("130.116.192.0", 19, "WA VPN"),
            ("140.253.0.0", 16, "QLD"),
            ("152.83.0.0", 16, "ACT")
        ]

        for ip, mask, desc in rules:
            self.service.connections.allow_from(
                ec2.Peer.ipv4(
                    f"{ip}/{mask}"
                ),
                port_range=ec2.Port.tcp_range(7473, 7474),
                description=desc + " [7473,7474]."
            )
            self.service.connections.allow_from(
                ec2.Peer.ipv4(
                    f"{ip}/{mask}"
                ),
                port_range=ec2.Port.tcp(port=7687),
                description=desc + " [7687]."
            )

        # Allow all vpc traffic
        self.service.connections.allow_from(
            other=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            port_range=ec2.Port.all_traffic(),
            description='All VPC traffic.'
        )

        # Add the load balancer address
        # for the neo4j instance
        assert balancers.alb
        assert balancers.nlb
        http_record = allocator.add_load_balancer(
            "neo4j_balancer_record",
            domain_prefix=http_instance_domain,
            load_balancer=balancers.alb,
            comment="Neo4j Load Balancer HTTP DNS target"
        )

        tcp_record = allocator.add_load_balancer(
            "neo4j_bolt_balancer_record",
            domain_prefix=bolt_instance_domain,
            load_balancer=balancers.nlb,
            comment="Neo4j Load Balancer bolt TCP DNS target"
        )

        self.neo4j_http_host = f"{http_instance_domain}.{allocator.root_domain}"
        self.neo4j_bolt_host = f"{bolt_instance_domain}.{allocator.root_domain}"
        self.neo4j_bolt_port = 7687
        self.neo4j_http_port = 7474
        self.file_system = file_system
