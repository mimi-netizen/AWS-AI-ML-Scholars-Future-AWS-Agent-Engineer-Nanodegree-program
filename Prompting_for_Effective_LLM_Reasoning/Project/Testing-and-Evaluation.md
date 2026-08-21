# Testing and Evaluation

Once your Bedrock Flow is built, you need to verify that it handles different messages correctly and produces expected responses. This guide walks you through the full testing workflow: writing test prompts, preparing your flow for programmatic invocation, running the test script, and evaluating the results using Bedrock Evaluations.

Bedrock Evaluations can't run a Bedrock Flow application directly, so instead you invoke the Flow, store its responses in a JSONL file, and upload that file to Bedrock Evaluations.

> Note: JSONL is a file format where every line represents a separate JSON document. This is in contrast to a JSON file, where the whole file represents a single JSON document.

## Automated Testing and Evaluation

This project includes a script that runs your application on a set of prompts. To use it, you need to:

- Create a list of test prompts in a separate file
- Run the testing script
- Evaluate the output using Bedrock Evaluations

## 1. Write Test Prompts

Before you can run any automated tests, you need a set of test prompts that cover each branch of your flow. The goal is to have at least one prompt per category so you can verify that the classifier routes messages to the correct path.

### Steps

Copy `flow-tests-template.json` to a new file called `flow-tests.json`:

```bash
cp flow-tests-template.json flow-tests.json
```

Open `flow-tests.json` and fill in the `flowInputNode.nodeName` field. This must match the name of the Input node in your flow. To find it, open your flow in the Bedrock console and click on the Input node — the name is displayed at the top of the node panel.

Add prompts you want to test your application on. Each entry has three fields:

| Field | Description |
|---|---|
| `id` | A unique identifier for the test (e.g. `t1_bug_report`). Used in log output to identify which test is running. |
| `prompt` | The customer message to send to the flow. Write realistic messages that clearly belong to one category. |
| `expected` | A description of what a good response should contain. This becomes the reference response for LLM-as-a-judge evaluation. It does not need to be an exact match — it describes the intent so the evaluator can assess whether the actual response is reasonable. |

## 2. Create a Flow Alias

To invoke your flow programmatically, you need a flow alias. An alias is a named pointer to a specific version of your flow. When you call the Bedrock API, you provide both the flow ID and an alias ID — not the flow itself. This is because Bedrock Flows supports versioning: you can publish multiple versions and use aliases to control which version gets invoked.

For this project, you just need one alias that points to the latest version.

### Steps

- Open your flow in the Bedrock console.
- Make sure you have saved and prepared your flow. If you have made changes since the last save, click **Save** first.
- Click on **Aliases** in the flow editor, then click **Create alias**.
- Give your alias a name (e.g. `v1`) and select **Prepare and create a new version and associate it to this alias**.
- Click **Create alias**.
- In the **Aliases** tab, copy the Alias ID that was generated — you will need it when running the test script.

You also need the Flow ID. You can find it on the flow's overview page or in the URL when viewing the flow in the console.

## 3. Set Up the Python Environment

The test script (`generate-eval-dataset.py`) uses `boto3` to call the Bedrock API. Before running it, set up a Python virtual environment and install the dependencies.

### Steps

Open a terminal and navigate to the project directory.

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Verify that `boto3` is installed:

```bash
python -c "import boto3; print(boto3.__version__)"
```

This should print a version number without any errors.

## 4. Run the Test Script

The `generate-eval-dataset.py` script reads your test prompts, invokes the flow once per prompt, and writes the results to a JSONL file. Each line in the output file contains the original prompt, the flow's actual response, and your reference response — everything that Bedrock Evaluations needs to run an LLM-as-a-judge assessment.

### Steps

Run the script with your flow ID and alias ID:

```bash
python generate-eval-dataset.py \
  --tests-json flow-tests.json \
  --flow-id <your-flow-id> \
  --flow-alias-id <your-flow-alias-id> \
  --region us-east-1
```

Replace `<your-flow-id>` and `<your-flow-alias-id>` with the values you noted in the previous section.

Trace output shows which nodes were executed and in what order, which is useful for debugging when a message is routed to the wrong branch.

When the script finishes, check the output file. Each line is a JSON object with this structure:

```json
{
  "prompt": "Your app crashes every time I try to upload a file...",
  "referenceResponse": "Acknowledges the issue and asks for steps to reproduce...",
  "modelResponses": [
    {
      "response": "I'm sorry to hear about the crash. Could you tell me...",
      "modelIdentifier": "my-flow-app"
    }
  ]
}
```

If any flow call failed, the `response` field will contain an error message prefixed with `[FLOW_ERROR]`. Check the terminal output for details.

## 5. Create Testing Resources

