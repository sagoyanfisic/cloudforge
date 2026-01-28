import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.network import APIGateway
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.storage import S3

os.makedirs("output", exist_ok=True)

with Diagram("E-commerce Platform Microservices", show=False, filename="output/ecommerce_platform", direction="LR"):
    api_gateway = APIGateway("E-commerce API")

    with Cluster("Microservices"):
        product_catalog_svc = Lambda("Product Catalog Service")
        shopping_cart_svc = Lambda("Shopping Cart Service")
        checkout_svc = Lambda("Checkout Service")
        payment_svc = Lambda("Payment Service")
        order_mgmt_svc = Lambda("Order Management Service")
        user_auth_svc = Lambda("User Auth Service")

    with Cluster("Databases"):
        product_db = RDS("Product DB")
        cart_db = RDS("Cart DB")
        order_db = RDS("Order DB")
        user_db = RDS("User DB")

    with Cluster("Messaging & Notifications"):
        payment_queue = SQS("Payment Queue")
        order_queue = SQS("Order Processing Queue")
        notification_topic = SNS("Notifications Topic")

    product_images_s3 = S3("Product Images")

    api_gateway >> [product_catalog_svc, shopping_cart_svc, checkout_svc, user_auth_svc]

    product_catalog_svc >> product_db
    product_catalog_svc >> product_images_s3

    shopping_cart_svc >> cart_db

    user_auth_svc >> user_db

    checkout_svc >> cart_db
    checkout_svc >> payment_queue

    payment_queue >> payment_svc
    payment_svc >> order_queue

    order_queue >> order_mgmt_svc
    order_mgmt_svc >> order_db
    order_mgmt_svc >> notification_topic