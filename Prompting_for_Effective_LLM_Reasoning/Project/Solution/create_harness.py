"""
Creates (or updates) the AgentCore managed harness using system_prompt.txt,
with the {{FAQ}} placeholder replaced by online_shop_faq.md, and the bug
report Gateway wired up as a tool.

Re-run this any time system_prompt.txt changes - it updates the existing
harness in place, no redeploy step needed.

    python create_harness.py
"""

import json
import time

import boto3

REGION = "us-east-1"
HARNESS_NAME = "bug_report_chatbot"  # letters/digits/underscores only, no hyphens
MODEL_ID = "us.amazon.nova-pro-v1:0"  # pinned per project requirements - do not use harness default


def load_config():
    with open("agentcore_config.json") as f:
        return json.load(f)


def build_system_prompt():
    with open("system_prompt.txt") as f:
        prompt = f.read()
    with open("online_shop_faq.md") as f:
        faq = f.read()
    if "{{FAQ}}" not in prompt:
        raise ValueError("system_prompt.txt is missing the {{FAQ}} placeholder")
    return prompt.replace("{{FAQ}}", faq)


def main():
    config = load_config()
    system_prompt = build_system_prompt()

    client = boto3.client("bedrock-agentcore-control", region_name=REGION)

    if "credential_provider_arn" not in config:
        raise SystemExit(
            "No credential_provider_arn in agentcore_config.json - "
            "run setup_harness_auth.py first."
        )

    tools = [
        {
            "type": "agentcore_gateway",
            "name": config["target_name"],  # "bugreports"
            "config": {
                "agentCoreGateway": {
                    "gatewayArn": (
                        f"arn:aws:bedrock-agentcore:{REGION}:"
                        f"{boto3.client('sts').get_caller_identity()['Account']}:"
                        f"gateway/{config['gateway_id']}"
                    ),
                    "outboundAuth": {
                        "oauth": {
                            "providerArn": config["credential_provider_arn"],
                            "scopes": [config["oauth_scope"]],
                            "grantType": "CLIENT_CREDENTIALS",
                        }
                    },
                }
            },
        }
    ]

    # Check if the harness already exists - if so, update it instead of
    # creating a duplicate.
    existing_arn = config.get("harness_arn")

    if existing_arn:
        print(f"Updating existing harness: {existing_arn}")
        harness_id = existing_arn.split("/")[-1]
        client.update_harness(
            harnessId=harness_id,
            systemPrompt=[{"text": system_prompt}],
            model={"bedrockModelConfig": {"modelId": MODEL_ID}},
            tools=tools,
        )
        harness_arn = existing_arn
    else:
        print(f"Creating harness: {HARNESS_NAME}")
        resp = client.create_harness(
            harnessName=HARNESS_NAME,
            executionRoleArn=config["harness_role_arn"],
            systemPrompt=[{"text": system_prompt}],
            model={"bedrockModelConfig": {"modelId": MODEL_ID}},
            tools=tools,
        )
        harness_arn = resp["harness"]["arn"]
        print(f"  Harness ARN: {harness_arn}")

    # Poll until READY
    print("  Waiting for harness to be ready...")
    while True:
        status = client.get_harness(harnessId=harness_arn.split("/")[-1])["harness"]["status"]
        print(f"    status: {status}")
        if status == "READY":
            break
        if status in ("CREATE_FAILED", "UPDATE_FAILED"):
            raise RuntimeError(f"Harness failed: {status}")
        time.sleep(5)

    config["harness_arn"] = harness_arn
    with open("agentcore_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Harness ready: {harness_arn}")
    print("Next: python chat.py")


if __name__ == "__main__":
    main()
