# Demo 3 – Bedrock Agent Prompt

## Setup

### Step 1 – Create the Lambda Functions

The Lambda function code is in the `lambda/` folder. Create two functions in the AWS console:

1. Open the [AWS Lambda console](https://console.aws.amazon.com/lambda) and click **Create function**

![AWS Lambda console landing page with the Create function button highlighted near the top right of the interface, and the Lambda service header and navigation menu visible in the background. The button text reads Create function.](images/image.png)

2. Choose **Author from scratch**, set runtime to **Python 3.15**
![AWS Lambda console with the Create function button highlighted in the upper right, the Lambda service header visible at the top, and the navigation menu displayed in the background. The button label reads Create function.](images/image1.png)

3. Create the first function:
   - Name: `demo3-get-weather`
   - Paste the code from `lambda/get_weather/lambda_function.py`
   - Click **Deploy**
   ![AWS Lambda console page showing the Deploy button highlighted in the upper right while the function configuration panel is visible in the main workspace. The interface is a standard AWS management console screen with a neutral, technical tone.](images/image3.png)
   ![AWS Lambda console page showing the deployed function details and configuration area with the Lambda service navigation visible in the background. The screen has a neutral, professional tone.](images/image-1.png)



4. Repeat for the second function:
   - Name: `demo3-get-top-attractions`
   - Paste the code from `lambda/get_top_attractions/lambda_function.py`
   - Click **Deploy**
   ![AWS Lambda console page showing the second function configuration screen with the Deploy button and main settings panel visible. The interface is a standard AWS management console workspace with a neutral, technical tone.](images/image-2.png)

---

### Step 2 – Create the Bedrock Agent

1. Open the [Amazon Bedrock console](https://console.aws.amazon.com/bedrock) and navigate to **Agents**

Note: Bedrock Agents (Agents Classic) is only available in the following regions. Make sure you have set your AWS region to one of these:

us-east-1
us-east-2
us-west-2
![Screenshot of an Amazon Bedrock note showing the supported AWS regions for Agents Classic: us-east-1, us-east-2, and us-west-2. The text appears in a simple, informational panel with a neutral technical tone.](images/image2.png)

2. Click **Create agent**
3. Give the agent a name (e.g. `travel-assistant`)
![Amazon Bedrock console page for creating a new agent, with the agent name field and model selection controls visible in the main workspace. The interface has a neutral technical layout and a left navigation pane.](images/image4.png)

4. Under **Model**, select **Amazon Nova Pro**
5. Paste the agent instruction below into the **Instructions for the Agent** field
6. Click **Save**

**My account doesn't support Bedrock agents so i'll have to redo the steps using AgentsCore**
![Screenshot of a note explaining that the current AWS account does not support Amazon Bedrock Agents, so the steps must be repeated using Agents Core. The message appears in a simple interface with a neutral, slightly frustrated tone.](images/image5.png)

---

### Step 3 – Create the Action Groups

Bedrock only allows one Lambda per action group. Create two separate action groups:

**Action Group 1: `get-weather`**

1. Click **Add action group** and name it `get-weather`
2. Under **Action group type**, choose **Define with function details**
3. Add a function named `get_weather` with parameters:
   - `city` (string, required) — the city name
   - `date` (string, required) — the date in YYYY-MM-DD format
4. Under **Action group invocation**, select the `demo3-get-weather` Lambda
5. Click **Save**

**Action Group 2: `get-top-attractions`**

1. Click **Add action group** and name it `get-top-attractions`
2. Under **Action group type**, choose **Define with function details**
3. Add a function named `get_top_attractions` with parameters:
   - `city` (string, required) — the city name
4. Under **Action group invocation**, select the `demo3-get-top-attractions` Lambda
5. Click **Save**

---

### Step 4 – Prepare and Test

1. Click **Save and exit**
2. Click **Prepare** to build the agent
3. Once preparation completes, use the **Test** panel on the right to try the test prompt below

---

## Agent Instruction

```
You are a helpful travel planning assistant. When a user asks for travel recommendations, always use the available tools to gather current weather conditions and top attractions before making any suggestions. Always look up available attractions using a tool call. If the weather is poor, prioritize indoor attractions. Always tailor suggestions to any preferences the user mentions, such as traveling with family or having limited time.
```

---

## Test Prompt

```
I'll be in London this Saturday with my family. What should we do?
```

**Expected:** The agent invokes `get_weather` and `get_top_attractions` before responding. Final answer is grounded in tool results, accounts for weather conditions, and filters for family-friendly options.
