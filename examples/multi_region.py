"""Example: Multi-Region Deployment"""

import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda, EC2
from diagrams.aws.database import Dynamodb, RDS
from diagrams.aws.network import Route53, CloudFront

# Ensure output directory exists
os.makedirs("examples", exist_ok=True)

with Diagram("Multi-Region Application", show=False, filename="examples/multi_region", direction="TB"):
    # Global services
    dns = Route53("Global DNS")
    cdn = CloudFront("CloudFront CDN")

    with Cluster("US-EAST-1"):
        with Cluster("Compute"):
            us_lambda = Lambda("Lambda")
            us_ec2 = EC2("EC2 Instances")

        with Cluster("Storage"):
            us_db = Dynamodb("DynamoDB")
            us_rds = RDS("RDS Primary")

    with Cluster("EU-WEST-1"):
        with Cluster("Compute"):
            eu_lambda = Lambda("Lambda")
            eu_ec2 = EC2("EC2 Instances")

        with Cluster("Storage"):
            eu_db = Dynamodb("DynamoDB")
            eu_rds = RDS("RDS Replica")

    # Global routing
    dns >> [cdn, us_lambda, eu_lambda]

    # Regional relationships
    us_lambda >> us_ec2
    us_ec2 >> us_db
    us_rds >> eu_rds

    eu_lambda >> eu_ec2
    eu_ec2 >> eu_db

    # Cross-region replication
    us_db >> eu_db
