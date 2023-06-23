import boto3  # type: ignore
import json
import os

from typing import Dict, Any

# expect topic ARN as env variable
topic_arn = os.getenv("TOPIC_ARN")


def handler(event: Dict[str, Any], context: Any) -> None:
    # Print event for debugging if required
    print(event)

    # Parse the incoming event
    sns_record = event['Records'][0]['Sns']
    contents = sns_record['Message']

    # Parse contents as json object
    json_contents = json.loads(contents)

    # Get the pipeline name and stage
    pipeline_name = json_contents['detail']['pipeline']
    pipeline_state = json_contents['detail']['state']

    # Produce new subject and contents
    new_subject = "Pipeline State Change Notification"
    new_content = f"""
    Pipeline: {pipeline_name}
    State change: {pipeline_state}
    """

    # Publish new message to the final SNS topic
    print(
        f"Publishing message subject '{new_subject}' contents '{new_content}'.")
    client = boto3.client("sns")
    resp = client.publish(
        TargetArn=topic_arn,
        Message=new_content,
        Subject=new_subject
    )
    print(f"Published: {resp=}")
