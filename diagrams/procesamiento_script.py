import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway

os.makedirs("output", exist_ok=True)

COLOR_PROD = "#E74C3C"

with Diagram("Serverless REST API", show=False, filename="/app/diagrams/procesamiento", direction="TB"):
    with Cluster("Network", graph_attr={"bgcolor": f"{COLOR_PROD}10"}):
        api_gateway = APIGateway("API Gateway")

    with Cluster("Compute", graph_attr={"bgcolor": f"{COLOR_PROD}10"}):
        lambda_function = Lambda("Lambda Function")

    api_gateway >> Edge(label="triggers") >> lambda_function