import os
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import Lambda

os.makedirs("output", exist_ok=True)

with Diagram("Web API with Lambda and DynamoDB", show=False, filename="/app/diagrams/web_api_final_test", direction="LR"):
    api_gateway = APIGateway("API Gateway")
    lambda_function = Lambda("Lambda Function")
    with Cluster("DynamoDB Table"):
        pass
    api_gateway >> lambda_function
    lambda_function >> Cluster("DynamoDB Table")