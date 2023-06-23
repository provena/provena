from aws_cdk import (
    aws_ec2 as ec2
)
from constructs import Construct
from typing import Any
from provena.custom_constructs.load_balancers import SharedBalancers


class NetworkConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 stage: str,
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create public and private subnet
        subnets = [
            ec2.SubnetConfiguration(
                name=stage + "_public_subnets",
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            ec2.SubnetConfiguration(
                name=stage + "_private_isolated_subnets",
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            )
        ]

        # Establish vpc
        self.vpc = ec2.Vpc(self,
                           "ECS_VPC",
                           cidr="10.0.0.0/16",
                           subnet_configuration=subnets,
                           max_azs=3)

        # setup shared balancers but don't establish anything yet
        self.balancers = SharedBalancers(
            scope=self,
            id='balancers'
        )