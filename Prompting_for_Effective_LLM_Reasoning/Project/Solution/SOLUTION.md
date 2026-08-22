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

**Result:** ![Dark terminal showing a successful AWS CloudFormation deployment. The terminal displays the command deploying cloudformation-tool.yaml with stack name bug-report-tool-stack, CAPABILITY_NAMED_IAM, and region us-east-1, followed by the message Successfully created/updated stack - bug-report-tool-stack. The surrounding developer workspace is minimal, with a successful and instructional tone.](image-7.png)

Stack outputs (`BugReportsTableArn`, `LambdaFunctionArn`, `LambdaExecutionRoleArn`):

```
BugReportsTableArn      = arn:aws:dynamodb:us-east-1:728319584873:table/BugReports-579769a0
LambdaFunctionArn       = arn:aws:lambda:us-east-1:728319584873:function:create-bug-report-579769a0
LambdaExecutionRoleArn  = arn:aws:iam::728319584873:role/create-bug-report-role-579769a0
```


![VS Code terminal displaying the AWS CloudFormation stack outputs for bug-report-tool-stack. The command aws cloudformation describe-stacks queries the stack in us-east-1 and formats the results as a table. The table lists BugReportsTableArn with value arn:aws:dynamodb:us-east-1:728319584873:table/BugReports-579769a0, LambdaExecutionRoleArn with value arn:aws:iam::728319584873:role/create-bug-report-role-579769a0, and LambdaFunctionArn with value arn:aws:lambda:us-east-1:728319584873:function:create-bug-report-579769a0. A shell prompt is visible below the successful output in a dark, technical development environment.](image-8.png)

### 1.2 Test Lambda function in isolation

Test event used: sample JSON from Project-Instructions.md (checkout crash example).

![AWS Lambda Functions console showing the deployed create-bug-report-579769a0 function](image-10.png)

![AWS Lambda console showing the deployed create-bug-report-579769a0 function in the United States N Virginia region. The Function overview displays the Lambda function, its ARN, the bug-report-tool-stack application, and controls for throttling, copying the ARN, adding a trigger, and adding a destination. The dark AWS management console has a technical, successful tone.](image-11.png)

![AWS Lambda Test event panel for create-bug-report-579769a0. The main focus is the test event configuration form in the AWS Lambda console. The panel shows a dark interface with a blue highlighted Create new event tab, a Synchronnous invocation type selected, event name field with the placeholder MyEventName, and a Private event sharing setting. At the top of the window, the Lambda function name create-bug-report-579769a0 is visible in the header, and a dark AWS navigation bar and browser chrome frame the page. The overall tone is technical and successful, with a clean development environment. Text visible in the image includes AWS Lambda, create-bug-report-579769a0, Test event, Invoke your function without saving an event, Create new event, Edit saved event, Synchronous, Event name, MyEventName, Private, and CloudShell, Agent Toolkit for AWS, Feedback.](image-12.png)

![AWS Lambda Test tab showing a successful invocation of create-bug-report-579769a0. The dark AWS console displays Executing function: succeeded and a Response panel with JSON showing actionGroup bug-report-actions, function create_bug_report, ticketId 5f81bbeb-2fa4-4f4c-b8fb-9b080e86ff16, and status OPEN. The Summary section shows Function version $LATEST, execution time 2 seconds ago, and a request ID. The AWS region is United States N Virginia, and the technical interface has a successful tone.](image-13.png)

![AWS CloudWatch Log Management showing the Lambda function log group /aws/lambda/create-bug-report-579769a0. The dark AWS console displays log group details including the ARN arn:aws:logs:us-east-1:728319584873:log-group:/aws/lambda/create-bug-report-579769a0:*, Standard log class, retention Never expire, and region United States N Virginia. Navigation links include CloudWatch, Log management, Ingestion, Dashboards, Alarms, AI Operations, GenAI Observability, Application Signals APM, Infrastructure Monitoring, and Logs. The page is a technical monitoring environment with a clear, successful deployment-focused tone.](image-14.png)

Ticket ID returned: `5f81bbeb-2fa4-4f4c-b8fb-9b080e86ff16`

### 1.3 Verify DynamoDB record

