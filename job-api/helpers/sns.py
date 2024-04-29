from ProvenaInterfaces.AsyncJobAPI import *
import boto3  # type: ignore
import logging
from pydantic import BaseModel

# setup logger
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get logger for this module
logger_key = "helpers"
logger = logging.getLogger(logger_key)


def publish_model_to_sns(model: BaseModel, topic_arn: str) -> None:
    # Serialize the model to JSON
    message_body = model.json(exclude_none=True)

    # Create an SNS client
    sns_client = boto3.client('sns')

    # Publish the message to the SNS topic
    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Message=message_body
        )
    except Exception as e:
        err = f"Failed to publish to SNS topic: {e}."
        logging.error(err)
        raise Exception(err)
