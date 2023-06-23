from aws_cdk import (
    aws_dynamodb as ddb,
    Duration,
    aws_lambda as _lambda,
    Annotations,
    aws_opensearchservice as search,
    aws_lambda_event_sources as lambda_sources,
    aws_sqs as sqs,
    RemovalPolicy,
    Stack
)

from constructs import Construct
from typing import Any, Dict
from provena.custom_constructs.docker_bundled_lambda import DockerizedLambda
from provena.utility.direct_secret_import import direct_import
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class SearchableObject(str, Enum):
    DATA_STORE_ITEM = "DATA_STORE_ITEM"
    REGISTRY_ITEM = "REGISTRY_ITEM"


@dataclass
class StreamerConfiguration():
    # unique ID suitable as cdk id base
    id: str
    # what is the name of the search index
    index_name: str
    # what is the name of the dynamoDB table
    dynamodb_table: ddb.Table
    # what is the name of the dynamoDB string field ID
    primary_id_field_name: str
    # what is the type of item - used to help process the searchable object
    # version
    item_type: SearchableObject


streamer_path = "../search-utils/record-streamer-lambda"
streamer_handler = "lambda_function.handler"
timeout = Duration.seconds(60)


class SearchStreamers(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            configs: List[StreamerConfiguration],
            linearised_field_name: str,
            qualified_search_domain_name: str,
            open_search_domain: search.IDomain,
            github_token_arn: str,
            branch_name: str,
            repo_string: str,
            extra_hash_dirs: List[str],
            dlq_enabled: bool = True,
            ** kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # resolve the github token
        oauth_token = direct_import(
            github_token_arn, Stack.of(self).region)

        # this construct sets up a set of dynamoDB event streams which
        # update/create/delete items as per the tables they emulate into the
        # specified indexes

        # check that the functions are unique
        id_set = set([c.id for c in configs])
        if len(id_set) != len(configs):
            Annotations.of(self).add_error(
                "Non unique search streamer config IDs. Aborting.")
            raise ValueError(
                "Non unique search streamer config IDs. Aborting.")

        function_map: Dict[str, _lambda.Function] = {}

        # create a dead letter queue for the processing lambda
        dlq: Optional[sqs.IQueue] = None
        if dlq_enabled:
            dlq = sqs.Queue(
                scope=self,
                id='streamer-dlq',
                removal_policy=RemovalPolicy.DESTROY,
                # max retention period
                retention_period=Duration.days(14)
            )

        for config in configs:
            func = DockerizedLambda(
                scope=self,
                id=config.id + '-streamer',
                path=streamer_path,
                handler=streamer_handler,
                timeout=timeout,
                bundling_environment={'GITHUB_TOKEN': oauth_token,
                                      'REPO_STRING': repo_string,
                                      'BRANCH_NAME': branch_name},
                lambda_environment={
                    "SEARCH_DOMAIN_NAME": qualified_search_domain_name,
                    "LINEARISED_FIELD": linearised_field_name,
                    "SEARCH_INDEX": config.index_name,
                    "RECORD_ID_FIELD": config.primary_id_field_name,
                    "ITEM_TYPE": config.item_type.value
                },
                dlq=dlq,
                extra_hash_dirs=extra_hash_dirs
            ).function

            # map the function
            function_map[config.id] = func

            # add read/write to specified index
            open_search_domain.grant_index_read_write(config.index_name, func)

            # create the event stream from ddb table and stream to lambda function
            table = config.dynamodb_table
            func.add_event_source(lambda_sources.DynamoEventSource(
                starting_position=_lambda.StartingPosition.LATEST,
                table=table,
                bisect_batch_on_error=True,
                retry_attempts=5,
                report_batch_item_failures=True,
            ))

            # grant the stream read permissions
            table.grant_stream_read(func)
