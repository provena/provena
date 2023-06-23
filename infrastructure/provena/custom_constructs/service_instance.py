
from aws_cdk import (
    aws_iam as iam,
    aws_ec2 as ec2,
    Annotations
)

from constructs import Construct
from typing import Any, List, Optional
from provena.custom_constructs.csiro_security_group import CsiroSshSecurityGroup


class ServiceInstance(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.IVpc,
        size: ec2.InstanceType = ec2.InstanceType.of(
            instance_class=ec2.InstanceClass.T3, instance_size=ec2.InstanceSize.MICRO),
        existing_role_arn: Optional[str] = None,
        existing_role: Optional[iam.IRole] = None,
        add_ssm_instance_permissions: bool = True,
        static_ip: bool = False,
        ** kwargs: Any
    ) -> None:
        super().__init__(scope, id, **kwargs)

        if existing_role is not None and existing_role_arn is not None:
            Annotations.of(self).add_error(
                "Cannot provide both a role ARN and an IAM IRole for a service instance.")

        role: Optional[iam.IRole] = None

        if existing_role:
            role = existing_role
        if existing_role_arn:
            role = iam.Role.from_role_arn(
                self, 'ec2-dev-role', existing_role_arn)

        # Create instance
        instance = ec2.Instance(
            scope=self,
            id='instance',
            instance_type=size,
            # use ubuntu image - more comfy for devs
            machine_image=ec2.MachineImage.lookup(
                name="ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20211129"),

            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            allow_all_outbound=True,
            vpc=vpc,
            role=role,
            block_devices=[ec2.BlockDevice(
                device_name="/dev/sda1",
                volume=ec2.BlockDeviceVolume(
                    ebs_device=ec2.EbsDeviceProps(
                            # Doesn't need to persist
                            delete_on_termination=True,
                            # 20 GB
                            volume_size=20
                    )
                )
            )],
        )

        # add the ssm managed policy
        if add_ssm_instance_permissions:
            # the base managed policy
            instance.role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        # create SSH security group
        csiro_sg = CsiroSshSecurityGroup(
            scope=self,
            id='ssh-sg',
            vpc=vpc
        )

        # Add ssh group
        instance.add_security_group(csiro_sg.sg)

        # add static IP if required
        if static_ip:
            eip = ec2.CfnEIP(
                self,
                'eip',
                domain="vpc",
                instance_id=instance.instance_id
            )

        self.instance = instance