Before running evaluations you need an S3 bucket to store the dataset and results, and an IAM role that Bedrock Evaluations can assume. These are defined in `cloudformation-testing.yaml`.

### Steps

Deploy the testing stack:

```bash
aws cloudformation deploy \
  --template-file cloudformation-testing.yaml \
  --stack-name bug-report-testing-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Once the stack is created, retrieve the outputs — you will need the bucket name and role ARN:

```bash
aws cloudformation describe-stacks \
  --stack-name bug-report-testing-stack \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region us-east-1
```

This prints `EvalDatasetBucketName` and `BedrockEvalRoleArn`. Keep these values handy.

## 6. Run Bedrock Evaluations

Now that you have a JSONL dataset with your flow's responses alongside reference responses, you can use Bedrock Evaluations to assess quality automatically. Bedrock Evaluations supports an LLM-as-a-judge method: an evaluator LLM reads each response, the reference response, and scores how well the flow answered.

We use the Bring Your Own Inference (BYOI) approach because our responses come from a file we supply. The JSONL file already contains the flow's responses, so Bedrock Evaluations doesn't need to invoke anything — it only needs to judge the quality.

### Upload the Dataset

Upload the JSONL dataset to the S3 bucket created in the previous step:

```bash
aws s3 cp output_eval_dataset.jsonl s3://<your-bucket-name>/output_eval_dataset.jsonl \
  --region us-east-1
```

Note the full S3 URI — you will need it when creating the evaluation job.

### Create the Evaluation Job

Use the `BedrockEvalRoleArn` and `EvalDatasetBucketName` values from the CloudFormation stack outputs.

```bash
aws bedrock create-evaluation-job \
  --job-name flow-eval-run-1 \
  --role-arn <BedrockEvalRoleArn> \
  --evaluation-config '{
    "automated": {
      "datasetMetricConfigs": [{
        "taskType": "General",
        "dataset": {
          "name": "flow-eval-dataset",
          "datasetLocation": {
            "s3Uri": "s3://<EvalDatasetBucketName>/output_eval_dataset.jsonl"
          }
        },
        "metricNames": ["Builtin.Correctness"]
      }],
      "evaluatorModelConfig": {
        "bedrockEvaluatorModels": [{
          "modelIdentifier": "amazon.nova-pro-v1:0"
        }]
      }
    }
  }' \
  --inference-config '{
    "models": [{
      "precomputedInferenceSource": {
        "inferenceSourceIdentifier": "my-flow-app"
      }
    }]
  }' \
  --output-data-config '{"s3Uri": "s3://<EvalDatasetBucketName>/results/"}' \
  --region us-east-1
```

Replace `<BedrockEvalRoleArn>` and `<EvalDatasetBucketName>` with the values from the CloudFormation stack outputs.

To view results in the console, go to Amazon Bedrock → **Evaluations** in the left sidebar → click on your job once it shows status **Completed**.

## Review the Results

Once the job completes, click on it to see the results.

The results page shows overall scores and per-record breakdowns. The evaluator model scores each response based on how well it matches the intent described in the reference response.

Look for patterns in the scores:

- Are all three branches producing reasonable responses?
- Are any prompts being misrouted (e.g. a bug report getting the "call support" response)?
- Are FAQ answers relevant, or is the model missing the point of the question?
- Does your application return a correct response, but the LLM-as-a-judge model is marking it as incorrect?

If scores are low for a particular category, go back to your flow and iterate on the prompts. Common fixes include making the classifier prompt more specific, improving the FAQ prompt, or adding more detail to the agent instructions.

## Next Steps

If you want to expand your test suite, add more test entries to `flow-tests.json` and re-run the script. Try to improve your application to make sure that it reliably responds to most common use cases.

## Cleanup

### Step 1: Empty the S3 Bucket

AWS CloudFormation cannot delete an S3 bucket if there are files inside it. We need to wipe the evaluation data we uploaded earlier.

```bash
aws s3 rm s3://<your-bucket-name> --recursive --region us-east-1
```

### Step 2: Delete the CloudFormation Stacks

Now we can use the AWS CLI to tear down the infrastructure (Lambda, DynamoDB, IAM roles, and the empty S3 bucket).

Delete the Testing Stack:

```bash
aws cloudformation delete-stack --stack-name bug-report-testing-stack --region us-east-1
```

Delete the Tool Stack:

```bash
aws cloudformation delete-stack --stack-name bug-report-tool-stack --region us-east-1
```

### Step 3: Delete Bedrock Resources (via AWS Console)

- Delete the Flow
- Delete the Agent

### Step 4: Local Cleanup (Optional)

If you want to clean up your local machine or Udacity workspace Python virtual environment to save space, run:

```bash
rm -rf venv
```