import boto3  # type: ignore


def direct_import(secret_name: str, region: str) -> str:
    # Try to create a session using no specified credentials
    try:
        # This should work for non local deployment (i.e. pipeline)
        # where creds are in the environment
        session = boto3.Session(region_name=region)
        client = session.client('secretsmanager')

        return client.get_secret_value(
            SecretId=secret_name
        )['SecretString']
    except Exception as e:
        print("Failed to retrieve secret directly! Ensure that all referenced secret ARNs are accessible from the current AWS authorisation context.")
        raise e
