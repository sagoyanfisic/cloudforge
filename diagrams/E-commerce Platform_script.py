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

with Diagram("Serverless E-commerce Platform", show=False, filename='/app/diagrams/E-commerce Platform', direction="TB", graph_attr={"bgcolor": "#E74C3C10"}):

    # ── External services (outside VPC) ──────────────────────────────────────
    route53 = Route53("Route53")
    cloudfront = CloudFront("CloudFront CDN")
    s3_static_assets = S3("S3 Static Assets")
    cognito_user_pool = Cognito("Cognito User Pool")

    # ── Core Services ────────────────────────────────────────────────────────
    waf = WAF("AWS WAF")
    alb = ALB("ALB")
    ecs_cluster = ECS("ECS Cluster")
    ecs_service_app = ECS("ECS Service (App)")
    fargate_task_app = Rack("Fargate Task (App)") # ECS Fargate is not a direct symbol
    rds_postgresql = RDS("RDS PostgreSQL (Multi-AZ)")
    elasticache_redis = ElastiCache("ElastiCache Redis")
    dynamodb_sessions = DynamodbTable("DynamoDB Sessions")
    nat_gateway = NATGateway("NAT Gateway")
    vpc_endpoint_s3 = VPCEndpoint("VPC Endpoint (S3)")
    vpc_endpoint_dynamodb = VPCEndpoint("VPC Endpoint (DynamoDB)")
    opensearch_domain = AmazonOpensearchService("OpenSearch Domain")

    # ── Integration & Events ─────────────────────────────────────────────────
    sqs_order_queue = SQS("SQS Order Queue")
    sns_order_events = SNS("SNS Order Events Topic")
    eventbridge_bus = EventBridge("EventBridge Bus")

    # ── Monitoring ───────────────────────────────────────────────────────────
    cloudwatch_metrics_logs = Cloudwatch("CloudWatch Metrics & Logs")
    xray_tracer = XRay("X-Ray Tracer")

    # ── Security & Identity ──────────────────────────────────────────────────
    secrets_manager = SecretsManager("Secrets Manager")
    kms_key = KMS("KMS Key")
    guardduty = GuardDuty("GuardDuty")
    iam_roles = IAM("IAM Roles")

    # ── Logical Groupings ────────────────────────────────────────────────────
    with Cluster("VPC: us-east-1", graph_attr={"bgcolor": "#EBF5FB10"}):
        with Cluster("Public Subnet", graph_attr={"bgcolor": "#D5E8D410"}):
            alb
            nat_gateway

        with Cluster("Private Subnet", graph_attr={"bgcolor": "#DAE8FC10"}):
            ecs_cluster
            ecs_service_app
            fargate_task_app
            rds_postgresql
            elasticache_redis
            vpc_endpoint_s3
            vpc_endpoint_dynamodb
            opensearch_domain

    with Cluster("Monitoring", graph_attr={"bgcolor": "#95A5A610"}):
        cloudwatch_metrics_logs
        xray_tracer

    with Cluster("Security & Identity", graph_attr={"bgcolor": "#C0392B10"}):
        waf
        cognito_user_pool
        secrets_manager
        kms_key
        guardduty
        iam_roles

    with Cluster("Integration & Events", graph_attr={"bgcolor": "#F39C1210"}):
        sqs_order_queue
        sns_order_events
        eventbridge_bus

    with Cluster("Storage & Search", graph_attr={"bgcolor": "#3498DB10"}):
        s3_static_assets
        dynamodb_sessions
        opensearch_domain

    # ── Connections ──────────────────────────────────────────────────────────
    route53 >> Edge(label="forwards") >> cloudfront
    cloudfront >> Edge(label="forwards") >> waf
    waf >> Edge(label="forwards") >> alb
    alb >> Edge(label="forwards") >> ecs_service_app
    ecs_service_app >> Edge(label="manages") >> fargate_task_app
    ecs_service_app >> Edge(label="reads_writes") >> rds_postgresql
    ecs_service_app >> Edge(label="reads_writes") >> elasticache_redis
    ecs_service_app >> Edge(label="reads_writes") >> dynamodb_sessions
    ecs_service_app >> Edge(label="triggers") >> sqs_order_queue
    ecs_service_app >> Edge(label="triggers") >> sns_order_events
    ecs_service_app >> Edge(label="reads_writes") >> opensearch_domain
    ecs_service_app >> Edge(label="pulls") >> secrets_manager
    ecs_service_app >> Edge(label="monitors") >> cloudwatch_metrics_logs
    ecs_service_app >> Edge(label="monitors") >> xray_tracer
    cognito_user_pool >> Edge(label="triggers") >> ecs_service_app
    eventbridge_bus >> Edge(label="triggers") >> sns_order_events
    s3_static_assets >> Edge(label="pulls") >> cloudfront
    kms_key >> Edge(label="manages") >> rds_postgresql
    kms_key >> Edge(label="manages") >> secrets_manager
    guardduty >> Edge(label="monitors") >> cloudwatch_metrics_logs
    iam_roles >> Edge(label="manages") >> ecs_service_app