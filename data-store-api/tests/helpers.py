from typing import Any

def setup_dynamodb_reviewers_table(client: Any, table_name: str) -> None:
    """    setup_dynamob_registry_table
        Use boto client to produce dynamodb table which mirrors
        the registry table for testing and uses a 'id' key for item
        retrieval.

        Arguments
        ----------
        client: dynamodb boto client
            The mocked dynamo db client
        table_name : str
            The name of the table

        See Also (optional)
        --------

        Examples (optional)
        --------
    """

    # Setup dynamo db
    client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }

        ],
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        BillingMode='PAY_PER_REQUEST',
    )