from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_s3_deployment as s3_deployment,
    aws_ecr_assets as ecr_assets,
    CfnOutput,
)
import aws_cdk as cdk
from constructs import Construct

class IacStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for the project
        bucket = s3.Bucket(
            self, "CreditScoringDataBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Build and push the custom SageMaker processing image to ECR
        processing_image = ecr_assets.DockerImageAsset(self, "SageMakerProcessingImage",
            directory="../sagemaker/processing",
            platform=ecr_assets.Platform.LINUX_AMD64
        )

        # Deploy other sagemaker scripts to S3 (if any)
        s3_deployment.BucketDeployment(self, "DeploySageMakerScripts",
            sources=[s3_deployment.Source.asset("../sagemaker/training")],
            destination_bucket=bucket,
            destination_key_prefix="sagemaker/training"
        )


        # IAM Role for SageMaker
        sagemaker_role = iam.Role(
            self, "SageMakerRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
            ],
        )

        # IAM Role for Step Functions
        step_functions_role = iam.Role(
            self, "StepFunctionsRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess"),
            ],
        )

        # IAM Role for Lambda
        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )

        # Lambda Function for publishing data
        publish_data_lambda = _lambda.Function(
            self, "PublishDataLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="publish_data.handler",
            code=_lambda.Code.from_asset("../src/lambdas"),
            role=lambda_role,
            timeout=cdk.Duration.seconds(60),
        )

        # Step Functions State Machine
        generate_data_job = sfn_tasks.CallAwsService(
            self, "Generate Synthetic Data",
            service="sagemaker",
            action="createProcessingJob",
            parameters={
                "ProcessingJobName": sfn.JsonPath.string_at("$.jobName"),
                "ProcessingInputs": [],
                "ProcessingOutputConfig": {
                    "Outputs": [
                        {
                            "OutputName": "synthetic_data",
                            "S3Output": {
                                "S3Uri": f"s3://{bucket.bucket_name}/raw/",
                                "LocalPath": "/opt/ml/processing/output",
                                "S3UploadMode": "EndOfJob",
                            },
                        }
                    ]
                },
                "AppSpecification": {
                    "ImageUri": processing_image.image_uri,
                    "ContainerEntrypoint": ["python3", "generate.py"],
                },
                "Environment": {
                    "NUM_ROWS": sfn.JsonPath.string_at("$.numRows"),
                    "MODEL_PATH": f"s3://{bucket.bucket_name}/model/credit_scoring_model.pkl",
                    "JOB_NAME": sfn.JsonPath.string_at("$.jobName"),
                },
                "ProcessingResources": {
                    "ClusterConfig": {
                        "InstanceCount": 1,
                        "InstanceType": "ml.t3.medium",
                        "VolumeSizeInGB": 10,
                    }
                },
                "RoleArn": sagemaker_role.role_arn,
            },
            iam_resources=["*"],
            result_path="$.sagemaker_result",
        )

        # Lambda invoker
        publish_data_task = sfn_tasks.LambdaInvoke(
            self, "Publish Data",
            lambda_function=publish_data_lambda,
            payload=sfn.TaskInput.from_object({
                "source_bucket": bucket.bucket_name,
                "source_key": sfn.JsonPath.format(
                    "processing-output/{}/{}.parquet",
                    sfn.JsonPath.string_at("$.jobName"),
                    sfn.JsonPath.string_at("$.jobName")
                ),
                "destination_key": sfn.JsonPath.format(
                    "published/{}.parquet",
                    sfn.JsonPath.string_at("$.jobName")
                )
            }),
            result_path="$.publish_result",
        )

        definition = generate_data_job.next(publish_data_task)

        state_machine = sfn.StateMachine(
            self, "CreditScoringStateMachine",
            definition=definition,
            timeout=cdk.Duration.minutes(30),
            role=step_functions_role,
        )

        # --- Outputs ---
        CfnOutput(
            self, "CreditScoringStateMachineArn",
            value=state_machine.state_machine_arn,
            description="The ARN of the Credit Scoring State Machine",
        )

        CfnOutput(
            self, "CreditScoringDataBucketName",
            value=bucket.bucket_name,
            description="The name of the S3 bucket for credit scoring data",
        )
