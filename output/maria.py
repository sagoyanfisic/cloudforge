import os
from diagrams import Diagram
from diagrams.aws.network import ELB
from diagrams.aws.compute import Lambda
from diagrams.aws.storage import S3

# 1. Setup Output Directory
os.makedirs("output", exist_ok=True)

# 2. Initialize Diagram
with Diagram("Basic AWS Services", show=False, filename="output/basic_aws_services", direction="TB"):
    # 3. Define Global Nodes
    elb_lb = ELB("ELB load balancer")
    lambda_funcs = Lambda("Lambda functions")
    s3_bucket = S3("S3 storage")