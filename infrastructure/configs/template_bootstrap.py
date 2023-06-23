from provena.config.config_class import GithubBootstrapConfig
from aws_cdk import Environment

def config() -> GithubBootstrapConfig:
    return GithubBootstrapConfig(
        env=Environment(
            account="TODO",  # your AWS account id
            region="TODO"  # e.g. ap-southeast-2
        ),
        github_token_arn="TODO"  # secret ARN containing your github oauth token
    )
