# Solution: Customer Support Chatbot with Amazon Bedrock Flows

## Status
- [ ] Step 0: Environment set up (AWS CLI, credentials, Python deps)
- [ ] Step 1: Tool deployed and tested
- [ ] Step 2: Bedrock Flow built (classification + 3 paths)
- [ ] Step 3: Testing and Evaluation complete

---

## Step 0: Environment Setup

### 0.1 AWS CLI installed and version confirmed

```bash
aws --version
```

Output: `<paste here>`

If not installed: `<document install method used — e.g. package manager, installer link>`

### 0.2 AWS credentials configured

Method used (check one):
- [ ] `aws configure` (access key / secret key)
- [ ] Vocareum lab-provided credentials (session token required — note expiry)
- [ ] Named profile: `<profile name>`
- [ ] Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)

Verify identity:
```bash
aws sts get-caller-identity
```

Output: `<paste — confirms account ID / role, without exposing actual key values>`

**Note:** if using a Vocareum-style lab account, session tokens expire — document how long the session lasts and the refresh step, since a mid-project expiry will silently break `aws cloudformation deploy` calls with a credentials error that looks unrelated to the actual template.

### 0.3 Region set

```bash
aws configure get region
```

Confirm it prints `us-east-1`, or pass `--region us-east-1` explicitly on every command (the walkthrough commands below all do this).

### 0.4 Bedrock model access enabled

In the Bedrock console → Model access → confirm Amazon Nova Pro (and any other model used) shows "Access granted" for `us-east-1`. This is a manual console step, not CLI — request access before Step 1 if not already granted, since approval isn't always instant.

![Bedrock model access confirmation](screenshots/00-model-access.png)

### 0.5 Python environment and dependencies

```bash
python3 --version
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify boto3:
```bash
python -c "import boto3; print(boto3.__version__)"
```

Output: `<paste version — should match requirements.txt (1.42.54)>`

### 0.6 Project files present

Confirm these exist in the project root before continuing:
- [ ] `cloudformation-tool.yaml`
- [ ] `cloudformation-testing.yaml`
- [ ] `create_bug_report.py`
- [ ] `generate-eval-dataset.py`
- [ ] `flow-tests-template.json`
- [ ] `online_shop_faq.md`
- [ ] `requirements.txt`

### Notes / issues encountered
- _(e.g. credential expiry, missing model access, venv activation issues on Windows vs WSL)_

---

## Step 1: Tool Deployment (DynamoDB + Lambda)

### 1.1 Deploy `cloudformation-tool.yaml`

Command run:
```bash
aws cloudformation deploy \
    --template-file cloudformation-tool.yaml \
    --stack-name bug-report-tool-stack \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

**Result:** _(paste stack outputs / confirm "Successfully created/updated stack")_

Stack outputs (`BugReportsTableArn`, `LambdaFunctionArn`, `LambdaExecutionRoleArn`):
```
<paste here>
```

![Stack creation success](screenshots/01-stack-created.png)

### 1.2 Test Lambda function in isolation

Test event used: sample JSON from Project-Instructions.md (checkout crash example).

![Lambda test event configuration](screenshots/02-lambda-test-event.png)

![Lambda test result](screenshots/03-lambda-test-result.png)

Ticket ID returned: `<paste here>`

### 1.3 Verify DynamoDB record

![DynamoDB BugReports table item](screenshots/04-dynamodb-record.png)

### Notes / issues encountered
- _(e.g. AccessDeniedException, ResourceNotFoundException, region mismatches)_

---

## Step 2: Bedrock Flow

### 2.1 Classification design

Labels used: `<e.g. BUG_REPORT | PLATFORM_QUESTION | OTHER>`

Classifier prompt:
```
<paste final classifier prompt text here>
```

Rationale for label choice / prompt structure:
- _(why these exact strings, how you enforce exact-match output)_

![Full flow diagram](screenshots/05-flow-diagram.png)

![Classifier prompt node configuration](screenshots/06-classifier-config.png)

