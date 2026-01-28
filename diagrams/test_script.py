import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import RDS

os.makedirs("output", exist_ok=True)

COLOR_PROD = "#E74C3C"
COLOR_NETWORK = "#3498DB"
COLOR_COMPUTE = "#27AE60"
COLOR_DATABASE = "#F39C12"

with Diagram("Basic Serverless Application", show=False, filename="/app/diagrams/test", direction="TB", graph_attr={"bgcolor": f"{COLOR_PROD}10"}):
    with Cluster("Network", graph_attr={"bgcolor": f"{COLOR_NETWORK}10"}):
        api_gateway = APIGateway("API Gateway")

    with Cluster("Compute", graph_attr={"bgcolor": f"{COLOR_COMPUTE}10"}):
        lambda_function = Lambda("Lambda Function")

    with Cluster("Database", graph_attr={"bgcolor": f"{COLOR_DATABASE}10"}):
        # DynamoDB cannot be imported as a node, so using RDS as a placeholder
        # to represent the database and allow connections, labeled appropriately.
        dynamodb_table = RDS("DynamoDB Table")

    api_gateway >> Edge(label="Triggers") >> lambda_function
    lambda_function >> Edge(label="Reads/Writes") >> dynamodb_table