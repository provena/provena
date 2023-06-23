from aws_cdk import (
    aws_ec2 as ec2
)

from constructs import Construct
from typing import Any


class CsiroSshSecurityGroup(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: ec2.IVpc,
            **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # Create SSH security group
        sg = ec2.SecurityGroup(self, 'sg', vpc=vpc, allow_all_outbound=True,
                               description="Security group to allow inbound SSH access for whitelisted CSIRO addresses.")

        # Add rules
        rules = [
            ("140.79.64.0", 20, "VPN VIC"),
            ("130.155.0.0", 16, "NSW"),
            ("138.194.0.0", 16, "VIC"),
            ("144.110.0.0", 16, "SA/NT"),
            ("140.79.0.0", 16, "TAS"),
            ("130.116.0.0", 16, "WA"),
            ("140.253.224.0", 20, "ACT VPN"),
            ("130.116.192.0", 19, "WA VPN"),
            ("140.253.0.0", 16, "QLD"),
            ("152.83.0.0", 16, "ACT")
        ]

        for ip, mask, desc in rules:
            sg.add_ingress_rule(peer=ec2.Peer.ipv4(
                f"{ip}/{mask}"), connection=ec2.Port.tcp(22), description=desc)

	
	# expose the sg as construct interface
        self.sg = sg
