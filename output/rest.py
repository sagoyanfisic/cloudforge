import os
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway, NATGateway
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS, DynamoDB
from diagrams.aws.management import CloudWatch, CloudTrail
from diagrams.storage import S3

os.makedirs("output", exist_ok=True)

with Diagram("API REST Serverless Híbrida con Multi-Base de Datos", show=False, filename="output/serverless_api", direction="TB"):
    # Public layer
    api_gw = APIGateway("REST API")

    # Private subnets (use Cluster, NOT from import)
    with Cluster("VPC - Private Subnet"):
        with Cluster("Compute"):
            lambda_func = Lambda("Lambda Function")

        with Cluster("Database Tier"):
            rds_instance = RDS("RDS Instance (PostgreSQL/MySQL)")
            dynamodb_table = DynamoDB("DynamoDB Table")

    # Monitoring
    cw_logs = CloudWatch("CloudWatch Logs")
    ct_trail = CloudTrail("CloudTrail")

    # Flows
    api_gw >> lambda_func
    lambda_func >> rds_instance
    lambda_func >> dynamodb_table
    lambda_func >> cw_logs