
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
)
from constructs import Construct

from typing import Optional, Any, List

class StorageBucket(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 bucket_arn: str,
                 **kwargs: Any) -> None:
        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket.from_bucket_arn(
            self, f"{construct_id}-imported-s3-bucket", bucket_arn=bucket_arn)

    def add_read_only(self, role: iam.Role) -> None:
        # Allow read access to the bucket for the user role
        self.bucket.grant_read(role)
        add_generic_s3_permissions(role)
        block_deletion_permissions(role)

    def add_read_write(self, role: iam.Role) -> None:
        # Allow read/write access to the bucket for the user role
        self.bucket.grant_read_write(role)
        add_generic_s3_permissions(role)
        block_deletion_permissions(role)

    def add_bucket_admin(self, role: iam.Role) -> None:
        # Allow read/write access to the bucket for the user role
        self.bucket.grant_read_write(role)
        add_generic_s3_permissions(role)
        # Don't block the deletion and other policy rules


class StaticWebsiteBucket(Construct):
    def __init__(self, scope: Construct,
                 construct_id: str,
                 trusted_build_account_ids: Optional[List[str]],
                 **kwargs: Any) -> None:
        # Super constructor
        super().__init__(scope, construct_id, **kwargs)

        # Create the bucket
        self.bucket = s3.Bucket(
            self, id=construct_id,
            removal_policy=RemovalPolicy.DESTROY,
            # This is required now because of cross account deployments!
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            # Remove all objects automatically - very helpful
            auto_delete_objects=True
        )

        # Enable build actions into the bucket from the trusted accounts - this
        # is required for cross account deployments to enable the pipeline in
        # the build project to deploy contents as a build step into the target
        # bucket
        if trusted_build_account_ids:
            for account_id in trusted_build_account_ids:
                # Grant read/write for the purposes of building into this static website
                self.bucket.grant_read_write(
                    iam.AccountPrincipal(account_id=account_id))

def add_generic_s3_permissions(role: iam.Role) -> None:
    # Also allow the saml role to list buckets in the account
    role.add_to_policy(iam.PolicyStatement(
        actions=[
            "s3:PutAccountPublicAccessBlock",
            "s3:GetAccountPublicAccessBlock",
            "s3:ListJobs",
            "s3:CreateJob",
            "s3:ListAllMyBuckets"
        ],
        resources=["*"]
    ))


def block_deletion_permissions(role: iam.Role) -> None:
    role.add_to_policy(iam.PolicyStatement(
        actions=[
            "s3:DeleteBucket",
            "s3:DeleteBucketPolicy",
            "s3:DeleteBucketWebsite",
            "s3:DeleteObjectVersion"
        ],
        resources=["*"],
        effect=iam.Effect.DENY
    ))