![Amazon DynamoDB Tables page in the AWS Management Console showing one active table, BugReports-579769a0. The table uses ticketId as its partition key, has no sort key or indexes, and has deletion protection turned off. The dark console interface is open in the United States N Virginia region, with DynamoDB navigation on the left and a technical, successful deployment-verification tone.](image-15.png)

![Amazon DynamoDB table settings page for BugReports-579769a0 in the AWS Management Console. The table is Active and has ticketId as its String partition key, no sort key, on-demand capacity, zero items, and zero bytes. Point-in-time recovery and resource-based policy are not active, and there are no active alarms. The page displays the table ARN arn:aws:dynamodb:us-east-1:728319584873:table/BugReports-579769a0. Visible navigation includes DynamoDB, Tables, Settings, Indexes, Monitor, Global tables, Backups, Exports and streams, Permissions, Actions, and Explore table items. The dark console provides a technical table-verification environment.](image-16.png)

![Amazon DynamoDB console showing the BugReports-579769a0 table with a Get live item count dialog open. The dialog reports an item count of 1, scan status Complete, and last updated August 22, 2026 11:46:02, with Scan again and Cancel buttons. It warns that scanning can consume additional read capacity and is not recommended for very large or critical production tables. Behind the dialog, the table status is Active and the Amazon Resource Name is arn:aws:dynamodb:us-east-1:728319584873:table/BugReports-579769a0. The dark AWS Management Console is open in the United States N Virginia region, creating a technical and successful verification environment.](image-17.png)

![Amazon DynamoDB Explore items page displaying one returned item from the BugReports-579769a0 table. The AWS Management Console shows a completed scan with Items returned: 1, Items scanned: 1, Efficiency: 100%, and RCUs consumed: 2. The results table includes ticketId, createdAt, description, environment, status, and stepsToReproduce columns; the single record begins with ticket ID 5f81bbeb-2fa4-4f4c-..., has status OPEN, and contains checkout-related bug details. The dark AWS console is open in the United States N Virginia region, providing a technical and successful verification environment.](image-18.png)

![Amazon DynamoDB Edit item page for the BugReports-579769a0 table, showing the single bug report record in a dark AWS Management Console. The form displays ticketId 5f81bbeb-2fa4-4f4c-b8fb-9b080e86ff16, createdAt 2026-08-22T08:39:54.856325+00:00, description The checkout page crashes when I click the Pay button, environment Chrome 120 on macOS Sonoma, status OPEN, and stepsToReproduce 1. Add an item to the cart. 2. Go to checkout. 3. Click Pay. Visible interface text includes Edit item, Attributes, Attribute name, Value, Type, Remove, Add new attribute, Form, JSON view, DynamoDB, Explore items: BugReports-579769a0, and CloudShell. The technical interface presents a clear, successful record-verification environment.](image-19.png)

```
{
  "ticketId": {
    "S": "5f81bbeb-2fa4-4f4c-b8fb-9b080e86ff16"
  },
  "createdAt": {
    "S": "2026-08-22T08:39:54.856325+00:00"
  },
  "description": {
    "S": "The checkout page crashes when I click the Pay button"
  },
  "environment": {
    "S": "Chrome 120 on macOS Sonoma"
  },
  "status": {
    "S": "OPEN"
  },
  "stepsToReproduce": {
    "S": "1. Add an item to the cart. 2. Go to checkout. 3. Click Pay."
  }
}
```

---

## Step 2: Bedrock Flow

### 2.1 Classification design

Labels used: `BUG_REPORT | PLATFORM_QUESTION | OTHER`

Classifier prompt:
```
You are a message classifier for a customer support chatbot. Classify the customer's message into exactly one of these three categories:

BUG_REPORT - the customer is reporting something broken, malfunctioning, or not working as expected on the website or app.
PLATFORM_QUESTION - the customer is asking about orders, shipping, delivery, returns, refunds, payments, products, or their account.
OTHER - the message doesn't fit either category above (general inquiries, unrelated topics, complaints not about a bug, etc).

Respond with ONLY the category label and nothing else. No punctuation, no explanation, no extra words.

Customer message: {{input}}
```

