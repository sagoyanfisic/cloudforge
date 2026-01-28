import os
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway, NATGateway
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS, DynamoDB
from diagrams.aws.management import CloudWatch, CloudTrail

os.makedirs("output", exist_ok=True)

with Diagram("API RESTful Empresarial Serverless con Persistencia Híbrida", show=False, filename="output/serverless_enterprise_api", direction="TB"):
    # Public facing components
    api_gateway = APIGateway("REST API")

    # Monitoring and Auditing services
    cloudwatch = CloudWatch("Monitoring & Logs")
    cloudtrail = CloudTrail("Audit Trail")

    with Cluster("VPC"): # Represents the Amazon Virtual Private Cloud
        # NAT Gateway for outbound internet access from private subnets
        # Typically resides in a Public Subnet, but shown here for connectivity from Private Subnet
        nat_gateway = NATGateway("NAT Gateway")

        with Cluster("VPC - Private Subnet"):
            # Lambda Function within its Security Group
            with Cluster("Security Group - Lambda"):
                lambda_function = Lambda("API Handler")

            # Database Tier within its own Security Group
            with Cluster("VPC - Database Tier"):
                with Cluster("Security Group - RDS"):
                    rds_instance = RDS("PostgreSQL DB")
                dynamodb_table = DynamoDB("NoSQL Table")

    # Define the relationships (flows)
    api_gateway >> lambda_function

    # Lambda needs outbound internet access (e.g., for external APIs, updates)
    # via the NAT Gateway as it's in a private subnet.
    lambda_function >> nat_gateway

    # Lambda interacts with the databases
    lambda_function >> rds_instance
    lambda_function >> dynamodb_table

    # Lambda sends logs and metrics to CloudWatch
    lambda_function >> cloudwatch

    # API Gateway also sends logs and metrics to CloudWatch
    api_gateway >> cloudwatch

    # CloudTrail monitors API calls across all AWS services for auditing
    # (No direct arrow from CloudWatch to CloudTrail is specified in blueprint,
    # they operate as separate monitoring/auditing services)