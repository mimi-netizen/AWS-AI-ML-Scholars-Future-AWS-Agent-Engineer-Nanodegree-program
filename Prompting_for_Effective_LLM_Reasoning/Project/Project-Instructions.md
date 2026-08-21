Step 1: Create Resources for Your Application
First you will deploy a tool that your application needs to create bug reports.

When a customer reports a bug, the chatbot needs to persist it somewhere so the engineering team can follow up. In this project we use a DynamoDB table as a simple ticket store, and a Lambda function as the tool that Bedrock Agents can call to create a new ticket.

Deploy with CloudFormation
All tool resources are defined in cloudformation-tool.yaml. The template creates:

Resource	Name	Purpose
DynamoDB table	BugReports	Stores one item per bug report, keyed by ticketId
IAM role	create-bug-report-role	Grants the Lambda function permission to write logs and call PutItem on the table
Lambda function	create-bug-report	Receives a bug report from the Bedrock Agent and writes it to DynamoDB
Run the following command from the project root:

aws cloudformation deploy \
    --template-file cloudformation-tool.yaml \
    --stack-name bug-report-tool-stack \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
Wait for the command to print Successfully created/updated stack - bug-report-tool-stack.

Test the Lambda Function
Before connecting the tool to an agent, verify it works in isolation. In the Lambda console, open the create-bug-report function and go to the Test tab.

Create a new test event with the following JSON:

{
    "messageVersion": "1.0",
    "function": "create_bug_report",
    "actionGroup": "bug-report-actions",
    "sessionId": "test-session-001",
    "agent": {
        "id": "test-agent",
        "alias": "test-alias"
    },
    "parameters": [
        {
            "name": "description",
            "value": "The checkout page crashes when I click the Pay button"
        },
        {
            "name": "stepsToReproduce",
            "value": "1. Add an item to the cart. 2. Go to checkout. 3. Click Pay."
        },
        {
            "name": "environment",
            "value": "Chrome 120 on macOS Sonoma"
        }
    ]
}
Screenshot of the Lambda console Test tab showing how to create a test event with the sample JSON payload
Creating a test event in the Lambda console

Click Test. You should see a successful response containing a ticketId and "status": "OPEN".

Screenshot of the Lambda console showing a successful test execution with a response containing ticketId and status OPEN
Successful Lambda test result

To confirm the record was written, go to the DynamoDB console, open the BugReports table, and click Explore table items. You should see one item with the ticket ID from the response.

Screenshot of the DynamoDB console showing a bug report item in the BugReports table with ticketId, description, stepsToReproduce, environment, and status fields
Bug report record created in DynamoDB

Troubleshooting: If the test fails with AccessDeniedException, check that the IAM policy is attached to the correct execution role. If it fails with ResourceNotFoundException, verify the DynamoDB table name is exactly BugReports.

Step 2: Build the Bedrock Flow
Now that you have a tool set up, you can start building the Bedrock Flow application. Your application needs to handle three types of requests:

Bug reports — collect additional information and create a ticket using the Lambda tool from Step 1
Platform questions — answer common questions about orders, shipping, returns, and payments using the FAQ
Other requests — politely redirect the customer to a human support phone line
Bug Report Tool Parameters
The create_bug_report tool accepts three parameters:

Parameter	Required	Description
description	Yes	Description of the bug
stepsToReproduce	No	Steps to follow to reproduce the issue
environment	No	User's environment (browser, OS, device)
Tips
Classification output needs to be predictable for routing to work reliably
The FAQ document (online_shop_faq.md) is short enough to include directly in a prompt
Don't forget to deploy resources after changes (e.g., prepare agents after modifying them)
Implement and test your solution step by step
Use us-east-1 region for all Bedrock features
Step 3: Testing
Once you have your Bedrock Flow application, test it manually using the chat interface in Bedrock Flows. However, manual testing is tedious and not scalable. For automated testing:

Create a set of test prompts and define expected results
Run your application programmatically on the test set
Use Bedrock Evaluations to evaluate your application's outputs
Follow the detailed steps in the Testing Framework page to run automated tests and evaluate your flow.

Submission Checklist
Your project will be evaluated on these criteria:

Classification and Routing — The flow classifies messages and routes them across at least three distinct paths, each with its own Output node. The classifier returns only defined labels, and the Condition node uses exact string matching.

Bug Report Path — At least one Agent node configured with the create-bug-report action group. The agent collects description, steps to reproduce, and environment. A record is created in the BugReports DynamoDB table.

Platform Question and Other Paths — A Prompt node with FAQ content embedded answers platform questions (and redirects to phone support when the FAQ doesn't cover it). A separate path handles other requests with a phone redirect.

Testing and Evaluation — flow-tests.json covers all three paths. The generate-eval-dataset.py script produces a JSONL output. A Bedrock Evaluation job is created, and you provide written observations on the results.

Stand-Out Suggestions
Add a guardrail to block harmful content and prompt injection attempts
Add edge-case test prompts: ambiguous messages, very short messages, prompt injection attempts
Replace the embedded FAQ with a Bedrock Knowledge Base backed by a vector index
Use structured output to ensure the classifier only produces valid labels