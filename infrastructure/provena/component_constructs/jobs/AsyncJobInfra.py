from aws_cdk import (
    aws_sns as sns,
    aws_sqs as sqs,
    aws_ec2 as ec2,
    Duration,
    RemovalPolicy,
    Stack,
    aws_dynamodb as ddb,
    aws_sns_subscriptions as sns_subs,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_apigateway as api_gw,
    aws_secretsmanager as sm,
    aws_certificatemanager as aws_cm
)
from constructs import Construct
from typing import Any, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from provena.utility.direct_secret_import import direct_import
from provena.custom_constructs.docker_lambda_function import DockerImageLambda
from provena.custom_constructs.docker_bundled_lambda import create_lambda
from provena.custom_constructs.DNS_allocator import DNSAllocator
from provena.config.config_class import APIGatewayRateLimitingSettings, SentryConfig
from typing import Optional

INDEX_NAME_POSTFIX = "-index"


class JobType(str, Enum):
    PROV_LODGE = "PROV_LODGE"
    REGISTRY = "REGISTRY"
    EMAIL = "EMAIL"


@dataclass
class JobConfig():
    type: JobType
    image: ecs.ContainerImage
    visibility_timeout: Duration
    environment: Dict[str, str]
    secrets: Dict[str, ecs.Secret]