Rationale for label choice / prompt structure:
- Short, all-caps, single-token-ish labels minimize the chance of the model appending punctuation, casing variation, or extra words that would break the Condition node's exact-string matching.
- The prompt explicitly forbids anything except the bare label to reduce prose leakage into the classifier output.
- Open question / edge case: messages that are complaints but not bugs (e.g. "my refund is taking too long") currently fall under OTHER and get redirected to phone support rather than answered from the FAQ. 

#### 2.1.1 Build steps

1. Bedrock console → Flows → Create flow (region: us-east-1 — confirm region selector before starting)
![Amazon Bedrock Flows page in the AWS Management Console, showing the How it works section with Create a flow, Test the flow, and Use the flow guidance, plus an empty Flows list and an orange Create flow button. The dark-themed interface is open in the United States N. Virginia region and has a calm, task-focused tone.](image-20.png)

![Amazon Bedrock Create flow dialog in the AWS Management Console. The Name field contains customer_support_chatbot, with options to enter a description, create and use a new service role, or use an existing service role. The dialog includes Additional Configurations, Cancel, and Create flow buttons. The dark-themed console is open to Flows in the United States N. Virginia region, with a focused and task-oriented interface.](image-21.png)

![Amazon Bedrock Flow builder for customer_support_chatbot in the AWS Management Console. The dark-themed interface shows the United States N. Virginia region and a blank flow canvas. The left Flow builder panel has Nodes selected and lists Collector, Condition, DoWhile Loop, and Iterator under Logic. The top toolbar includes Duplicate, Open Flow templates, Save, Save and exit, and Create Execution. On the right, the Test flow panel contains an empty message field with a Run button. The uncluttered workspace has a focused, task-oriented tone.](image-22.png)

2. Add an Input node. Input node name: `FlowInputNode`
![Amazon Bedrock Flow builder showing a blank customer support chatbot canvas with a Flow Input node connected to a Prompts node and a Flow output node. The left configuration panel is open for the Flow Input node and shows the node name FlowInputNode and output name document. The top toolbar includes Duplicate, Open Flow templates, Save, Save and exit, and Create Execution. On the right, the Test flow panel contains an empty message field and a Run button. The dark AWS Management Console interface is open in the United States N. Virginia region and presents a focused workspace for configuring and testing the flow.](image-23.png)


3. Add a Prompt node after the Input node. Model: Amazon Nova Pro. Paste the classifier prompt above, wire `{{document}}` to the Input node's output.
![Amazon Bedrock Flow builder showing the Prompts node configuration for a customer support chatbot. The canvas contains a Flow input node connected to Prompt_1 and a Flow output node. The Configure panel identifies the node as Prompts, shows the node name Prompt_1, and offers options to use a prompt from Prompt Management or define one in the node. The AWS console is open to the customer_support_chatbot working draft in the United States N. Virginia region, with the Test flow panel and Run button visible on the right. The focused dark-themed interface presents a clean workspace for configuring and testing the flow.](image-24.png)

![Amazon Bedrock Flow builder showing the customer_support_chatbot working draft in the United States N. Virginia region. A blank flow canvas contains a Flow input node connected to a Prompts node labeled Prompt_1 and a Flow output node. The left configuration panel shows the selected Nova Pro 1.0 On-demand model, an optional Guardrail selector, and a classifier prompt beginning You are a message classifier for a customer support chatbot. The right Test flow panel has an empty Enter your message here field and a Run button. The dark AWS Management Console interface presents a focused workspace for configuring and testing the prompt flow.](image-25.png)


4. Add a Condition node after the Prompt node. Define three exact-match conditions, one per label (`BUG_REPORT`, `PLATFORM_QUESTION`, `OTHER`).

Right panel, "Enter your message here" box: type a clean bug report, e.g.

```
The checkout page crashes when I click Pay.
```

Click **Run**. Look at the output — it should show `modelCompletion: BUG_REPORT` with nothing else attached (no period, no quotes, no "Category: " prefix).

![Amazon Bedrock Flow builder for customer_support_chatbot showing a classifier test result. In the Test flow panel, the submitted message reads The checkout page crashes when I click Pay. and the FlowOutputNode response is BUG_REPORT. The dark AWS Management Console displays an otherwise empty flow canvas, with the Flow builder panel on the left and the message entry area with a Run button on the right. The focused interface documents a successful bug-report classification test.](image-26.png)

