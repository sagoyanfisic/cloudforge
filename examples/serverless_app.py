"""Example: Serverless Application Architecture"""

import os
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway
from diagrams.aws.integration import SQS
from diagrams.aws.storage import S3

# Ensure output directory exists
os.makedirs("examples", exist_ok=True)

with Diagram("Serverless Application", show=False, filename="examples/serverless_app", direction="TB"):
    # Entry point
    api_gateway = APIGateway("API Gateway")

    # Compute layer
    main_handler = Lambda("Main Handler")
    async_processor = Lambda("Async Processor")

    # Storage layer
    user_bucket = S3("User Files")
    database = Dynamodb("DynamoDB")

    # Queue
    job_queue = SQS("Job Queue")

    # Relationships
    api_gateway >> main_handler
    main_handler >> [database, user_bucket]
    main_handler >> job_queue
    job_queue >> async_processor
    async_processor >> database