class AsyncJobInfra(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 jobs: List[JobConfig],
                 idle_timeout: int,
                 max_task_scaling: int,
                 github_build_token_arn: str,
                 cert_arn: str,
                 allocator: DNSAllocator,
                 keycloak_endpoint: str,
                 domain: str,
                 domain_base: str,
                 stage: str,
                 repo_string: str,
                 branch_name: str,
                 vpc: ec2.Vpc,
                 api_rate_limiting: Optional[APIGatewayRateLimitingSettings],
                 job_api_extra_hash_dirs: List[str],
                 invoker_extra_hash_dirs: List[str],
                 connector_extra_hash_dirs: List[str],
                 git_commit_id: Optional[str],
                 sentry_config: SentryConfig,
                 feature_number: Optional[int],
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        oauth_token = direct_import(
            github_build_token_arn, Stack.of(self).region)

        # ==============
        # JOB API SETUP
        # ==============

        # Make sure these parameters match deployment
        # requirements
        api_environment = {
            "KEYCLOAK_ENDPOINT": keycloak_endpoint,
            "DOMAIN_BASE": domain_base,
            "STAGE": stage,
            "GIT_COMMIT_ID": git_commit_id,
            "MONITORING_ENABLED": str(sentry_config.monitoring_enabled),
            "SENTRY_DSN": sentry_config.sentry_dsn_back_end,
            "FEATURE_NUMBER": str(feature_number)
        }

        # Create the function
        job_api: DockerImageLambda = DockerImageLambda(
            self,
            'job-lambda',
            build_directory="../job-api",
            dockerfile_path_relative="lambda_dockerfile",
            build_args={
                "github_token": oauth_token,
                "repo_string": repo_string,
                "branch_name": branch_name
            },
            extra_hash_dirs=job_api_extra_hash_dirs,
            memory_size=1024
        )

        assert job_api.function.role

        for key, val in api_environment.items():
            if val is not None:
                job_api.function.add_environment(key, val)

        # Setup api gw integration
        # retrieve certificate
        acm_cert = aws_cm.Certificate.from_certificate_arn(
            self, "api-cert", cert_arn
        )

        # Setup API gateway routing
        api = api_gw.LambdaRestApi(
            scope=self,
            id='apigw',
            handler=job_api.function,
            # Greedy proxy forwards all traffic at endpoint
            # to lambda
            proxy=True,
            domain_name=api_gw.DomainNameOptions(
                domain_name=f"{domain}.{allocator.root_domain}",
                certificate=acm_cert
            ),
            deploy_options=api_gw.StageOptions(
                description="Async Job API Docker Lambda FastAPI API Gateway",
                throttling_burst_limit=api_rate_limiting.throttling_burst_limit if api_rate_limiting else None,
                throttling_rate_limit=api_rate_limiting.throttling_rate_limit if api_rate_limiting else None,
            )
        )
        # API is non stateful - clean up
        api.apply_removal_policy(RemovalPolicy.DESTROY)

        # add dns entry
        allocator.add_api_gateway_target(
            id="lambda-job-api-route",
            target=api,
            domain=domain,
            comment="Lambda Job API domain entry"
        )

        # Add rule to listener to hit this target group
        target_host = domain + "." + allocator.root_domain

        # expose endpoint
        self.job_api_endpoint = f"https://{target_host}"

        # ==================
        # STATUS TABLE SETUP
        # ==================

        # DynamoDB for job status (all)
        session_id_key = "session_id"
        timestamp_key = "created_timestamp"
        username_key = "username"
        batch_key = "batch_id"
        gsi_field_key = "gsi_status"

        status_table: ddb.Table = ddb.Table(
            scope=self,
            id='status',
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,

            # Primary key = session id
            partition_key=ddb.Attribute(
                name=session_id_key, type=ddb.AttributeType.STRING),
        )

        # GSI for looking up against username instead of session ID
        username_index_name = username_key+'-'+timestamp_key+INDEX_NAME_POSTFIX
        batch_id_index_name = batch_key+'-'+timestamp_key+INDEX_NAME_POSTFIX
        global_list_index_name = gsi_field_key + \
            '-' + timestamp_key + INDEX_NAME_POSTFIX

        # for fetching against username
        status_table.add_global_secondary_index(
            index_name=username_index_name,
            partition_key=ddb.Attribute(
                name=username_key,
                type=ddb.AttributeType.STRING
            ),
            sort_key=ddb.Attribute(
                name=timestamp_key,
                type=ddb.AttributeType.NUMBER
            ),
        )

        # for fetching against batch ID
        status_table.add_global_secondary_index(
            index_name=batch_id_index_name,
            partition_key=ddb.Attribute(
                name=batch_key,
                type=ddb.AttributeType.STRING
            ),
            sort_key=ddb.Attribute(
                name=timestamp_key,
                type=ddb.AttributeType.NUMBER
            ),
        )

        # for listing all items sorted by timestamp
        status_table.add_global_secondary_index(
            index_name=global_list_index_name,
            partition_key=ddb.Attribute(
                name=gsi_field_key,
                type=ddb.AttributeType.STRING
            ),
            sort_key=ddb.Attribute(
                name=timestamp_key,
                type=ddb.AttributeType.NUMBER
            ),
        )

        # Grant job API access into status table and provide table name
        status_table.grant_read_write_data(job_api.function)
        job_api.function.add_environment(
            key="status_table_name", value=status_table.table_name)
        job_api.function.add_environment(
            key="username_index_name", value=username_index_name)
        job_api.function.add_environment(
            key="batch_id_index_name", value=batch_id_index_name)
        job_api.function.add_environment(
            key="global_list_index_name", value=global_list_index_name)

        # =============
        # CLUSTER SETUP
        # =============

        # ECS Cluster and tasks as configured (all)
        # No services need to run here
        cluster: ecs.Cluster = ecs.Cluster(
            scope=self,
            id='cluster',
            vpc=vpc,
            enable_fargate_capacity_providers=True
        )

        # ====================
        # LAMBDA INVOKER SETUP
        # ====================

        # Lambda function to invoke ECS according to rules (all)
        invoker = create_lambda(
            scope=self,
            id='invoker',
            handler="lambda_function.handler",
            path="../async-util/lambda_invoker",
            timeout=Duration.minutes(2),
            bundling_required=True,
            extra_hash_dirs=invoker_extra_hash_dirs
        )

        # Let the invoker know the cluster ARN
        invoker.add_environment(key="CLUSTER_ARN", value=cluster.cluster_arn)

        # The invoker also needs some extra permissions

        # Create an IAM policy statement allowing describe subnets
        describe_subnets_statement = iam.PolicyStatement(
            actions=['ec2:DescribeSubnets'],
            # TODO restrict this more
            resources=['*'],
        )
        describe_tasks_statement = iam.PolicyStatement(
            actions=['ecs:DescribeTasks', 'ecs:ListTasks'],
            # TODO restrict this more
            resources=['*'],
        )

        invoker.add_to_role_policy(describe_subnets_statement)
        invoker.add_to_role_policy(describe_tasks_statement)

        # ======================
        # LAMBDA CONNECTOR SETUP
        # ======================

        # Lambda function to connect SNS -> Status Table
        connector = create_lambda(
            scope=self,
            id='tableconnector',
            handler="lambda_function.handler",
            path="../async-util/ddb_connector",
            timeout=Duration.minutes(2),
            bundling_required=True,
            extra_hash_dirs=connector_extra_hash_dirs
        )

        # Let the connector publish to status table
        status_table.grant_read_write_data(connector)

        # Let connector know the table name
        connector.add_environment(
            key="TABLE_NAME", value=status_table.table_name)

        # ==========
        # JOBS SETUP
        # ==========

        # Need an SNS topic for each job type (each)
        topics: Dict[JobType, sns.Topic] = {}
        queues: Dict[JobType, sqs.Queue] = {}
        task_roles: Dict[JobType, iam.IGrantable] = {}
        task_dfns: Dict[JobType, ecs.FargateTaskDefinition] = {}

        for job in jobs:
            # Fanout SNS topic
            topic: sns.Topic = sns.Topic(
                scope=self,
                id='topic' + job.type,
                # fifo=True
            )

            # Let the job API publish to topic
            topic.grant_publish(job_api.function)

            # Let the job API know the topic name for this job type
            job_api.function.add_environment(
                key=job.type + "_TOPIC_ARN",
                value=topic.topic_arn
            )

            # SQS job queue with DLQ for each job type
            dlq = sqs.Queue(scope=self,
                            id='dlq' + job.type,
                            # fifo=True
                            )

            redrive = sqs.DeadLetterQueue(
                # only single attempt
                max_receive_count=1,
                queue=dlq
            )

            queue: sqs.Queue = sqs.Queue(
                scope=self,
                id='queue' + job.type,
                # fifo=True,
                dead_letter_queue=redrive,
                # Specified visibility timeout
                visibility_timeout=job.visibility_timeout
            )

            # Subscribe the queue to topic
            topic.add_subscription(
                sns_subs.SqsSubscription(queue=queue)
            )
            # Subscribe the invoker to topic
            topic.add_subscription(
                sns_subs.LambdaSubscription(
                    fn=invoker
                )
            )

            # Subscribe the ddb connector to topic

            topic.add_subscription(
                sns_subs.LambdaSubscription(
                    fn=connector
                )
            )

            # Build the task definition
            task_dfn: ecs.FargateTaskDefinition = ecs.FargateTaskDefinition(
                scope=self,
                id='fgdfn' + job.type,
                # 1 vcpu
                cpu=1024,
                # 2048MB ram
                memory_limit_mib=2048
            )

            # Task requires these permissions
            # r/w sqs queue
            # r/w ddb table
            queue.grant_consume_messages(task_dfn.task_role)
            status_table.grant_read_write_data(task_dfn.task_role)

            # Add the container to task dfn
            base_environment = job.environment.copy()
            base_environment.update({
                'QUEUE_URL': queue.queue_url,
                'STATUS_TABLE_NAME': status_table.table_name,
                'SNS_TOPIC_ARN': topic.topic_arn,
                'JOB_TYPE': job.type,
                # This is also included for all tasks
                'JOB_API_ENDPOINT': self.job_api_endpoint,
                # Determines how long the job polls before quitting
                'IDLE_TIMEOUT': str(idle_timeout)
            })
            task_dfn.add_container(
                id='jobcontainer' + job.type,
                image=job.image,
                environment=base_environment,
                secrets=job.secrets,
                logging=ecs.LogDriver.aws_logs(stream_prefix=job.type)
            )

            # Update dicts
            queues[job.type] = queue
            topics[job.type] = topic
            task_dfns[job.type] = task_dfn
            task_roles[job.type] = task_dfn.task_role

            # expose the cluster ARN and task definition to the invoker

            # At invoke time the cluster, launch type (FARGATE) and task
            # definition are provided.
            invoker.add_environment(
                # e.g. PROV_LODGE_TASK_DEFINITION_ARN
                key=job.type + "_TASK_DEFINITION_ARN", value=task_dfn.task_definition_arn)

            # Let the invoker invoke the task definition
            task_dfn.grant_run(invoker)

        invoker.add_environment(
            key="vpc_id", value=vpc.vpc_id
        )
        invoker.add_environment(
            key="idle_timeout", value=str(idle_timeout)
        )
        invoker.add_environment(
            key="max_task_scaling", value=str(max_task_scaling)
        )

        # expose information
        self.status_table = status_table
        self.task_dfns = task_dfns
        self.queues = queues
        self.topics = topics
        self.task_roles = task_roles
