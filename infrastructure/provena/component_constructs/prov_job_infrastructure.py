from aws_cdk import (
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda_event_sources as lambda_sources,
    aws_sns_subscriptions as sns_subs,
    aws_secretsmanager as sm,
    aws_lambda as aws_lambda,
    aws_dynamodb as dynamo_db,
    RemovalPolicy,
    Duration,
    Stack
)

from constructs import Construct
from typing import Any, List

from provena.custom_constructs.docker_bundled_lambda import DockerizedLambda
from provena.utility.direct_secret_import import direct_import


class ProvJobQueue(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            build_github_token_arn: str,
            branch_name: str,
            repo_string: str,
            keycloak_endpoint: str,
            prov_api_endpoint: str,
            dispatcher_service_role_secret_arn: str,
            extra_hash_dirs: List[str],
            topic_display_name: str = "prov-job-topic",
            dispatcher_timeout: Duration = Duration.minutes(2),
            table_removal_policy: RemovalPolicy = RemovalPolicy.DESTROY,
            **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # resolve the github token
        oauth_token = direct_import(
            build_github_token_arn, Stack.of(self).region)

        # sns topic to manage lodging the job
        topic = sns.Topic(
            scope=self,
            id='topic',
            display_name=topic_display_name
        )

        # sqs queue to decouple lodging from handling job submission
        queue = sqs.Queue(
            scope=self,
            id='queue',
            # don't allow messages to reappear on the queue until 5 minutes have
            # passed
            visibility_timeout=Duration.minutes(5),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=5,
                queue=sqs.Queue(
                    scope=self,
                    id='dlq'
                )
            )
        )

        # dynamoDB table to log job status - primary key = "id"
        # expiry key = "expiry"
        table = dynamo_db.Table(
            scope=self,
            id='table',
            removal_policy=table_removal_policy,
            point_in_time_recovery=True,
            partition_key=dynamo_db.Attribute(
                name="id",
                type=dynamo_db.AttributeType.STRING
            ),
            # Do not use provisioned throughput
            billing_mode=dynamo_db.BillingMode.PAY_PER_REQUEST
        )

        # subscribe the sqs queue to topic
        # deliver all sns messages -> the SQS queue
        topic.add_subscription(sns_subs.SqsSubscription(
            queue=queue
        ))

        # processor lambda which is subbed to sqs as event source

        # Set this up as a docker bundled lambda so that we can package shared
        # interfaces
        bundled_lambda = DockerizedLambda(
            scope=self,
            id='dispatcher',
            path="../prov_job_dispatcher",
            handler="lambda_function.handler",
            timeout=dispatcher_timeout,
            bundling_environment={'GITHUB_TOKEN': oauth_token,
                                  'REPO_STRING' : repo_string,
                                  'BRANCH_NAME': branch_name},
            # limit rapid pulling off the job queue to avoid overwhelming
            # downstream consumer prov API
            max_concurrency=2,
            extra_hash_dirs=extra_hash_dirs
        )
        # pull out the lambda function interface
        processor_lambda = bundled_lambda.function
        
        # add the table name as env variable
        processor_lambda.add_environment(
            key="JOB_TABLE_NAME",
            value=table.table_name
        )

        # add the service role ARN environment variable
        processor_lambda.add_environment(
            key="SERVICE_ROLE_SECRET_ARN",
            value=dispatcher_service_role_secret_arn
        )

        # Get the secret
        service_secret = sm.Secret.from_secret_complete_arn(
            scope=self,
            id='service-account-secret',
            secret_complete_arn=dispatcher_service_role_secret_arn
        )

        # Grant read to dispatcher role
        assert processor_lambda.role
        service_secret.grant_read(processor_lambda.role)

        # add the keycloak endpoint
        processor_lambda.add_environment(
            key="KEYCLOAK_ENDPOINT",
            value=keycloak_endpoint
        )

        # where is the prov API?
        processor_lambda.add_environment(
            key="PROV_API_ENDPOINT",
            value=prov_api_endpoint
        )

        # sub lambda function to sqs
        processor_lambda.add_event_source(lambda_sources.SqsEventSource(
            queue=queue,
            # process one at a time
            batch_size=1,
            enabled=True
        ))

        # and let the lambda do things with the table
        table.grant_read_write_data(processor_lambda)

        # Create a  table which links a user ID -> batch ID(s) -> job ID(s)
        # primary key = user email
        batch_table = dynamo_db.Table(
            scope=self,
            id='batch-table',
            removal_policy=table_removal_policy,
            point_in_time_recovery=True,
            # identified by username
            partition_key=dynamo_db.Attribute(
                name="username",
                type=dynamo_db.AttributeType.STRING
            ),
            # Do not use provisioned throughput
            billing_mode=dynamo_db.BillingMode.PAY_PER_REQUEST
        )

        # interface
        self.dispatcher_function = processor_lambda
        self.job_status_table = table
        self.lodge_job_topic = topic
        self.job_queue = queue
        self.batch_table = batch_table
