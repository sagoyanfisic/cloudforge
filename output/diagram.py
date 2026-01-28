import os
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.queue import SQS

os.makedirs("output", exist_ok=True)

with Diagram("E-commerce Microservices Platform", show=False, filename="output/ecommerce_platform", direction="TB"):
    # Define all visual nodes and clusters first
    api_gateway = APIGateway("API Gateway")
    product_lambda = Lambda("Product Service")
    cart_lambda = Lambda("Shopping Cart Service")
    checkout_lambda = Lambda("Checkout Service")
    payment_lambda = Lambda("Payment Service")
    order_lambda = Lambda("Order Service")
    order_payment_rds = RDS("Order & Payment DB")
    order_sqs_queue = SQS("Order S")