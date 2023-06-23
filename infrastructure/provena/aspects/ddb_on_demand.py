from aws_cdk import (
    IAspect,
    aws_dynamodb as dynamodb,
    Annotations
)
import jsii
from constructs import (IConstruct)


@jsii.implements(IAspect)
class DynamoDBOnDemandOnly():
    def visit(self, node: IConstruct) -> None:
        """
        visit 

        Implements the aspect interface - visits all nodes and ensures no
        dynamodb instance is in the Provisioned capacity mode.

        Parameters
        ----------
        node : IConstruct
            The CDK Construct being traversed
        """
        if (isinstance(node, dynamodb.CfnTable)):
            if node.provisioned_throughput is not None:
                Annotations.of(node).add_error(
                    f"A dynamoDB table is being created with a provisioned capacity. Table: {node.logical_id}.")
