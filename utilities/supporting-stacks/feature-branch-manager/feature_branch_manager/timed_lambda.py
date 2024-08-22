from aws_cdk import (
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
)
from constructs import Construct
from typing import Dict, Optional, Any

RULE_POSTFIX = "_rule"
EVENT_POSTFIX = "_timer"


class TimedLambda(Construct):
    """
    Defines a construct for containing a lambda 
    function which is invoked at a specified rate.
    """

    @property
    def lambda_function(self) -> _lambda.Function:
        return self._lambda

    @property
    def schedule(self) -> events.Schedule:
        return self._schedule

    def __init__(self,
                 scope: Construct,
                 construct_id: str,
                 lambda_function : _lambda.Function,
                 schedule_expression: str,
                 event_contents: Optional[Dict] = None,
                 **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the schedule from the expression
        timer_schedule = events.Schedule.expression(schedule_expression)

        # Target the lambda

        # If a custom event context is provided then we add that using
        # the dictionary converter method
        if event_contents:
            rule_target_input = events.RuleTargetInput.from_object(
                event_contents)
            lambda_target = targets.LambdaFunction(
                lambda_function,
                event=rule_target_input
            )
        # otherwise just send the default event.
        else:
            lambda_target = targets.LambdaFunction(lambda_function)

        # Create the rule according to schedule
        events.Rule(self,
                    construct_id + RULE_POSTFIX,
                    schedule=timer_schedule,
                    targets=[lambda_target])

        self._schedule = timer_schedule
        self._lambda = lambda_function
