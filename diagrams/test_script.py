import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3

os.makedirs("output", exist_ok=True)

COLOR_PROD = "#E74C3C"

with Diagram("Basic Serverless API with Data Storage", show=False, filename="/app/diagrams/test", direction="TB"):
    with Cluster("Network", graph_attr={"bgcolor": f"{COLOR_PROD}10"}):
        api_gateway = APIGateway("API Gateway")

    with Cluster("Compute", graph_attr={"bgcolor": f"{COLOR_PROD}10"}):
        lambda_function = Lambda("Lambda Function")

    with Cluster("Database", graph_attr={"bgcolor": f"{COLOR_PROD}10"}):
        dynamodb_table = Cluster("DynamoDB Table")

    with Cluster("Storage", graph_attr={"bgcolor": f"{COLOR_PROD}10"}):
        s3_bucket = S3("S3 Bucket")

    api_gateway >> Edge(label="triggers") >> lambda_function
    lambda_function >> Edge(label="reads_writes") >> dynamodb_table
    lambda_function >> Edge(label="reads_writes") >> s3_bucket