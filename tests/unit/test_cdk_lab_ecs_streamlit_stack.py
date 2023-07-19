import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_lab_ecs_streamlit.cdk_lab_ecs_streamlit_stack import CdkLabEcsStreamlitStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_lab_ecs_streamlit/cdk_lab_ecs_streamlit_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkLabEcsStreamlitStack(app, "cdk-lab-ecs-streamlit")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
