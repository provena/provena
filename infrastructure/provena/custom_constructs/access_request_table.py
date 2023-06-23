
from aws_cdk import(
    RemovalPolicy,
    aws_dynamodb as dynamo_db
)

from constructs import Construct
from typing import Any

class AccessRequestTable(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 enable_pitr: bool,
                 removal_policy:RemovalPolicy,
                 **kwargs: Any) -> None:
        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # Build table

        # See auth api/models/RequestAccessTableItem
        # for more info on these attributes

        # fields:
        # - username (partition key)
        # - request_id (sort key)
        # - expiry (ttl attribute timestamp)

        # - created_timestamp
        # - updated_timestamp
        # - status (from status enum defined in auth API)
        # - notes (misc str field - do with as we want)
        # - request_diff_contents (str serialized json document)
        # - complete_contents (str serialized json document)
        self.table = dynamo_db.Table(
            scope=self,
            id='table',
            removal_policy=removal_policy,
            time_to_live_attribute="expiry",
            point_in_time_recovery=enable_pitr,
            partition_key=dynamo_db.Attribute(
                name="username",
                type=dynamo_db.AttributeType.STRING
            ),
            sort_key=dynamo_db.Attribute(
                name="request_id",
                type=dynamo_db.AttributeType.NUMBER
            ),
            # Do not use provisioned throughput
            billing_mode=dynamo_db.BillingMode.PAY_PER_REQUEST
        )
