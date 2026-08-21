
# Project Rubric Checklist

Use this checklist to verify that your project meets the rubric requirements before submission.

---

## 1. Implement Classification and Routing

### Criteria
Build a Bedrock Flow that classifies customer messages and routes them across distinct paths.

### Submission Requirements
- [ ] The flow classifies incoming customer messages into distinct categories
- [ ] The classifier produces consistent, unambiguous output that can drive routing decisions
- [ ] Messages are routed to distinct paths based on their category
- [ ] Distinct paths exist in the flow, each terminating at a separate Output node

### Evidence to Include
- [ ] Screenshot of the full flow diagram
- [ ] Screenshot of the classifier prompt configuration
- [ ] Screenshot of the Condition node expressions

---

## 2. Implement the Bug Report Path

### Criteria
Implement the bug report path using a Bedrock Agent with a tool to collect information and create tickets.

### Submission Requirements
- [ ] The bug report path includes a Bedrock Agent
- [ ] The agent is configured to invoke the Lambda tool to persist the ticket
- [ ] The agent collects:
  - [ ] bug description
  - [ ] steps to reproduce
  - [ ] environment information
- [ ] A record is created in the `BugReports` DynamoDB table when a bug report message is processed through the flow

### Evidence to Include
- [ ] Screenshot of the Agent node configuration showing the action group
- [ ] Screenshot(s) of flow test responses for creating a bug report
- [ ] Screenshot(s) of flow test responses for creating a bug report with follow-up questions
- [ ] Screenshot of the DynamoDB `BugReports` table showing at least one item created by the flow

---

## 3. Implement Platform Question and Other Request Paths

### Criteria
Implement Platform Question and Other Request paths.

### Submission Requirements
- [ ] The application produces a relevant answer when the question is covered by the FAQ
- [ ] The application directs a user to a support phone number when the question is not covered by the FAQ
- [ ] A separate path exists for other customer support requests that directs the user to a support phone number

### Evidence to Include
- [ ] Screenshot of the FAQ Prompt node template showing embedded FAQ content
- [ ] Screenshot(s) of flow test responses for:
  - [ ] a covered question
  - [ ] an uncovered question
  - [ ] an other-request message

---

## 4. Implement the Testing and Evaluation

### Criteria
Test the flow using an automated test suite and evaluate response quality using Bedrock Evaluations with LLM-as-a-judge.

### Submission Requirements
- [ ] `flow-tests.json` contains:
  - [ ] at least one test entry for the bug report path
  - [ ] at least one test entry for the platform question path
  - [ ] at least one test entry for the other requests path
- [ ] The `generate-eval-dataset.py` script is run against the flow and produces a JSONL output file
- [ ] The JSONL file is uploaded to S3 and a Bedrock Evaluation job is created
- [ ] The result's correctness score is close to 1

### Evidence to Include
- [ ] `flow-tests.json` file
- [ ] JSONL output file
- [ ] Screenshot of the Bedrock Evaluation job results page
- [ ] Written observation in a `README` or separate text file

---

## Suggestions to Make the Project Stand Out

- [ ] Add a guardrail to the flow that blocks harmful content and prompt injection attempts before any model processes the message
- [ ] Add edge-case test prompts to `flow-tests.json`, such as:
  - [ ] ambiguous messages that could belong to multiple categories
  - [ ] very short messages with minimal context
  - [ ] prompt injection attempts
- [ ] Replace the embedded FAQ with a Bedrock Knowledge Base backed by a vector index
- [ ] Use structured output so the classifier node only produces valid values

---

## Final Pre-Submission Check

Before submitting, confirm that:

- [ ] Every required path works end-to-end
- [ ] Every rubric bullet is satisfied
- [ ] Every required screenshot has been captured
- [ ] Your evidence clearly matches the rubric
- [ ] Your evaluation results and written observations are included