![Amazon Bedrock Flow builder Test flow screen showing the customer support message The checkout page crashes when I click Pay. and the FlowOutputNode result BUG_REPORT. A JSON details pane displays the input document, the Prompt_1 node, FlowInputNode, and the timestamp, while the message entry field remains visible below. The dark AWS Management Console workspace has a focused, task-oriented tone.](image-27.png)

Then run two more, one at a time, checking output each time:

```
How long does delivery usually take?
```
→ expect exactly `PLATFORM_QUESTION`

![Amazon Bedrock Flow builder test screen showing the customer message How long does delivery usually take? and a FlowOutputNode result of PLATFORM_QUESTION. The expanded Output trace displays JSON containing the submitted document, the next Prompt_1 node, the document output type STRING, FlowInputNode, and a timestamp. The dark AWS Management Console workspace also shows the empty Enter your message here field and Run button. The focused interface documents a successful platform-question classification test.](image-28.png)

```
Do you have any job openings?
```
→ expect exactly `OTHER`
![Amazon Bedrock Flow builder test panel showing the message Do you have any job openings? and the FlowOutputNode result OTHER. The expanded Output trace displays JSON with the submitted document, the Prompt_1 node, document output type STRING, FlowInputNode, and a timestamp. The dark AWS Management Console interface includes the Enter your message here field and Run button, presenting a clear successful classification test.](image-29.png)

### 2.1.2 Wiring the Condition node

1. In the flow canvas, delete the direct wire from Prompt_1's `modelCompletion` output straight into FlowOutputNode's input — you're about to insert a Condition node between them.
![Amazon Bedrock Flow builder canvas showing a purple Prompts node labeled Prompt_1 connected by a curved line to a gold Flow output node labeled FlowOutputNode. Prompt_1 displays the labels Input, Output, document, modelCompletion, and String. FlowOutputNode displays Input, document, and String. The nodes sit on an otherwise empty dotted-grid canvas, documenting the initial direct connection in a neutral technical workspace.](image-30.png)
![Amazon Bedrock Flow builder canvas showing a Flow input node connected to a purple Prompts node labeled Prompt_1, with a separate gold Flow output node labeled FlowOutputNode below. Visible labels include document, String, Input, Output, and modelCompletion. The nodes are arranged on a light dotted-grid workspace, showing the initial flow configuration before the output node is connected.](image-31.png)

2. From the Nodes panel (left, where "Nodes | Configure" tabs live), drag a Condition node onto the canvas.
![Amazon Bedrock Flow builder showing a Condition node named ConditionNode_1 on a dotted-grid canvas below a Prompts node named Prompt_1. The Condition node contains the labels Input, conditionInput, String, Conditions, Condition, No condition set, Go to node, Not defined, If all conditions are false, and Go to node. Prompt_1 shows document, String, and modelCompletion, and a Flow output node named FlowOutputNode is positioned to the right. The left Nodes panel lists Collector, Condition, DoWhile Loop, and Iterator. The right Test flow panel shows a FlowOutputNode result of OTHER, an Enter your message here field, and a Run button. The dark AWS Management Console workspace has a focused, task-oriented interface for configuring conditional routing.](image-32.png)


3. Wire Prompt_1's `modelCompletion` output → Condition node's input.
![Amazon Bedrock Flow builder canvas showing a Flow input node connected to a Prompts node named Prompt_1, whose modelCompletion output connects to a Condition node named ConditionNode_1. Visible labels include Output, document, String, Input, modelCompletion, conditionInput, Conditions, Condition, No condition set, Go to node, and Not defined. The Condition node also shows If all conditions are false and a second Go to node field set to Not defined. The nodes are arranged on a light dotted-grid workspace for configuring conditional routing.](image-33.png)


