import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.cost import *
from diagrams.aws.ar import *
from diagrams.aws.general import *
from diagrams.aws.database import *
from diagrams.aws.management import *
from diagrams.aws.ml import *
from diagrams.aws.game import *
from diagrams.aws.enablement import *
from diagrams.aws.network import *
from diagrams.aws.quantum import *
from diagrams.aws.iot import *
from diagrams.aws.robotics import *
from diagrams.aws.migration import *
from diagrams.aws.mobile import *
from diagrams.aws.compute import *
from diagrams.aws.media import *
from diagrams.aws.engagement import *
from diagrams.aws.security import *
from diagrams.aws.devtools import *
from diagrams.aws.integration import *
from diagrams.aws.business import *
from diagrams.aws.analytics import *
from diagrams.aws.blockchain import *
from diagrams.aws.storage import *
from diagrams.aws.satellite import *
from diagrams.aws.enduser import *
from diagrams.onprem.vcs import *
from diagrams.onprem.database import *
from diagrams.onprem.gitops import *
from diagrams.onprem.workflow import *
from diagrams.onprem.etl import *
from diagrams.onprem.inmemory import *
from diagrams.onprem.identity import *
from diagrams.onprem.network import *
from diagrams.onprem.cd import *
from diagrams.onprem.container import *
from diagrams.onprem.certificates import *
from diagrams.onprem.mlops import *
from diagrams.onprem.dns import *
from diagrams.onprem.compute import *
from diagrams.onprem.logging import *
from diagrams.onprem.registry import *
from diagrams.onprem.security import *
from diagrams.onprem.client import *
from diagrams.onprem.groupware import *
from diagrams.onprem.iac import *
from diagrams.onprem.analytics import *
from diagrams.onprem.messaging import *
from diagrams.onprem.tracing import *
from diagrams.onprem.ci import *
from diagrams.onprem.search import *
from diagrams.onprem.storage import *
from diagrams.onprem.auth import *
from diagrams.onprem.monitoring import *
from diagrams.onprem.aggregator import *
from diagrams.onprem.queue import *
from diagrams.k8s.others import *
from diagrams.k8s.rbac import *
from diagrams.k8s.network import *
from diagrams.k8s.ecosystem import *
from diagrams.k8s.compute import *
from diagrams.k8s.chaos import *
from diagrams.k8s.infra import *
from diagrams.k8s.podconfig import *
from diagrams.k8s.controlplane import *
from diagrams.k8s.clusterconfig import *
from diagrams.k8s.storage import *
from diagrams.k8s.group import *
from diagrams.generic.database import *
from diagrams.generic.blank import *
from diagrams.generic.network import *
from diagrams.generic.virtualization import *
from diagrams.generic.place import *
from diagrams.generic.device import *
from diagrams.generic.compute import *
from diagrams.generic.os import *
from diagrams.generic.storage import *
from diagrams.saas.crm import *
from diagrams.saas.identity import *
from diagrams.saas.chat import *
from diagrams.saas.recommendation import *
from diagrams.saas.cdn import *
from diagrams.saas.communication import *
from diagrams.saas.media import *
from diagrams.saas.logging import *
from diagrams.saas.security import *
from diagrams.saas.social import *
from diagrams.saas.alerting import *
from diagrams.saas.analytics import *
from diagrams.saas.automation import *
from diagrams.saas.filesharing import *

