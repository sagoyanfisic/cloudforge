import os
from diagrams import Diagram, Node
from diagrams.aws.network import ALB

os.makedirs("output", exist_ok=True)

with Diagram("CDN Fronted Web Application", show=False, filename="/app/diagrams/web_app", direction="TB"):
    cloudfront_dist = Node("CloudFront Distribution")
    alb = ALB("Application Load Balancer")
    cloudfront_dist >> alb