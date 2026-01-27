import os
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway, NATGateway, SecurityGroup
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDSProxy, RDS, DynamoDB
from diagrams.aws.management import Cloudwatch, Cloudtrail

# 1. Setup Output Directory
os.makedirs("output", exist_ok=True)

# 2. Initialize Diagram
with Diagram("API RESTful Serverless Empresarial Segura con VPC", show=False, filename="output/api_restful_serverless_empresarial_segura_con_vpc", direction="TB"):
    # 3. Define Global Nodes
    api_gateway = APIGateway("API Gateway")
    dynamodb = DynamoDB("DynamoDB Table")

    # 4. Define Clusters
    with Cluster("Amazon VPC"):
        lambda_function = Lambda("Lambda Function")
        rds_proxy = RDSProxy("RDS Proxy")
        rds = RDS("RDS Instance")
        nat_gateway = NATGateway("NAT Gateway")
        sg_lambda = SecurityGroup("Security Group (Lambda)")
        sg_rds_proxy = SecurityGroup("Security Group (RDS/Proxy)")

    with Cluster("Monitoring & Logging"):
        cloudwatch = Cloudwatch("CloudWatch")
        cloudtrail = Cloudtrail("CloudTrail")

    # 5. Define Flows (None specified in Blueprint)
    # api_gateway >> lambda_function
    # lambda_function >> rds_proxy
    # rds_proxy >> rds
    # lambda_function >> dynamodb
    # lambda_function >> nat_gateway
    # lambda_function - sg_lambda
    # rds_proxy - sg_rds_proxy
    # rds - sg_rds_proxy
    # lambda_function >> cloudwatch
    # lambda_function >> cloudtrail