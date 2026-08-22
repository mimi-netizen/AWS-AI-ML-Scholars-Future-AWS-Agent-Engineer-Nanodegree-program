#!/usr/bin/env python3
"""
Runs the AgentCore harness against a test suite and emits a JSONL file
for Bedrock Evaluations (LLM-as-a-judge, Bring Your Own Inference).

Usage:
    python generate-eval-dataset.py \
        --tests-json harness-tests.json \
        --harness-arn <harness-arn> \
        --region us-east-1
"""

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

import boto3


def invoke_harness_once(client, harness_arn: str, prompt: str) -> str:
    """
    Invokes the harness with a single user message in a fresh session
    and returns the concatenated assistant text response.
    """
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    response = client.invoke_harness(
        harnessArn=harness_arn,
        runtimeSessionId=session_id,
        runtimeUserId=user_id,
        messages=messages,
    )

    assistant_text = ""
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                assistant_text += delta["text"]

    return assistant_text


def main():
    p = argparse.ArgumentParser(
        description="Run AgentCore harness tests and emit Bedrock Evaluations JSONL (LLM-as-judge BYOI)."
    )
    p.add_argument("--tests-json", required=True, help="Path to the test suite JSON (harness-tests.json).")
    p.add_argument("--harness-arn", required=True, help="AgentCore harness ARN.")
    p.add_argument("--model-identifier", default="bug-report-chatbot", help="Value to put in modelResponses[0].modelIdentifier.")
    p.add_argument("--out-jsonl", default="output_eval_dataset.jsonl", help="Where to write the eval dataset JSONL.")
    p.add_argument("--region", default="us-east-1", help="AWS region.")
    args = p.parse_args()

    suite = json.loads(Path(args.tests_json).read_text(encoding="utf-8"))
    tests = suite["tests"]

    session = boto3.Session(region_name=args.region)
    client = session.client("bedrock-agentcore")

    out_path = Path(args.out_jsonl)
    n_ok = 0

    with out_path.open("w", encoding="utf-8") as f:
        for t in tests:
            test_id = t["id"]
            prompt = t.get("prompt", "")
            reference = t.get("expected", "")

            try:
                response_text = invoke_harness_once(client, args.harness_arn, prompt)
                n_ok += 1
            except Exception as e:
                # If the harness errors, still emit a record so the eval run captures failures
                print(f"{test_id}: {e}", file=sys.stderr)
                response_text = f"[HARNESS_ERROR] {type(e).__name__}: {e}"

            record: Dict[str, Any] = {
                "prompt": prompt,
                "referenceResponse": reference,
                "modelResponses": [
                    {
                        "response": response_text,
                        "modelIdentifier": args.model_identifier,
                    }
                ],
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"{test_id}: wrote eval line", file=sys.stderr)

    print(f"\nWrote {len(tests)} JSONL lines to {out_path} ({n_ok} harness calls succeeded).", file=sys.stderr)


if __name__ == "__main__":
    main()
