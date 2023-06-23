from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    Duration
)
from constructs import Construct

from typing import List, Dict, Optional, Any


class Cluster(Construct):
    def __init__(self, scope: Construct,
                 id: str,
                 service_name: str,
                 vpc: ec2.Vpc,
                 cpu: int,
                 memory: int,
                 desired_count: int,
                 open_tcp_ports: Optional[List[int]] = None,
                 **kwargs: Any) -> None:
        """Creates an ECS fargate cluster hosting a single instance which auto scales.
        Could be extended to have multiple containers.
        This method does not produce any auto scaling configuration. It is assumed you will
        use an application load balancer to distribute traffic to this instance and that construct
        provides a method to register this service as an auto scaling target.

        Args:
            scope (cdk.Construct): The CDK scope.
            id (str): The CDK id for this construct.
            service_name (str): The semantic name of the service e.g. "api" "db" etc
            vpc (ec2.Vpc): The VPC in which to launch the ECS cluster.
            cpu (int): The amount of CPU units (1024=1 vCPU) to use for this container e.g. 1024
            memory (int): The amount of memory (in MiB) e.g. 2048
            desired_count (int): The target live count.
            open_tcp_ports (Optional[List[int]], optional): If the load balancer does not automatically expose a security group
            entry for your port, you can specify that the security group have these ports open for TCP traffic. If you
            are using TCP load balancers (network load balancers), you should use this parameter. Defaults to None.
        """
        # Super constructor
        super().__init__(scope, id, **kwargs)

        # Create cluster
        # This also produces VPC with two AZ's by default
        self.cluster = ecs.Cluster(
            self,
            f"{service_name}ECSCluster",
            vpc=vpc
        )

        # Create a task definition
        self.task_definition = ecs.FargateTaskDefinition(
            self,
            f"{service_name}FargateTask",
            cpu=cpu,
            memory_limit_mib=memory
        )

        # Create fargate service
        self.service = ecs.FargateService(
            self,
            f"{service_name}FargateService",
            cluster=self.cluster,
            task_definition=self.task_definition,
            desired_count=desired_count,
            assign_public_ip=True,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            health_check_grace_period=Duration.seconds(180)
        )

        # Enable access on specified TCP ports
        # TODO tighten to only allow balancer traffic rather
        # than vpc wide traffic
        if open_tcp_ports:
            for port in open_tcp_ports:
                self.service.connections.allow_from(
                    ec2.Peer.ipv4(vpc.vpc_cidr_block),
                    port_range=ec2.Port.tcp(port),
                    description=f"Allow VPC connections on {port=}."
                )

    def add_container_to_service(
            self,
            service_name: str,
            port_mappings: List[ecs.PortMapping],
            container: ecs.ContainerImage,
            environment_variables: Dict[str, str],
            secret_environment_variables: Dict[str, ecs.Secret],
            custom_health_check: Optional[ecs.HealthCheck] = None
    ) -> None:
        # Create the container, in this case a port 80 http application
        optional_args: Dict[str, Any] = {}

        # only provide custom health check arg if provided
        if custom_health_check is not None:
            optional_args["health_check"] = custom_health_check

        self.task_definition.add_container(
            f"{service_name}FargateTaskContainer",
            image=container,
            port_mappings=port_mappings,
            environment=environment_variables,
            secrets=secret_environment_variables,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=f"provena-{service_name}",
                log_retention=logs.RetentionDays.ONE_MONTH
            ),
            **optional_args
        )
