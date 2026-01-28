import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3

os.makedirs("output", exist_ok=True)

COLOR_PROD = "#E74C3C"
COLOR_NETWORK = "#9B59B6"
COLOR_COMPUTE = "#3498DB"
COLOR_DATABASE = "#27AE60"
COLOR_STORAGE = "#F39C12"

with Diagram("AWS Serverless Architecture", show=False, filename="/app/diagrams/serverless_cdn", direction="TB"):
    with Cluster("Network", graph_attr={"bgcolor": f"{COLOR_NETWORK}10"}):
        api_gw = APIGateway("API Gateway")

    with Cluster("Compute", graph_attr={"bgcolor": f"{COLOR_COMPUTE}10"}):
        lambda_func = Lambda("Lambda Function")

    with Cluster("Database", graph_attr={"bgcolor": f"{COLOR_DATABASE}10"}):
        dynamodb_table = RDS("DynamoDB Table")

    with Cluster("Storage", graph_attr={"bgcolor": f"{COLOR_STORAGE}10"}):
        s3_bucket = S3("S3 Bucket")

    api_gw >> Edge(label="Triggers") >> lambda_func
    lambda_func >> Edge(label="Reads/Writes") >> dynamodb_table
    lambda_func >> Edge(label="Reads/Writes") >> s3_bucket