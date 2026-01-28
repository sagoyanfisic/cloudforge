import os
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway

os.makedirs("output", exist_ok=True)

with Diagram("Serverless REST API", show=False, filename="/app/diagrams/a1", direction="LR"):
    api_gateway = APIGateway("API Gateway")
    lambda_function = Lambda("Lambda Function")
    api_gateway >> lambda_function