4. In the Condition node's Configure tab, add three conditions, each an exact-match expression against the input, one per label:
   - Condition 1: input equals `BUG_REPORT`
   - Condition 2: input equals `PLATFORM_QUESTION`
   - Condition 3: input equals `OTHER` (or use the Condition node's default/else branch for this one, if it has one — check what the UI offers)
![Amazon Bedrock Flow builder canvas showing Prompt_1 connected to ConditionNode_1, which routes the prompt output to FlowOutputNode. The Condition node displays the expression $.conditionInput == BUG_REPORT, the Go to node field set to FlowOutputNode, and If all conditions are false set to Not defined. Visible labels include Flow input, Output, document, String, Prompts, modelCompletion, conditionInput, Conditions, and Flow output. The nodes are arranged on a light dotted-grid workspace with zoom and canvas controls along the right side.](image-34.png)

![Amazon Bedrock Flow Builder canvas showing two Condition nodes routing classification results. ConditionNode_2 contains the expression $.conditionInput == PLATFORM_QUESTION and routes to FaqOutput. ConditionNode_3 contains the expression $.conditionInput == OTHER and routes to OtherOutput. Each node displays conditionInput, String, Conditions, Condition, Go to node, and If all conditions are false fields. Partial output nodes are visible on the right, including FaqOutput and OtherOutput. The nodes are arranged side by side on a light dotted-grid workspace in a technical workflow editor.](image-35.png)

![Amazon Bedrock Flow Builder canvas showing three gold Flow output nodes arranged vertically and connected from a partially visible Condition node on the left. The nodes are labeled FlowOutputNode, FaqOutput, and OtherOutput, and each displays Input, document, and String. Partially visible condition text includes == OTHER. The nodes sit on a light dotted-grid workflow workspace in a clear, technical configuration view.](image-36.png)



5. You'll now need three separate Output nodes (not the single existing FlowOutputNode) — per the project's own tip: "A single Output node can't receive connections from multiple branches." Rename or duplicate FlowOutputNode into three, e.g. `BugReportOutput`, `FaqOutput`, `OtherOutput`.

![Amazon Bedrock Flow Builder canvas showing a ConditionNode_1 routing the BUG_REPORT classification to FlowOutputNode. The condition reads $.conditionInput == BUG_REPORT, and its Go to node field is set to FlowOutputNode. A second ConditionNode_2 below is partially visible with the condition $.conditionInput == PLATFORM_QUESTION and a route to FaqOutput. The nodes are displayed on a light dotted-grid workflow canvas in a clear technical configuration environment.](image-37.png)
![Amazon Bedrock Flow Builder canvas showing Prompt_1 connected to two Condition nodes that route classified requests to separate outputs. The upper ConditionNode_2 displays the expression $.conditionInput == PLATFORM_QUESTION and routes to FaqOutput. The lower ConditionNode_3 displays the expression $.conditionInput == OTHER and routes to OtherOutput. Visible node text includes Flow input, Prompts, Prompt_1, modelCompletion, Condition, conditionInput, Conditions, Go to node, FaqOutput, OtherOutput, and Flow output. The nodes are arranged on a light dotted-grid workflow canvas in a focused technical configuration environment.](image-38.png)

6. Wire each Condition branch to its own temporary Output node.

![AWS Amazon Bedrock Flow Builder displays the saved customer_support_chatbot working draft. On the dotted workflow canvas, Flow input connects to Prompts Prompt_1, whose modelCompletion output connects to parallel Condition nodes ConditionNode_2 and ConditionNode_3. ConditionNode_2 shows conditionInput == PLATFORM_QUESTION and routes to the Flow output FaqOutput. ConditionNode_3 shows conditionInput == OTHER and routes to OtherOutput. The green banner reads Changes to customer_support_chatbot successfully saved. The AWS console interface has a focused technical configuration tone.](image-39.png)

7. Test all three messages again once wired, confirming each lands at the correct Output node this time — not just the correct label.

In "Enter your message here," type a clear bug report, e.g. `The checkout page crashes when I click Pay.`
Click Run.
In the response, check the node name shown above the output — it should say FlowOutputNode (that's the BUG_REPORT destination), with BUG_REPORT as the value.

![Amazon Bedrock Test flow panel showing the message The checkout page crashes when I click Pay and a completed result from FlowOutputNode. The result value is BUG_REPORT. The expanded ConditionNode_1 trace shows document BUG_REPORT, nodeInputName conditionInput, source node Prompt_1, output field modelCompletion, expression $.data, and type STRING. The dark AWS console presents the result in a focused technical debugging workspace.](image-40.png)
![Amazon Bedrock flow test result confirming that a clear checkout crash report was classified as BUG_REPORT and routed to FlowOutputNode. The dark console interface shows the completed test response and the flow execution details in a technical workflow environment.](image-41.png)

`How long does delivery usually take?` — response should come from FaqOutput, value PLATFORM_QUESTION.

![Amazon Bedrock flow test result for the message How long does delivery usually take? showing routing to FaqOutput with the classification value PLATFORM_QUESTION. The result appears in the dark Test flow console within a structured workflow debugging workspace.](image-42.png)
![Amazon Bedrock execution details confirming that a delivery-time question was classified as PLATFORM_QUESTION and reached the FaqOutput node. The dark technical console displays the completed flow test and routing trace.](image-44.png)

`Do you have any job openings?` — response should come from OtherOutput, value OTHER.

![Amazon Bedrock flow test result for the message Do you have any job openings? showing routing to OtherOutput with the classification value OTHER. The result is displayed in the dark Test flow console as a completed workflow test.](image-45.png)
![Amazon Bedrock Test flow console showing a completed customer support classification. The left panel displays the message The checkout page crashes when I click Pay and a FlowOutputNode result with the value BUG_REPORT. The right panel shows an expanded ConditionNode_3 input trace with document OTHER, nodeInputName conditionInput, source node Prompt_1, output field modelCompletion, and type STRING. The dark AWS debugging workspace has a focused technical tone.](image-46.png)

### Notes / issues encountered — 2.1

- The three Condition nodes (ConditionNode_1/2/3) are wired in parallel, each fed independently from Prompt_1's modelCompletion output, rather than chained. Each has an exact-match condition for one label (BUG_REPORT, PLATFORM_QUESTION, OTHER) routing to its own Output node.
- Known limitation: none of the three "If all conditions are false" branches are wired to a fallback. If the classifier ever returns output that doesn't exactly match one of the three defined labels (whitespace, casing, extra text), the flow has no defined path and will likely fail rather than degrade to a redirect. Attempted to wire each false-branch to OtherOutput as a defensive catch-all; connections did not take in the console (possibly because Output node inputs don't support multiple incoming wires — unconfirmed). Left unresolved for now.
- Mitigation in place instead: the classifier prompt was tested in isolation across all three categories and returned clean, exact-match output with no stray characters each time (see 2.1.1). Eval testing in Step 3 should be checked for any FLOW_ERROR entries that might indicate this edge case firing in practice.







### 2.2 Bug Report path (Agent node)

Action group / Lambda linkage:


Data collected: description, stepsToReproduce, environment
- "User input" advanced setting enabled: Yes/No

Test — clear bug report (single turn):

![Amazon Bedrock flow test showing a clear bug report submitted through the customer support flow and its resulting response. The dark workflow console presents the test interaction in a focused technical environment.](screenshots/09-test-bug-clear.png)

Test — vague bug report requiring follow-up questions:

![Amazon Bedrock flow test showing a vague bug report that triggers follow-up questions from the customer support flow. The dark console displays the conversational test in a technical workflow environment.](screenshots/10-test-bug-followup.png)

DynamoDB record created via the Flow (not the isolated Lambda test):

![Amazon DynamoDB record created by the customer support flow after a bug report test. The database console displays stored bug details including the report description, reproduction steps, and environment in a structured technical interface.](screenshots/11-dynamodb-flow-record.png)

### 2.3 Platform Question path

FAQ embedding approach:

![Amazon Bedrock flow builder showing the FAQ prompt node template used for platform questions. The prompt configuration appears on a dark technical workflow canvas.](screenshots/12-faq-prompt-node.png)

Test — question covered by FAQ:

![Amazon Bedrock flow test showing a platform question answered by the FAQ path because the question is covered by the configured FAQ content. The dark console displays the completed test in a technical workflow environment.](screenshots/13-test-faq-covered.png)

Test — question NOT covered by FAQ (should redirect to phone support):

![Amazon Bedrock flow test showing a platform question not covered by the FAQ and redirected to phone support. The dark console displays the completed routing result in a technical workflow environment.](screenshots/14-test-faq-uncovered.png)

### 2.4 Other Requests path

Test — generic/unrelated request:

![Amazon Bedrock flow test showing a generic or unrelated request routed through the Other Requests path. The dark console displays the completed classification and response in a focused technical workflow environment.](screenshots/15-test-other.png)

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
