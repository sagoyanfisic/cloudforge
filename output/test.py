import os
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import Lambda

os.makedirs("output", exist_ok=True)

with Diagram("E-commerce Microservices Platform", show=False, filename="output/ecommerce_platform", direction="TB"):
    api_gateway = APIGateway("API Gateway")

    with Cluster("Cognito User Pool") as cognito_user_pool:
        pass

    with Cluster("Main VPC") as main_vpc:
        with Cluster("Public Subnet A") as public_subnet_a:
            with Cluster("NAT Gateway") as nat_gateway:
                pass

        with Cluster("Private Subnet A") as private_subnet_a:
            product_lambda = Lambda("Product Service")
            cart_lambda = Lambda("Cart Service")
            checkout_lambda = Lambda("Checkout Service")

            with Cluster("Product Catalog DynamoDB") as product_dynamodb:
                pass

            with Cluster("Product Cache ElastiCache") as product_cache:
                pass

            with Cluster("Shopping Cart ElastiCache") as cart_cache:
                pass

    api_gateway >> cognito_user_pool
    api_gateway >> product_lambda
    api_gateway >> cart_lambda
    api_gateway >> checkout_lambda

    product_lambda >> product_cache
    product_lambda >> product_dynamodb

    cart_lambda >> cart_cache

    checkout_lambda >> cart_cache
    checkout_lambda >> product_lambda