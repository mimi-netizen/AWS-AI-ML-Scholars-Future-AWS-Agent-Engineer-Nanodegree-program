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

Output: ![AWS CLI version output in a terminal window. The command aws --version is shown, and the result reads aws-cli/2.36.20 Python/3.14.6 Linux/6.18.3-2-microsoft-standard-WSL x86_64 ubuntu.24. The wider scene is a dark developer terminal with minimal interface elements. The tone is neutral and technical.](image.png)


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

Output: ![Terminal output from the AWS CLI command aws sts get-caller-identity. The command appears in a dark developer terminal and the response is displayed as JSON in a monospace format. The output includes UserId, Account, and Arn fields, with the Account value shown as 72831954873 and the Arn value beginning with arn:aws:sts::72831954873:assumed-role. The wider environment is a minimal dark terminal interface with no extra UI elements. The tone is neutral and technical.](image-1.png)

**Note:** if using a Vocareum-style lab account, session tokens expire — document how long the session lasts and the refresh step, since a mid-project expiry will silently break `aws cloudformation deploy` calls with a credentials error that looks unrelated to the actual template.

### 0.3 Region set

```bash
aws configure get region
```

Confirm it prints `us-east-1`, or pass `--region us-east-1` explicitly on every command.

![Terminal window from the AWS CLI showing the region configuration check. The command aws configure get region is entered twice. The first output is us-west-2 and the second output is us-east-1, with the command prompt displayed above each result in a dark developer terminal. The wider environment is a minimal dark coding workspace with a file explorer and terminal UI visible in the background. The tone is neutral and instructional.](image-2.png)

### 0.4 Bedrock model access enabled

**Console region check:** the AWS Console has its own region selector (top-right), independent of aws configure. Confirm it reads US East (N. Virginia) before doing anything in the Bedrock/Lambda/DynamoDB consoles — a mismatch here means console actions land in the wrong region even after the CLI default is fixed.

![Amazon Bedrock Model access page in the AWS management console, shown in a dark interface. The left sidebar lists Amazon Bedrock, Discover, Labs, Test, and Infer. The main panel shows the heading Model access and the text Model access page has been retired. The body explains that serverless foundation models are now automatically enabled and that no manual activation is needed. A right-side panel lists regions, with United States, N. Virginia and us-east-1 selected. A note says AWS Marketplace permissions must be configured and that users can access models through the InvokeModel API or Converse. The browser chrome and AWS console header are visible in the wider environment, which is a dark, technical workspace. The tone is neutral and instructional.](image-3.png)

**Model access:** AWS retired the manual Model access page — foundation models (including Amazon Nova Pro) are now auto-enabled account-wide on first invocation, no activation step needed. 

Confirm access works by invoking the model once (Bedrock Playground, us-east-1) rather than checking a settings page.

![Amazon Bedrock Playground page in the AWS Management Console, displayed in a dark navy interface. The left sidebar includes Discover, Labs, Test, and Infer. In the main panel, the model selector shows Nova Pro, the mode is Chat, and the chat window contains the user message Hello, confirm you are working. The assistant response reads Hello! I am here and functioning as expected. How can I assist you today? If you have a question, need information, or require help with a task, feel free to ask! The wider environment is a browser window on a desktop with a dark coding workspace visible behind it. The overall tone is neutral and technical.](image-4.png)

### 0.5 Python environment and dependencies

```bash
python3 --version
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

![Dark terminal window in a developer workspace showing the Python virtual environment setup steps. The command python3 --version is entered first, returning Python 3.12.3. Next, python3 -m venv venv is run, followed by source venv/bin/activate, and then pip install -r requirements.txt. The terminal uses a dark theme with blue command text on a black background, while the surrounding workspace remains minimally visible in a neutral coding environment. The overall tone is instructional and technical.](image-5.png)

Verify boto3:
```bash
python -c "import boto3; print(boto3.__version__)"
```

Output: ![Terminal window in a dark developer environment showing the boto3 version check. The command python -c import boto3; print(boto3.__version__) is entered in the terminal, and the output line reads 1.42.54 in blue text. The surrounding workspace is minimal and technical, with a dark UI and command prompt visible. The tone is neutral and instructional.](image-6.png)

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
