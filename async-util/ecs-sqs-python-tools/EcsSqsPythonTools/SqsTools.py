import boto3  # type: ignore
from pydantic import BaseModel
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class MessageContents():
    # The raw contents
    message_raw: str
    # The receipt handle which is handed back when succeeded
    receipt_handle: str


def consume_raw_messages_from_queue(queue_url: str, max_count: int = 1) -> List[MessageContents]:
    """

    Pulls an item from the queue

    Args:
        queue_url (str): The queue url
        max_count (int, optional): The count. Defaults to 1.

    Returns:
        Optional[MessageContents]: Message if found
    """
    sqs = boto3.client('sqs')

    # Receive set number of messages from queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=max_count,
        WaitTimeSeconds=0
    )

    print(f"SQS response from queue poll: {response}")

    # Check if a message was received
    messages: List[MessageContents] = []
    if 'Messages' in response:
        for message in response['Messages']:
            # Extract the message body and receipt handle
            message_body = message['Body']
            receipt_handle = message['ReceiptHandle']

            messages.append(MessageContents(
                message_raw=message_body, receipt_handle=receipt_handle))

    print(f"Messages received. Count: {len(messages)}, Contents: {messages}.")
    return messages


def delete_message_from_queue(queue_url: str, receipt_handle: str) -> None:
    # Setup client
    sqs = boto3.client('sqs')
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
