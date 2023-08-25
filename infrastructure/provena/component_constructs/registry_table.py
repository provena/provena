from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct
from typing import List, Any, Tuple

BILLING_MODE = dynamodb.BillingMode.PAY_PER_REQUEST
ID_FIELD_NAME = "id"
STREAMS_ENABLED = True
INDEX_NAME_POSTFIX = "-index"

# TODO move into config. Actually can leave here as this is the registry_table module.
global_secondary_indexes: List[Tuple[str, str]] = [

    # To add these to an existing table, comment them all out then add back in (cdk deploy) one by one until all uncommented.
    # Should be able to add them with new tables.
    ("item_subtype", "updated_timestamp"),
    ("item_subtype", "created_timestamp"),
    ("item_subtype", "display_name"),

    ("universal_partition_key", "updated_timestamp"),
    ("universal_partition_key", "created_timestamp"),
    ("universal_partition_key", "display_name"),

    ("release_approver", "release_timestamp"),
    # maybe another, release_approver and release_status?

]

# list of attribute used for sorting that are of type string
string_sort_keys: List[str] = ["display_name"]


class RegistryTable(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            pitr_enabled: bool,
            readers: List[iam.IGrantable],
            writers: List[iam.IGrantable],
            removal_policy: RemovalPolicy,
            **kwargs: Any) -> None:
        """    __init__
            Basic dynamoDB registry table. Setup to not be deleted if the 
            cloud formation stack is destroyed. Pay per request. 
            Configurable in the static variables above. 

            Uses a single primary key - 'id' which is intended for the registry
            to be a handle ID. Otherwise there is no prescriptive model 
            for what goes in this table.

            Arguments
            ----------
            scope : Construct
                The CDK scope
            construct_id : str
                The CDK construct ID
            pitr_enabled: bool
                Should the dynamoDB table have continuous PITR recovery enabled
            readers : List[iam.IGrantable]
                List of grantable readers
            writers : List[iam.IGrantable]
                List of grantable writers

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        super().__init__(scope, construct_id, **kwargs)

        # Exposing handle field name
        self.handle_field_name = ID_FIELD_NAME

        # Create a dynamo DB table
        self.table = dynamodb.Table(
            self,
            "table",
            billing_mode=BILLING_MODE,
            point_in_time_recovery=pitr_enabled,

            removal_policy=removal_policy,
            partition_key=dynamodb.Attribute(
                name=ID_FIELD_NAME,
                type=dynamodb.AttributeType.STRING
            ),
            # conditionally enable streams
            stream=dynamodb.StreamViewType.NEW_IMAGE if STREAMS_ENABLED else None,
        )

        # add global secondary indexes
        for partition_key, sort_key in global_secondary_indexes:

            # default project all attributes.
            self.table.add_global_secondary_index(
                # naming convention used by default in aws console when creating GSIs
                index_name=partition_key+'-'+sort_key+INDEX_NAME_POSTFIX,
                partition_key=dynamodb.Attribute(
                    name=partition_key,
                    type=dynamodb.AttributeType.STRING
                ),
                sort_key=dynamodb.Attribute(
                    name=sort_key,
                    type=dynamodb.AttributeType.STRING if sort_key in string_sort_keys else dynamodb.AttributeType.NUMBER
                ),
            )

        # Add the permissions to other components
        for r in readers:
            self.table.grant_read_data(r)

        for w in writers:
            self.table.grant_read_write_data(w)

        # Expose the table name
        self.table_name = self.table.table_name


class IdIndexTable(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            pitr_enabled: bool,
            readers: List[iam.IGrantable],
            writers: List[iam.IGrantable],
            removal_policy: RemovalPolicy,
            **kwargs: Any) -> None:
        """    __init__
            Basic dynamoDB registry auth table. Setup to not be deleted if the 
            cloud formation stack is destroyed. Pay per request. 
            Configurable in the static variables above. 

            Uses a single primary key - 'id' which is intended for the registry
            to be a handle ID. Otherwise there is no prescriptive model 
            for what goes in this table.

            Arguments
            ----------
            scope : Construct
                The CDK scope
            construct_id : str
                The CDK construct ID
            pitr_enabled: bool
                Should the dynamoDB table have continuous PITR recovery enabled
            readers : List[iam.IGrantable]
                List of grantable readers
            writers : List[iam.IGrantable]
                List of grantable writers

            See Also (optional)
            --------

            Examples (optional)
            --------
        """
        super().__init__(scope, construct_id, **kwargs)

        # Exposing handle field name
        self.handle_field_name = ID_FIELD_NAME

        # Create a dynamo DB table
        self.table = dynamodb.Table(
            self,
            "table",
            billing_mode=BILLING_MODE,
            point_in_time_recovery=pitr_enabled,
            removal_policy=removal_policy,
            partition_key=dynamodb.Attribute(
                name=ID_FIELD_NAME,
                type=dynamodb.AttributeType.STRING
            )
            # no streams enabled for the auth or lock table
        )

        # Add the permissions to other components
        for r in readers:
            self.table.grant_read_data(r)

        for w in writers:
            self.table.grant_read_write_data(w)

        # Expose the table name
        self.table_name = self.table.table_name
