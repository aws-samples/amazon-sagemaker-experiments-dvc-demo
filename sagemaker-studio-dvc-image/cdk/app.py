#!/usr/bin/env python3

from aws_cdk import core

from sagemakerStudioCDK.sagemaker_studio_stack import SagemakerStudioStack
import os
import boto3

sts_client = boto3.client("sts")
account_id = os.environ.get('ACCOUNT_ID', sts_client.get_caller_identity()["Account"])
region = os.environ.get('REGION', 'eu-west-1')

domain_id = os.environ.get('DOMAIN_ID', None)

app = core.App()

if domain_id is None:
    print("Create a new studio domain")
else:
    print("Existing domain ID: {}".format(domain_id))

SagemakerStudioStack(app, "sagemakerStudioUserCDK", domain_id, env={"account": account_id, 'region': region})

app.synth()
