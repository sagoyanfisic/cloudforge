import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.network import ALB

os.makedirs("output", exist_ok=True)

COLOR_PROD = "#E74C3C"
COLOR_NETWORK = "#3498DB"
COLOR_COMPUTE = "#F39C12"
COLOR_DATABASE = "#27AE60"

with Diagram("Production SaaS Platform", show=False, filename="/app/diagrams/saas_final", direction="TB", graph_attr={"bgcolor": f"{COLOR_PROD}10"}):
    with Cluster("Network", graph_attr={"bgcolor": f"{COLOR_NETWORK}10"}):
        alb_lb = ALB("ALB Load Balancer")

    with Cluster("Compute", graph_attr={"bgcolor": f"{COLOR_COMPUTE}10"}):
        lambda_microservices = Lambda("Lambda Microservices")

    with Cluster("Database", graph_attr={"bgcolor": f"{COLOR_DATABASE}10"}):
        rds_postgresql = RDS("RDS PostgreSQL Database")

    alb_lb >> Edge(label="forwards") >> lambda_microservices
    lambda_microservices >> Edge(label="reads_writes") >> rds_postgresql