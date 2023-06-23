from aws_cdk import (
    Stack,
    CfnOutput
)


def get_output_name(output: CfnOutput) -> str:
    """
    get_output_name 
    Gets the output name of a CfnOutput by resolving its logical id using its
    stack as context
    Parameters
    ----------
    output : CfnOutput
        The output to resolve
    Returns
    -------
    str
        The logical name
    """
    stack = Stack.of(output)
    name = stack.resolve(output.logical_id)
    return name


def get_stack_name(output: CfnOutput) -> str:
    """
    get_stack_name 
    Gets the stack name of a CfnOutput
    Parameters
    ----------
    output : CfnOutput
        The output to resolve
    Returns
    -------
    str
        The stack name
    """
    return Stack.of(output).stack_name
