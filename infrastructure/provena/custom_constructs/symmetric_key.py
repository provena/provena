from constructs import Construct
from aws_cdk import (
    aws_kms as kms,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
)
from typing import Any


class SymmetricKeyConstruct(Construct):
    def __init__(self, scope: Construct, id: str, **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a symmetric key
        self.key = kms.Key(
            self,
            "SymmetricKey",
            description="Symmetric KMS key for general encryption/decryption",
            enabled=True,
            enable_key_rotation=True,
            pending_window=Duration.days(7),
            removal_policy=RemovalPolicy.DESTROY
        )

    def grant_encrypt_decrypt(self, identity: iam.IGrantable) -> None:
        """
        Grants encrypt and decrypt permissions to an IAM identity

        Args:
            identity: The IAM identity (role, user, etc.) to grant permissions to
        """
        self.key.grant_encrypt_decrypt(identity)

    def grant_encrypt(self, identity: iam.IGrantable) -> None:
        """
        Grants encrypt-only permissions to an IAM identity

        Args:
            identity: The IAM identity (role, user, etc.) to grant permissions to
        """
        self.key.grant_encrypt(identity)

    def grant_decrypt(self, identity: iam.IGrantable) -> None:
        """
        Grants decrypt-only permissions to an IAM identity

        Args:
            identity: The IAM identity (role, user, etc.) to grant permissions to
        """
        self.key.grant_decrypt(identity)

    def add_to_resource_policy(self, statement: iam.PolicyStatement) -> None:
        """
        Adds a statement to the key's resource policy

        Args:
            statement: The policy statement to add
        """
        self.key.add_to_resource_policy(statement)


# Example usage:
"""
from aws_cdk import Stack
from constructs import Construct

class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Create the key construct
        key_construct = SymmetricKeyConstruct(self, "MySymmetricKey")
        
        # Example: Grant permissions to a Lambda function
        lambda_role = iam.Role(
            self, 
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        key_construct.grant_encrypt_decrypt(lambda_role)
        
        # Example: Grant decrypt-only permissions to an ECS task
        task_role = iam.Role(
            self, 
            "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        key_construct.grant_decrypt(task_role)
        
        # Example: Add a custom policy statement
        custom_statement = iam.PolicyStatement(
            actions=["kms:Decrypt"],
            principals=[iam.AccountRootPrincipal()],
            resources=["*"]
        )
        key_construct.add_to_resource_policy(custom_statement)
"""
