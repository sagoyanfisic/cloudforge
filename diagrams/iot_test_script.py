import os
from diagrams import Diagram, Cluster
from diagrams.aws.integration import Kinesis
from diagrams.aws.compute import Lambda
from diagrams.aws.storage import S3

os.makedirs("output", exist_ok=True)

with Diagram("IoT Data Pipeline", show=False, filename="/app/diagrams/iot_test", direction="LR"):
    kinesis_stream = Kinesis("KinesisDataStream")
    lambda_processor = Lambda("Lambda Processor")
    with Cluster("DynamoDB"):
        dynamodb_table = S3("DynamoDB Table")
    kinesis_stream >> lambda_processor
    lambda_processor >> dynamodb_table