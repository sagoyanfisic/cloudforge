"""Example: Microservices Architecture with ECS"""

import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import ECS
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.network import ALB, Route53

# Ensure output directory exists
os.makedirs("examples", exist_ok=True)

with Diagram("Microservices Architecture", show=False, filename="examples/microservices", direction="TB"):
    # DNS
    dns = Route53("Route53")

    # Load Balancer
    load_balancer = ALB("Application Load Balancer")

    with Cluster("Microservices"):
        with Cluster("Users Service"):
            user_service = ECS("User Service")

        with Cluster("Orders Service"):
            order_service = ECS("Order Service")

        with Cluster("Products Service"):
            product_service = ECS("Product Service")

    with Cluster("Data Layer"):
        # Cache
        cache = ElastiCache("Redis Cache")

        with Cluster("Databases"):
            user_db = RDS("Users DB")
            order_db = RDS("Orders DB")
            product_db = RDS("Products DB")

    # Relationships
    dns >> load_balancer
    load_balancer >> [user_service, order_service, product_service]

    # Services to Database
    user_service >> cache >> user_db
    order_service >> order_db
    product_service >> product_db

    # Inter-service communication
    order_service >> product_service
