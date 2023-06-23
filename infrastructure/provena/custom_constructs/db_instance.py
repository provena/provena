from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    Duration,
    RemovalPolicy
)
from constructs import Construct
from typing import Optional, Any

# Setting for RDS instance
BACKUP_RETENTION_DAYS = 10
BACKUP_DURATION = Duration.days(BACKUP_RETENTION_DAYS)
NO_BACKUP_DURATION = Duration.days(0)
RDS_POSTGRES_VERSION = rds.PostgresEngineVersion.VER_13_7
INSTANCE_TYPE = ec2.InstanceType.of(
    instance_class=ec2.InstanceClass.BURSTABLE3,
    instance_size=ec2.InstanceSize.MEDIUM
)


class DBInstance(Construct):
    def __init__(self, scope: Construct,
                 id: str,
                 service_name: str,
                 vpc: ec2.Vpc,
                 backup_duration: Optional[Duration] = NO_BACKUP_DURATION,
                 public: Optional[bool] = True,
                 default_database_name: Optional[str] = "keycloak",
                 user_name: str = "keycloak",
                 removal_policy: Optional[RemovalPolicy] = RemovalPolicy.SNAPSHOT,
                 **kwargs: Any) -> None:
        """Creates a database cluster from an existing cluster snapshot.

        Args:
            scope (cdk.Construct): CDK construct scope
            id (str): The CDK id 
            service_name (str): The name of the service (prefixes to most names, e.g. "db")
            vpc (ec2.Vpc): The VPC in which to deploy the cluster
            backup_duration (Optional[cdk.Duration], optional): The amount of time to store backups for. Defaults to disabled.
            public (Optional[bool], optional): Should the db be exposed to the public - will place it in a public subnet if so. Defaults to True.
            default_database_name (Optional[str], optional): The name of the database within the db. Defaults to "hydrokg".
            user_name (Optional[str], optional): The name of the root user. Defaults to "hydrokg".
            removal_policy (Optional[cdk.RemovalPolicy], optional): What should happen when the cluster is removed. Defaults to cdk.RemovalPolicy.SNAPSHOT.
        """

        # Super constructor
        super().__init__(scope, id, **kwargs)

        # Restore from cluster backup
        self.instance = rds.DatabaseInstance(
            self,
            id=f"{service_name}DBInstance",
            # Setup credentials to use specified user name
            credentials=rds.Credentials.from_username(user_name),
            allocated_storage=20,
            database_name=default_database_name,
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
