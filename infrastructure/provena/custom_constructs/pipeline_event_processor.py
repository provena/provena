from aws_cdk import(
    aws_codepipeline as codepipeline,
    aws_sns as sns, 
    aws_codestarnotifications as notifications, 
    aws_sns_subscriptions as subs,
    aws_lambda as _lambda, 
)

from constructs import Construct
from typing import Any


class PipelineEventProcessor(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 code_pipeline: codepipeline.Pipeline,
                 email_address: str,
                 **kwargs : Any) -> None:
        """    __init__
            Produces an intermediary filter topic and lambda function 
            which handles the codepipeline notification events and publishes
            to the email address with a filtered subset.

            Arguments
            ----------
            scope : Construct
                The scope
            construct_id : str
                The desired ID
            code_pipeline : codepipeline.Pipeline
                The built pipeline underlying cdk pipelines - cannot be edited
            email_address : str
                The email address for final publishing

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # Create SNS topic for intermediary
        intermediary_topic = sns.Topic(self, 'pipeline-intermediary-topic')

        # Create SNS topic for final output
        final_topic = sns.Topic(self, 'pipeline-final-topic')

        # Create notification from underlying object
        rule = notifications.NotificationRule(
            self, 'notification',
            events=[
                "codepipeline-pipeline-pipeline-execution-failed",
                "codepipeline-pipeline-pipeline-execution-canceled",
                "codepipeline-pipeline-pipeline-execution-started",
                "codepipeline-pipeline-pipeline-execution-resumed",
                "codepipeline-pipeline-pipeline-execution-succeeded",
                "codepipeline-pipeline-pipeline-execution-superseded"
            ],
            source=code_pipeline,
            targets=[intermediary_topic],
            detail_type=notifications.DetailType.BASIC
        )
        

        # Create processing lambda function
        processing_function = _lambda.Function(
            scope=self,
            id='event-processor',
            code=_lambda.Code.from_asset(
                'provena/lambda_utility/pipeline_event_filter'),
            handler="lambda_function.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            environment={
                "TOPIC_ARN": final_topic.topic_arn
            }
        )

        # Create subscription to email alerts channel
        email_sub = subs.EmailSubscription(
            email_address=email_address
        )

        # Subscribe email to final topic
        final_topic.add_subscription(email_sub)
        
        # Subscribe lambda to intermediary
        intermediary_topic.add_subscription(subs.LambdaSubscription(processing_function))

        # Allow lambda function to publish to final topic 
        final_topic.grant_publish(processing_function)
