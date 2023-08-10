from aws_cdk import (
    NestedStack,
    aws_ec2 as ec2,
)
from constructs import Construct

class VPCStack(NestedStack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create 2 AZs x 2 Types of Subnets = 4 Subnets
        self.vpc = ec2.Vpc(
            self, "VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.10.0.0/16"),
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="public",
                    cidr_mask=24
                    ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="private",
                    cidr_mask=24
                    )
                ],
            )
