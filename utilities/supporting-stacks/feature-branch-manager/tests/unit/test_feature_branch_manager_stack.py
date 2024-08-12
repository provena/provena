import aws_cdk as core
import aws_cdk.assertions as assertions

from feature_branch_manager.feature_branch_manager_stack import FeatureBranchManagerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in feature_branch_manager/feature_branch_manager_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FeatureBranchManagerStack(app, "feature-branch-manager")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