![Condition node expressions](screenshots/07-condition-node.png)

### 2.2 Bug Report path (Agent node)

Action group / Lambda linkage:

![Agent node configuration showing action group](screenshots/08-agent-config.png)

Data collected: description, stepsToReproduce, environment
- "User input" advanced setting enabled: Yes/No

Test — clear bug report (single turn):

![Flow test - clear bug report](screenshots/09-test-bug-clear.png)

Test — vague bug report requiring follow-up questions:

![Flow test - bug report with follow-up](screenshots/10-test-bug-followup.png)

DynamoDB record created via the Flow (not the isolated Lambda test):

![DynamoDB record from Flow test](screenshots/11-dynamodb-flow-record.png)

### 2.3 Platform Question path

FAQ embedding approach:

![FAQ prompt node template](screenshots/12-faq-prompt-node.png)

Test — question covered by FAQ:

![Flow test - covered FAQ question](screenshots/13-test-faq-covered.png)

Test — question NOT covered by FAQ (should redirect to phone support):

![Flow test - uncovered FAQ question](screenshots/14-test-faq-uncovered.png)

### 2.4 Other Requests path

Test — generic/unrelated request:

![Flow test - other request](screenshots/15-test-other.png)

### Notes / issues encountered
- _(misrouting cases, prompt iterations, output node wiring gotchas)_

---

## Step 3: Testing and Evaluation

### 3.1 Test suite

`flow-tests.json` — see file in submission. Covers:
- [ ] At least 1 bug report test
- [ ] At least 1 platform question test
- [ ] At least 1 other-request test
- [ ] Stand-out: ambiguous message
- [ ] Stand-out: very short message
- [ ] Stand-out: prompt injection attempt

### 3.2 Flow alias

Flow ID: `<paste>`
Alias ID: `<paste>` (name: `v1`)

### 3.3 Run generate-eval-dataset.py

```bash
python generate-eval-dataset.py \
  --tests-json flow-tests.json \
  --flow-id <flow-id> \
  --flow-alias-id <alias-id> \
  --region us-east-1
```

Output: `output_eval_dataset.jsonl` — see file in submission.

### 3.4 Deploy evaluation resources

```bash
aws cloudformation deploy \
  --template-file cloudformation-testing.yaml \
  --stack-name bug-report-testing-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Outputs: `EvalDatasetBucketName`, `BedrockEvalRoleArn`
```
<paste here>
```

### 3.5 Upload dataset and create evaluation job

```bash
aws s3 cp output_eval_dataset.jsonl s3://<bucket-name>/output_eval_dataset.jsonl --region us-east-1

aws bedrock create-evaluation-job \
  --job-name flow-eval-run-1 \
  ...
```

### 3.6 Evaluation results

![Bedrock Evaluation job results page](screenshots/16-eval-results.png)

**Correctness score:** `<paste overall score>`

### 3.7 Written observations

- Are all three branches producing reasonable responses?
  - _(answer)_
- Any misrouted prompts (e.g. bug report getting the "call support" response)?
  - _(answer)_
- Are FAQ answers relevant to the actual question asked?
  - _(answer)_
- Any cases where the response was correct but the judge model scored it low? Why?
  - _(answer)_
- What did you change as a result of low scores, if anything?
  - _(answer)_

---

## Stand-Out Suggestions Implemented

- [ ] Guardrail blocking harmful content / prompt injection
- [ ] Edge-case test prompts (ambiguous / short / injection)
- [ ] Bedrock Knowledge Base replacing embedded FAQ
- [ ] Structured output for classifier

_(describe implementation for each checked item)_

---

## Cleanup

```bash
aws s3 rm s3://<bucket-name> --recursive --region us-east-1
aws cloudformation delete-stack --stack-name bug-report-testing-stack --region us-east-1
aws cloudformation delete-stack --stack-name bug-report-tool-stack --region us-east-1
```

- [ ] Flow deleted via console
- [ ] Agent deleted via console
- [ ] Both stacks confirmed deleted
