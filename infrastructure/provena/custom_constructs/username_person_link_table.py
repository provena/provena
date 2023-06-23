
from aws_cdk import (
    RemovalPolicy,
    aws_dynamodb as dynamo_db
)

from constructs import Construct
from typing import Any


class UsernamePersonLinkTable(Construct):
    def __init__(self, scope: Construct,
                 id: str,
                 enable_pitr: bool,
                 removal_policy: RemovalPolicy,
                 **kwargs: Any) -> None:
        # Super constructor
        super().__init__(scope, id, **kwargs)

        # fields:
        # - username (primary)
        # - person_id (non specified)

        partition_key = "username"
        self.table = dynamo_db.Table(
            scope=self,
            id='table',
            removal_policy=removal_policy,
            point_in_time_recovery=enable_pitr,
            # id field must be unique
            partition_key=dynamo_db.Attribute(
                name=partition_key,
                type=dynamo_db.AttributeType.STRING
            ),
            # Do not use provisioned throughput
            billing_mode=dynamo_db.BillingMode.PAY_PER_REQUEST
        )

        # Add GSI which enables lookup from the person id -> username (admin only)
        gsi_partition_key = "person_id"

        # this is exposed as part of the construct interface
        person_gsi_index_name = "person_id_index"
        # default project all attributes.
        self.table.add_global_secondary_index(
            index_name=person_gsi_index_name,
            partition_key=dynamo_db.Attribute(
                name=gsi_partition_key,
                type=dynamo_db.AttributeType.STRING
            ),
        )

        # expose the index name for passing into the Auth API
        self.person_gsi_index_name = person_gsi_index_name
