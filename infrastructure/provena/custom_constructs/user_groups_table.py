
from aws_cdk import (
    RemovalPolicy,
    aws_dynamodb as dynamo_db
)

from constructs import Construct
from typing import Any


class UserGroupsTable(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 enable_pitr: bool,
                 removal_policy: RemovalPolicy,
                 **kwargs: Any) -> None:
        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # fields:
        # - id (partition key)

        self.table = dynamo_db.Table(
            scope=self,
            id='table',
            removal_policy=removal_policy,
            point_in_time_recovery=enable_pitr,
            # id field must be unique
            partition_key=dynamo_db.Attribute(
                name="id",
                type=dynamo_db.AttributeType.STRING
            ),
            # Do not use provisioned throughput
            billing_mode=dynamo_db.BillingMode.PAY_PER_REQUEST
        )
