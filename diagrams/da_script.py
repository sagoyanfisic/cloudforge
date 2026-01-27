import os
from diagrams import Diagram
from diagrams.aws.network import CloudFront, ALB

os.makedirs("output", exist_ok=True)

with Diagram("Web Application with CDN and Load Balancer", show=False, filename="/app/diagrams/da", direction="TB"):
    cdn = CloudFront("CloudFront Distribution")
    alb = ALB("Application Load Balancer")
    cdn >> alb