from aws_cdk import (
    IAspect,
    CfnResource,
    RemovalPolicy
)
import jsii
from constructs import (IConstruct)


@jsii.implements(IAspect)
class RemovalPolicyAspect():
    def visit(self, node: IConstruct) -> None:
        """
        visit 

        Implements the aspect interface - visits all nodes and applies destroy
        removal policy if possible.

        Parameters
        ----------
        node : IConstruct
            The CDK Construct being traversed
        """
        if (isinstance(node, CfnResource)):
            node.apply_removal_policy(RemovalPolicy.DESTROY)
