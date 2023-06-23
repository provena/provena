from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct
from typing import List, Any


BILLING_MODE = dynamodb.BillingMode.PAY_PER_REQUEST
HANDLE_FIELD_NAME = "handle"
STREAMS_ENABLED = True


class DataRegistry(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            stage: str,
            enable_pitr: bool,
            readers: List[iam.IGrantable],
            writers: List[iam.IGrantable],
            table_removal_policy: RemovalPolicy,
            **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Exposing handle field name
        self.handle_field_name = HANDLE_FIELD_NAME

        # Create a dynamo DB table
        self.table = dynamodb.Table(
            self,
            "table",
            billing_mode=BILLING_MODE,
            point_in_time_recovery=enable_pitr,
            removal_policy=table_removal_policy,
            partition_key=dynamodb.Attribute(
                name=HANDLE_FIELD_NAME,
                type=dynamodb.AttributeType.STRING
            ),
            # conditionally enable streams
            stream=dynamodb.StreamViewType.NEW_IMAGE if STREAMS_ENABLED else None
        )

        # Setup the schema/indexes
        # For now - no secondary index

        # Add the permissions to other components
        for r in readers:
            self.table.grant_read_data(r)

        for w in writers:
            self.table.grant_read_write_data(w)

        # Let API know how to talk to this database
        # (Environment variable)
        # Exposing table name
        self.table_name = self.table.table_name
