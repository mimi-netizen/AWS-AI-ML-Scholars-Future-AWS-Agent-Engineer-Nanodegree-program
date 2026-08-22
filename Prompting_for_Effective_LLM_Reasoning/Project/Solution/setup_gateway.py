"""
Creates the AgentCore Gateway and registers the create-bug-report Lambda
as a tool target named 'bugreports'. Reads everything it needs from the
bug-report-tool-stack CloudFormation outputs - no copy-pasting required.

Run this once, after deploying cloudformation-tool.yaml:
    python setup_gateway.py

Saves gateway id, gateway URL, target id, and auth info to
agentcore_config.json for use by create_harness.py and chat.py.
"""

import json
import time

import boto3
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient

STACK_NAME = "bug-report-tool-stack"
REGION = "us-east-1"
GATEWAY_NAME = "bug-report-gateway"
TARGET_NAME = "bugreports"  # becomes the tool name prefix: bugreports___create_bug_report

# Tool schema the Gateway exposes to the model. Field names/requirements
# must match what the Lambda (index.py) expects and enforces.
TOOL_SCHEMA = [
    {
        "name": "create_bug_report",
        "description": (
            "Creates a support ticket for a bug reported by a customer. "
            "All three fields are required - do not call this tool until "
            "you have collected description, stepsToReproduce, and "
            "environment from the customer."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the bug, in the customer's words",
                },
                "stepsToReproduce": {
                    "type": "string",
                    "description": "Steps to follow to reproduce the issue",
                },
                "environment": {
                    "type": "string",
                    "description": "Customer's environment (browser, OS, device)",
                },
            },
            "required": ["description", "stepsToReproduce", "environment"],
        },
    }
]


def get_stack_outputs(cfn_client, stack_name):
    resp = cfn_client.describe_stacks(StackName=stack_name)
    outputs = resp["Stacks"][0]["Outputs"]
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


def main():
    print(f"Reading outputs from stack: {STACK_NAME}")
    cfn = boto3.client("cloudformation", region_name=REGION)
    outputs = get_stack_outputs(cfn, STACK_NAME)

    lambda_arn = outputs["LambdaFunctionArn"]
    gateway_role_arn = outputs["GatewayRoleArn"]
    print(f"  Lambda ARN: {lambda_arn}")
    print(f"  Gateway role ARN: {gateway_role_arn}")

    client = GatewayClient(region_name=REGION)

    print("\nCreating Cognito OAuth authorizer...")
    cognito_response = client.create_oauth_authorizer_with_cognito(GATEWAY_NAME)

    print("Creating gateway...")
    gateway = client.create_mcp_gateway(
        name=GATEWAY_NAME,
        role_arn=gateway_role_arn,
        authorizer_config=cognito_response["authorizer_config"],
    )
    gateway_id = gateway["gatewayId"]
    gateway_url = gateway.get("gatewayUrl")
    print(f"  Gateway ID: {gateway_id}")
    print(f"  Gateway URL: {gateway_url}")

    print(f"\nRegistering Lambda as tool target '{TARGET_NAME}'...")
    target = client.create_mcp_gateway_target(
        gateway=gateway,
        target_type="lambda",
        name=TARGET_NAME,
        target_payload={
            "lambdaArn": lambda_arn,
            "toolSchema": {"inlinePayload": TOOL_SCHEMA},
        },
    )
    target_id = target.get("targetId")
    print(f"  Target ID: {target_id}")
    print(f"  Tool will appear to the model as: {TARGET_NAME}___create_bug_report")

    config = {
        "region": REGION,
        "gateway_id": gateway_id,
        "gateway_url": gateway_url,
        "gateway_role_arn": gateway_role_arn,
        "target_id": target_id,
        "target_name": TARGET_NAME,
        "client_info": cognito_response.get("client_info"),
        "harness_role_arn": outputs["HarnessRoleArn"],
        "lambda_arn": lambda_arn,
    }
    with open("agentcore_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\nSaved config to agentcore_config.json")
    print("Next: write system_prompt.txt, then run create_harness.py")


if __name__ == "__main__":
    main()
