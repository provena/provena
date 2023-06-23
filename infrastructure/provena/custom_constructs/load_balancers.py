from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elb,
    aws_elasticloadbalancingv2_targets as targets,
    aws_ecs as ecs,
    aws_certificatemanager as acm,
    Duration
)
from constructs import Construct
from typing import Optional, List, Any, Dict


class SharedBalancers(Construct):
    https_port: int = 443
    http_port: int = 80

    def __init__(self, scope: Construct,
                 id: str,
                 **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # balancers
        self.alb: Optional[elb.ApplicationLoadBalancer] = None
        self.nlb: Optional[elb.NetworkLoadBalancer] = None

        # listeners
        self.https_listener: Optional[elb.ApplicationListener] = None
        self.http_listener: Optional[elb.ApplicationListener] = None
    
        
    def setup_alb(
        self,
        vpc: ec2.Vpc,
        public: bool = True,
        subnet_type: ec2.SubnetType = ec2.SubnetType.PUBLIC,
    ) -> elb.ApplicationLoadBalancer:
        if self.alb is not None:
            raise Exception(f"ALB already established.")

        self.alb = elb.ApplicationLoadBalancer(
            self,
            "alb",
            vpc=vpc,
            internet_facing=public,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=subnet_type
            )
        )

        return self.alb

    def setup_nlb(
        self,
        vpc: ec2.Vpc,
        public: bool = True,
        subnet_type: ec2.SubnetType = ec2.SubnetType.PUBLIC,
    ) -> elb.NetworkLoadBalancer:
        if self.nlb is not None:
            raise Exception(f"NLB already established.")

        self.nlb = elb.NetworkLoadBalancer(
            scope=self,
            id="nlb",
            vpc=vpc,
            internet_facing=public,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=subnet_type
            )
        )

        return self.nlb

    def setup_https_listener(
        self,
        certificates: List[elb.ListenerCertificate] = []
    ) -> elb.ApplicationListener:
        if self.https_listener is not None:
            raise Exception(f"HTTPS listener already established!")
        if self.alb is None:
            raise Exception(
                f"Cannot setup https listener without establishing alb.")

        # this sets up a basic 443 https listener ready to receive new action/target combos
        self.https_listener = elb.ApplicationListener(
            scope=self,
            id='https-listener',
            load_balancer=self.alb,
            certificates=certificates,
            default_action=elb.ListenerAction.fixed_response(
                status_code=404,  # not found
                content_type="text/plain",
                message_body="Service does not exist. Contact administrator if you believe this is an error."
            ),
            port=self.https_port
        )

        return self.https_listener

    def setup_http_listener(
        self,
    ) -> elb.ApplicationListener:
        if self.alb is None:
            raise Exception(
                f"Cannot setup http listener without establishing alb.")

        # this sets up a basic 443 https listener ready to receive new action/target combos
        self.http_listener = elb.ApplicationListener(
            scope=self,
            id='http-listener',
            load_balancer=self.alb,
            default_action=elb.ListenerAction.fixed_response(
                status_code=404,  # not found
                content_type="text/plain",
                message_body="Service does not exist. Contact administrator if you believe this is an error."
            ),
            port=self.http_port
        )

        return self.http_listener

    def add_https_certificates(
        self,
        id: str,
        certificates: List[elb.ListenerCertificate],
    ) -> None:
        if self.https_listener is None:
            raise Exception(f"HTTPS listener not established!")

        self.https_listener.add_certificates(
            id=id,
            certificates=certificates
        )

    def add_http_redirected_conditional_https_target(
        self,
        action_id: str,
        target_group: elb.ApplicationTargetGroup,
        conditions: List[elb.ListenerCondition],
        priority: int,
        http_redirect_priority: int
    ) -> None:
        if self.https_listener is None:
            raise Exception(f"HTTPS listener not established!")
        if self.http_listener is None:
            raise Exception(f"HTTP listener not established!")

        # add the listener action on https listener
        self.https_listener.add_action(
            id=action_id,
            action=elb.ListenerAction.forward(
                target_groups=[target_group]
            ),
            conditions=conditions,
            priority=priority
        )

        # and add http redirect
        self.http_listener.add_action(
            id=f"{action_id}-https-redirect",
            action=elb.ListenerAction.redirect(
                permanent=True,
                port=str(self.https_port),
                protocol="HTTPS"
            ),
            # redirect via the same conditions
            conditions=conditions,
            priority=http_redirect_priority
        )

    def add_conditional_http_route(
        self,
        id: str,
        target_group: elb.ApplicationTargetGroup,
        conditions: List[elb.ListenerCondition],
        priority: int
    ) -> None:
        if self.http_listener is None:
            raise Exception(f'HTTP listener must be setup.')

        self.http_listener.add_action(
            id=id,
            action=elb.ListenerAction.forward(
                target_groups=[target_group]
            ),
            conditions=conditions,
            priority=priority
        )

    def add_tcp_route(
        self,
        id: str,
        source_port: int,
        target_group: elb.NetworkTargetGroup,
    ) -> None:
        """
        setup_tcp_route 

        Setup an ELB listener listening on given source port targeting target
        group.

        Parameters
        ----------
        id : str
            A unique name
        source_port : int
            The source TCP port
        target_group : elb.NetworkTargetGroup
            The target group accepting TCP traffic

        Raises
        ------
        Exception
            NLB not setup
        """
        if self.nlb is None:
            raise Exception(f'Network load balancer is not setup.')

        # Listen on this balancer for each port
        listener = self.nlb.add_listener(
            f"{id}Listener{source_port}",
            port=source_port,
            protocol=elb.Protocol.TCP
        )

        # Associate listeners to target groups
        listener.add_target_groups(
            f"{id}Actions",
            target_group
        )