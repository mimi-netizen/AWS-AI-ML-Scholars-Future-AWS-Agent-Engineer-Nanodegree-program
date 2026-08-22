"""
Creates an AgentCore Identity OAuth2 credential provider wrapping the
Cognito app client that setup_gateway.py already created. The harness
needs this so it can present a valid bearer token when it calls the
Gateway's MCP endpoint (the Gateway requires Cognito JWT auth).

Run this once, after setup_gateway.py and before create_harness.py:
    python setup_harness_auth.py

Saves credential_provider_arn to agentcore_config.json.
"""

import json

import boto3

REGION = "us-east-1"
PROVIDER_NAME = "bug-report-harness-auth"


def main():
    with open("agentcore_config.json") as f:
        config = json.load(f)

    client_info = config["client_info"]
    account_id = boto3.client("sts").get_caller_identity()["Account"]

    discovery_url = (
        f"https://cognito-idp.{REGION}.amazonaws.com/"
        f"{client_info['user_pool_id']}/.well-known/openid-configuration"
    )

    client = boto3.client("bedrock-agentcore-control", region_name=REGION)

    print(f"Creating OAuth2 credential provider: {PROVIDER_NAME}")
    print(f"  Discovery URL: {discovery_url}")

    resp = client.create_oauth2_credential_provider(
        name=PROVIDER_NAME,
        credentialProviderVendor="CustomOauth2",  # lowercase 'a' - confirmed API enum
        oauth2ProviderConfigInput={
            "customOauth2ProviderConfig": {
                "oauthDiscovery": {"discoveryUrl": discovery_url},
                "clientId": client_info["client_id"],
                "clientSecret": client_info["client_secret"],
            }
        },
    )

    provider_arn = resp["credentialProviderArn"]
    print(f"  Provider ARN: {provider_arn}")

    config["credential_provider_arn"] = provider_arn
    config["oauth_scope"] = client_info["scope"]
    with open("agentcore_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\nSaved credential_provider_arn to agentcore_config.json")
    print("Next: re-run create_harness.py to wire it into the tool config")


if __name__ == "__main__":
    main()
