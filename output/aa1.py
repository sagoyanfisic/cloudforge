import os
from diagrams import Diagram
from diagrams.aws.network import ELB
from diagrams.aws.compute import Lambda
from diagrams.aws.storage import S3

# 1. Setup Output Directory
os.makedirs("output", exist_ok=True)

# 2. Initialize Diagram
with Diagram("Basic Cloud Services", show=False, filename="output/basic_cloud_services", direction="TB"):
    # 3. Define Global Nodes
    elb_lb = ELB("ELB load balancer")
    lambda_function = Lambda("Lambda functions")
    s3_bucket = S3("S3 storage")

    # 4. Define Clusters (if any in Blueprint)
    # No clusters defined in this blueprint

    # 5. Define Storage/DB
    # S3 is already defined as a global node

    # 6. Define Flows
    lambda_function >> s3_bucket