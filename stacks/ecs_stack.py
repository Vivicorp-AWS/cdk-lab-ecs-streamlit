from aws_cdk import (
    NestedStack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling,
    custom_resources as cr,
    aws_ecs_patterns as ecs_patterns,
    Duration,
    CfnOutput,
)
from constructs import Construct

class ECSFargatePublicSubnetStack(NestedStack):

    def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a ECS Cluster
        cluster = ecs.Cluster(
            self, "Cluster",
            vpc=vpc,  # If not set, add capacity via ecs.Cluster.add_capacity,
                      # and a VPC with 2 AZs will be created automatically
        )

        # Add an AutoScalingGroup with spot instances to the existing cluster
        # # [NOTE] This was copied from https://github.com/aws-samples/generative-ai-sagemaker-cdk-demo/blob/e6f9e6351014d23f3172b7109000903008f6313e/stack/generative_ai_demo_web_stack.py#L77
        # # and is replaced by calling ecs.Cluster.add_asg_capacity_provider()
        # cluster.add_capacity("AsgSpot",
        #     max_capacity=2,
        #     min_capacity=1,
        #     desired_capacity=2,
        #     instance_type=ec2.InstanceType("t4g.micro"),
        #     machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.ARM),
        #     # spot_price="0.0016",
        #     spot_instance_draining=True,  # Enable the Automated Spot Draining support for Amazon ECS
        # )

        # Use Cluster.add_asg_capacity_provider instead of calling cluster.add_capacity()
        auto_scaling_group = autoscaling.AutoScalingGroup(
            self, "ASG",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_type=ec2.InstanceType("t4g.micro"),
        machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.ARM),
            max_capacity=2,
            min_capacity=1,
            # spot_price="0.0016",
        )

        capacity_provider = ecs.AsgCapacityProvider(
            self, "ASGCapacityProvider",
            auto_scaling_group=auto_scaling_group,
        )

        cluster.add_asg_capacity_provider(
            provider=capacity_provider,
            spot_instance_draining=True,
        )

        # "Unable to delete CDK Auto Scaling Group" issue
        # Ref: https://github.com/aws/aws-cdk/issues/18179#issuecomment-1150981559
        auto_scaling_group_force_delete = cr.AwsCustomResource(
            self, "ASGForceDelete",
            on_delete=cr.AwsSdkCall(
                service="AutoScaling",
                action="deleteAutoScalingGroup",
                parameters={
                    "AutoScalingGroupName": auto_scaling_group.auto_scaling_group_name,
                    "ForceDelete": True,
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE,),
        )
        auto_scaling_group_force_delete.node.add_dependency(auto_scaling_group)

        # Build Dockerfile from local folder and push to ECR
        image = ecs.ContainerImage.from_asset("streamlit-app")

        # Create Fargate service
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "StreamlitApplication",
            cluster=cluster,  # Required
            memory_limit_mib=1024,  # Default is 512, and this will affect cpu parameter's option
            cpu=512,  # Default is 256 (512 is 0.5 vCPU, 2048 is 2 vCPU)
            desired_count=1,  # Default is 1
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image, 
                container_port=8501,
                ),
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            assign_public_ip=True,  # Must assign True. If not, will face "unable to pull secrets or registry auth: execution resource retrieval failed: unable to retrieve ecr registry auth" error
            public_load_balancer=True,  # Default is True
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )
        # To add IAM policy to the task role,
        # call fargate_service.task_definition.add_to_task_role_policy()
        # to add policy to the task role
        # (FargateTaskDefinition.task_role, )

        # [NOTE] ECS task role vs ECS execution role:
        # ECS task role "is essential when the application in your ECS container running on Fargate or EC2 needs to access other AWS Services like an S3 bucket"
        # ECS execution role "grants the Amazon ECS container and Fargate agents permission to make AWS API calls on your behalf"
        # Ref: https://towardsthecloud.com/amazon-ecs-task-role-vs-execution-role

        # Setup task auto-scaling
        scaling = fargate_service.service.auto_scale_task_count(
            max_capacity=4,
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

class ECSFargatePrivateSubnetStack(NestedStack):

    def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a ECS Cluster
        cluster = ecs.Cluster(
            self, "Cluster",
            vpc=vpc,  # If not set, add capacity via ecs.Cluster.add_capacity,
                      # and a VPC with 2 AZs will be created automatically
        )

        # # Add an AutoScalingGroup with spot instances to the existing cluster
        # # [NOTE] This was copied from https://github.com/aws-samples/generative-ai-sagemaker-cdk-demo/blob/e6f9e6351014d23f3172b7109000903008f6313e/stack/generative_ai_demo_web_stack.py#L77
        # # and is replaced by calling ecs.Cluster.add_asg_capacity_provider()
        # cluster.add_capacity("AsgSpot",
        #     max_capacity=2,
        #     min_capacity=1,
        #     desired_capacity=2,
        #     instance_type=ec2.InstanceType("t4g.micro"),
        #     machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.ARM),
        #     # spot_price="0.0016",
        #     spot_instance_draining=True,  # Enable the Automated Spot Draining support for Amazon ECS
        # )

        # Use Cluster.add_asg_capacity_provider instead of calling cluster.add_capacity()
        auto_scaling_group = autoscaling.AutoScalingGroup(
            self, "ASG",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            instance_type=ec2.InstanceType("t4g.micro"),
        machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.ARM),
            max_capacity=2,
            min_capacity=1,
            # spot_price="0.0016",
        )

        capacity_provider = ecs.AsgCapacityProvider(
            self, "ASGCapacityProvider",
            auto_scaling_group=auto_scaling_group,
        )

        cluster.add_asg_capacity_provider(
            provider=capacity_provider,
            spot_instance_draining=True,
        )

        # "Unable to delete CDK Auto Scaling Group" issue
        # Ref: https://github.com/aws/aws-cdk/issues/18179#issuecomment-1150981559
        auto_scaling_group_force_delete = cr.AwsCustomResource(
            self, "ASGForceDelete",
            on_delete=cr.AwsSdkCall(
                service="AutoScaling",
                action="deleteAutoScalingGroup",
                parameters={
                    "AutoScalingGroupName": auto_scaling_group.auto_scaling_group_name,
                    "ForceDelete": True,
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE,),
        )
        auto_scaling_group_force_delete.node.add_dependency(auto_scaling_group)

        # Build Dockerfile from local folder and push to ECR
        image = ecs.ContainerImage.from_asset("streamlit-app")

        # Create Fargate service
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "StreamlitApplication",
            cluster=cluster,  # Required
            memory_limit_mib=1024,  # Default is 512, and this will affect cpu parameter's option
            cpu=512,  # Default is 256 (512 is 0.5 vCPU, 2048 is 2 vCPU)
            desired_count=1,  # Default is 1
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image, 
                container_port=8501,
                ),
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            public_load_balancer=True,  # Default is True
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )
        # To add IAM policy to the task role,
        # call fargate_service.task_definition.add_to_task_role_policy()
        # to add policy to the task role
        # (FargateTaskDefinition.task_role, )

        # [NOTE] ECS task role vs ECS execution role:
        # ECS task role "is essential when the application in your ECS container running on Fargate or EC2 needs to access other AWS Services like an S3 bucket"
        # ECS execution role "grants the Amazon ECS container and Fargate agents permission to make AWS API calls on your behalf"
        # Ref: https://towardsthecloud.com/amazon-ecs-task-role-vs-execution-role

        # Setup task auto-scaling
        scaling = fargate_service.service.auto_scale_task_count(
            max_capacity=4,
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        CfnOutput(self, "LoadBalancerDNSName", value=fargate_service.load_balancer.load_balancer_dns_name)