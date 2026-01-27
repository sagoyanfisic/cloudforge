import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway

os.makedirs("output", exist_ok=True)

with Diagram("Serverless API", show=False, filename="/app/diagrams/test_serverless", direction="LR"):
    api_gateway = APIGateway("API Gateway")
    with Cluster("Compute"):
        lambda_functions = Lambda("Lambda Functions")
    with Cluster("DynamoDB"):
        pass
    api_gateway >> lambda_functions