import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway

os.makedirs("output", exist_ok=True)

COLOR_PROD = "#E74C3C"
COLOR_NETWORK = "#3498DB"
COLOR_COMPUTE = "#27AE60"
COLOR_DATABASE = "#F39C12"

with Diagram("Production Serverless API", show=False, filename="/app/diagrams/procesamiento1", direction="TB"):
    with Cluster("Network", graph_attr={"bgcolor": f"{COLOR_NETWORK}10"}):
        api_gateway = APIGateway("API Gateway")

    with Cluster("Compute", graph_attr={"bgcolor": f"{COLOR_COMPUTE}10"}):
        lambda_function = Lambda("Lambda Function")

    with Cluster("Database", graph_attr={"bgcolor": f"{COLOR_DATABASE}10"}):
        dynamodb_table = Cluster("DynamoDB Table")

    api_gateway >> Edge(label="Triggers") >> lambda_function
    lambda_function >> Edge(label="Reads/Writes") >> dynamodb_table