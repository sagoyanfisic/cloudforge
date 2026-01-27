import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import RDS

os.makedirs("output", exist_ok=True)

with Diagram("API REST Serverless Híbrida con Observabilidad", show=False, filename="/app/diagrams/serverless", direction="TB"):
    api_gateway = APIGateway("API Gateway")
    lambda_function = Lambda("Lambda Function")
    rds_instance = RDS("RDS Instance")

    # DynamoDB and CloudWatch are represented as Clusters as per instructions
    # For connection purposes, a placeholder node (Lambda) is used inside the Cluster
    # as specific DynamoDB/CloudWatch node classes are not importable.
    with Cluster("DynamoDB"):
        dynamodb_table = Lambda("DynamoDB