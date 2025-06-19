from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    Duration,
    RemovalPolicy,
)
from constructs import Construct
from typing import Optional, Any

from provena.custom_constructs.db_instance import INSTANCE_TYPE

# Setting for RDS instance
BACKUP_RETENTION_DAYS = 10
BACKUP_DURATION = Duration.days(BACKUP_RETENTION_DAYS)
NO_BACKUP_DURATION = Duration.days(0)

# Bump up the version due to minor updates
# if you try to update from snapshot using a specified older version RDS service tries to "update" backwards from new version -> older.
# make sure that this value reflects the actual current version of the restoring instance

RDS_POSTGRES_VERSION = rds.PostgresEngineVersion.VER_13_16

DEV_INSTANCE_TYPE = ec2.InstanceType.of(
    instance_class=ec2.InstanceClass.BURSTABLE3,
    instance_size=ec2.InstanceSize.MICRO
)
DEFAULT_INSTANCE_TYPE = ec2.InstanceType.of(
    instance_class=ec2.InstanceClass.BURSTABLE3,
    instance_size=ec2.InstanceSize.MEDIUM
)


class DBInstanceFromSnapshot(Construct):
    def __init__(self, scope: Construct,
                 id: str,
                 service_name: str,
                 stage: str,
                 vpc: ec2.Vpc,
                 snapshot_arn: str,
                 backup_duration: Optional[Duration] = NO_BACKUP_DURATION,
                 public: Optional[bool] = True,
                 user_name: str = "keycloak",
                 removal_policy: Optional[RemovalPolicy] = RemovalPolicy.SNAPSHOT,
                 **kwargs: Any) -> None:
        """Creates a database cluster from an existing cluster snapshot.

        Args:
            scope (cdk.Construct): CDK construct scope
            id (str): The CDK id 
            service_name (str): The name of the service (prefixes to most names, e.g. "db")
            vpc (ec2.Vpc): The VPC in which to deploy the cluster
            snapshot_arn (str): The ARN of the cluster snapshot
            instances (int, optional): The number of instances to launch, act as read + write replicas. Defaults to 1.
            backup_duration (Optional[cdk.Duration], optional): The amount of time to store backups for. Defaults to backups disabled (zero duration).
            public (Optional[bool], optional): Should the db be exposed to the public - will place it in a public subnet if so. Defaults to True.
            user_name (Optional[str], optional): The name of the root user. Defaults to "hydrokg".
            removal_policy (Optional[cdk.RemovalPolicy], optional): What should happen when the cluster is removed. Defaults to cdk.RemovalPolicy.SNAPSHOT.
        """

        # Super constructor
        super().__init__(scope, id, **kwargs)

        if stage in ['DEV', 'STAGE', 'TEST']:
            INSTANCE_TYPE = DEV_INSTANCE_TYPE
        else:
            INSTANCE_TYPE = DEFAULT_INSTANCE_TYPE

        # Restore from cluster backup
        self.instance = rds.DatabaseInstanceFromSnapshot(
            self,
            id=f"{service_name}DBSnapshotInstance",
            # Setup credentials to use specified user name
            credentials=rds.SnapshotCredentials.from_generated_secret(
                username=user_name),
            snapshot_identifier=snapshot_arn,
            allocated_storage=20,
            engine=rds.DatabaseInstanceEngine.postgres(
                version=RDS_POSTGRES_VERSION),
            instance_type=INSTANCE_TYPE,
            publicly_accessible=public,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC if public else \
                ec2.SubnetType.PRIVATE_ISOLATED
            ),
            backup_retention=backup_duration,
            removal_policy=removal_policy,
            vpc=vpc,
            allow_major_version_upgrade=False,
            auto_minor_version_upgrade=True,
            port=5432
        )

        # Allow security group access to RDS
        if public:
            self.instance.connections.allow_default_port_from_any_ipv4(
                "Allow traffic from all IPs to db (authenticated)."
            )

        self.secret = self.instance.secret

    def give_connectable_access(self, connection: ec2.IConnectable) -> None:
        self.instance.connections.allow_default_port_from(connection)