with Diagram("Production-Grade E-commerce Monolith", show=False, filename='/app/diagrams/my_architecture', direction="TB", graph_attr={"bgcolor": "#E74C3C10"}):

    # ── External services (outside VPC) ──────────────────────────────────────
    route53 = Route53("Route 53")
    cloudfront = CloudFront("CloudFront CDN")
    s3_frontend = S3("S3 Frontend Bucket")

    # ── Core Services (defined at top level for connections) ─────────────────
    waf = WAF("AWS WAF")
    alb = ALB("Application Load Balancer")
    ec2_monolith = EC2("EC2 Monolith Instances")
    ec2_asg = AutoScalingGroup("EC2 Auto Scaling Group")
    ebs_volumes = EBS("EBS Volumes")
    rds_postgres = RDS("RDS PostgreSQL Multi-AZ")
    elasticache_redis = ElastiCache("ElastiCache for Redis")
    s3_media = S3("S3 Media Bucket")
    dynamodb = DynamodbTable("DynamoDB") # Corrected: DynamodbTable
    opensearch = AmazonOpensearchService("OpenSearch Service") # Corrected: AmazonOpensearchService
    sqs_orders = SQS("SQS Order Processing Queue")
    sqs_notifications = SQS("SQS Notification Queue")
    sns_order_alerts = SNS("SNS Order Alerts Topic")
    sns_customer_updates = SNS("SNS Customer Updates Topic")
    eventbridge = EventBridge("EventBridge")
    cognito_user_pool = Cognito("Cognito User Pool")
    secrets_manager = SecretsManager("Secrets Manager")
    kms = KMS("KMS")
    iam_ec2_role = IAM("IAM Role for EC2")
    guardduty = GuardDuty("GuardDuty")
    shield_advanced = Shield("Shield Advanced")
    cloudwatch = Cloudwatch("CloudWatch") # Corrected: Cloudwatch
    xray = XRay("X-Ray") # Corrected: XRay
    cloudwatch_logs = CloudwatchLogs("CloudWatch Logs") # Corrected: CloudwatchLogs
    nat_gateway = NATGateway("NAT Gateway")
    vpc_endpoint_s3 = VPCEndpoint("VPC Endpoint for S3")
    vpc_endpoint_dynamodb = VPCEndpoint("VPC Endpoint for DynamoDB")
    vpc_endpoint_secrets = VPCEndpoint("VPC Endpoint for Secrets Manager")

    # ── Logical Groupings ────────────────────────────────────────────────────
    with Cluster("VPC: us-east-1", graph_attr={"bgcolor": "#EBF5FB10"}):
        with Cluster("Public Subnet", graph_attr={"bgcolor": "#D5E8D410"}):
            alb
            nat_gateway
        with Cluster("Private Subnet", graph_attr={"bgcolor": "#DAE8FC10"}):
            ec2_monolith
            rds_postgres
            elasticache_redis
            opensearch
            vpc_endpoint_s3
            vpc_endpoint_dynamodb
            vpc_endpoint_secrets

    with Cluster("Monitoring", graph_attr={"bgcolor": "#95A5A610"}):
        cloudwatch
        xray
        cloudwatch_logs

    with Cluster("Security & Identity", graph_attr={"bgcolor": "#C0392B10"}):
        waf
        cognito_user_pool
        secrets_manager
        kms
        iam_ec2_role
        guardduty
        shield_advanced

    with Cluster("Integration & Events", graph_attr={"bgcolor": "#F5F5F510"}):
        sqs_orders
        sqs_notifications
        sns_order_alerts
        sns_customer_updates
        eventbridge

    with Cluster("Storage & Search", graph_attr={"bgcolor": "#F5F5F510"}):
        s3_frontend
        s3_media
        dynamodb
        opensearch

    # ── Connections ──────────────────────────────────────────────────────────
    route53 >> Edge(label="forwards") >> cloudfront
    cloudfront >> Edge(label="forwards") >> waf
    waf >> Edge(label="forwards") >> alb
    cloudfront >> Edge(label="pulls") >> s3_frontend
    cloudfront >> Edge(label="forwards") >> alb
    alb >> Edge(label="forwards") >> ec2_monolith
    ec2_asg >> Edge(label="manages") >> ec2_monolith
    ec2_monolith >> Edge(label="reads_writes") >> ebs_volumes
    ec2_monolith >> Edge(label="reads_writes") >> rds_postgres
    ec2_monolith >> Edge(label="reads_writes") >> elasticache_redis
    ec2_monolith >> Edge(label="reads_writes") >> s3_media
    ec2_monolith >> Edge(label="reads_writes") >> dynamodb
    ec2_monolith >> Edge(label="reads_writes") >> opensearch
    ec2_monolith >> Edge(label="triggers") >> sqs_orders
    ec2_monolith >> Edge(label="triggers") >> sqs_notifications
    ec2_monolith >> Edge(label="triggers") >> sns_order_alerts
    ec2_monolith >> Edge(label="triggers") >> sns_customer_updates
    ec2_monolith >> Edge(label="triggers") >> eventbridge
    cognito_user_pool >> Edge(label="manages") >> ec2_monolith
    ec2_monolith >> Edge(label="pulls") >> secrets_manager
    ec2_monolith >> Edge(label="manages") >> kms
    ec2_monolith >> Edge(label="manages") >> iam_ec2_role
    ec2_monolith >> Edge(label="monitors") >> cloudwatch
    ec2_monolith >> Edge(label="monitors") >> xray
    ec2_monolith >> Edge(label="monitors") >> cloudwatch_logs
    alb >> Edge(label="monitors") >> cloudwatch
    rds_postgres >> Edge(label="monitors") >> cloudwatch
    elasticache_redis >> Edge(label="monitors") >> cloudwatch
    opensearch >> Edge(label="monitors") >> cloudwatch
    ec2_monolith >> Edge(label="forwards") >> vpc_endpoint_s3
    ec2_monolith >> Edge(label="forwards") >> vpc_endpoint_dynamodb
    ec2_monolith >> Edge(label="forwards") >> vpc_endpoint_secrets
    ec2_monolith >> Edge(label="forwards") >> nat_gateway