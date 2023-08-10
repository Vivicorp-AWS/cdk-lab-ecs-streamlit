#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.vpc_stack import VPCStack
from stacks.ecs_stack import (
    ECSFargatePublicSubnetStack,
    ECSFargatePrivateSubnetStack,
    )
from constructs import Construct

app = cdk.App()

class TopStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)

# [NOTE] The prefix (such as "Lab-") is recommended, and can't be started with preserved words like "aws", "ecs", ...etc.,
# to avoid the error when creating ECSStack (This is a hard requirement for ECS service)
top_stack = TopStack(app, "StreamlitECSLAB",)

vpc_stack = VPCStack(top_stack, "VPCStack",)
vpc = vpc_stack.vpc

ecs_stack = ECSFargatePublicSubnetStack(top_stack, "PublicECSPStack", vpc=vpc,)
# ecs_stack = ECSFargatePrivateSubnetStack(top_stack, "PrivateECSPStack", vpc=vpc,)

app.synth()
