"""
Deletes the harness, gateway target, gateway, and OAuth2 credential
provider created for this project. Does NOT touch the CloudFormation
stacks (bug-report-tool-stack, bug-report-testing-stack) - delete those
separately.

Also does NOT delete the Cognito User Pool created by setup_gateway.py's
EZ Auth flow, or the Secrets Manager secret auto-created by the OAuth2
credential provider - check the console manually for those after running
this script.

    python cleanup_agentcore.py
"""

import json

import boto3

REGION = "us-east-1"
PROVIDER_NAME = "bug-report-harness-auth"  # must match setup_harness_auth.py


def main():
    with open("agentcore_config.json") as f:
        config = json.load(f)

    client = boto3.client("bedrock-agentcore-control", region_name=REGION)

    # 1. Delete the harness first (it depends on the gateway/tools)
    harness_arn = config.get("harness_arn")
    if harness_arn:
        harness_id = harness_arn.split("/")[-1]
        print(f"Deleting harness: {harness_id}")
        try:
            client.delete_harness(harnessId=harness_id, deleteManagedMemory=True)
            print("  Deleted.")
        except Exception as e:
            print(f"  Failed (may already be deleted): {e}")
    else:
        print("No harness_arn in config, skipping.")

    # 2. Delete the gateway target before the gateway itself
    gateway_id = config.get("gateway_id")
    target_id = config.get("target_id")
    if gateway_id and target_id:
        print(f"Deleting gateway target: {target_id}")
        try:
            client.delete_gateway_target(gatewayIdentifier=gateway_id, targetId=target_id)
            print("  Deleted.")
        except Exception as e:
            print(f"  Failed (may already be deleted): {e}")
    else:
        print("No gateway_id/target_id in config, skipping target deletion.")

    # 3. Delete the gateway
    if gateway_id:
        print(f"Deleting gateway: {gateway_id}")
        try:
            client.delete_gateway(gatewayIdentifier=gateway_id)
            print("  Deleted.")
        except Exception as e:
            print(f"  Failed (may already be deleted): {e}")
    else:
        print("No gateway_id in config, skipping.")

    # 4. Delete the OAuth2 credential provider
    print(f"Deleting OAuth2 credential provider: {PROVIDER_NAME}")
    try:
        client.delete_oauth2_credential_provider(name=PROVIDER_NAME)
        print("  Deleted.")
    except Exception as e:
        print(f"  Failed (may already be deleted): {e}")

    print("\nDone. Still need to check/delete manually:")
    print(f"  - Cognito User Pool: {config.get('client_info', {}).get('user_pool_id', '(unknown)')}")
    print("  - Secrets Manager secret under bedrock-agentcore-identity!default/oauth2/*")
    print("  - CloudFormation stacks: bug-report-tool-stack, bug-report-testing-stack (not touched by this script)")


if __name__ == "__main__":
    main()
