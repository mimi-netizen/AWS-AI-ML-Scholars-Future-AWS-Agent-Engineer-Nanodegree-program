# Demo 3 — Rebuilt for Amazon Bedrock AgentCore

This walks through recreating the original "travel-assistant" exercise using
AgentCore instead of the retired Bedrock Agents console. The core idea:
your two Lambda functions become two Python functions, your agent
instruction becomes a system prompt, and instead of clicking through the
Bedrock Agents console you write ~30 lines of Python.

---

## Concept mapping (old → new)

| Bedrock Agents (old) | AgentCore (new) |
|---|---|
| Agent created in console | `strands.Agent` object in Python |
| "Instructions for the Agent" field | `system_prompt` string |
| Action Group + Lambda function | Python function with `@tool` decorator |
| Amazon Nova Pro (model dropdown) | Model ID passed to `BedrockModel` |
| **Test** panel in console | Run the Python script locally |
| **Prepare** button | Not needed — no separate build step |

---

## Step 1 — Install prerequisites

You need Python 3.10+ and an AWS account with Bedrock model access already
configured (same AWS account you were going to use for Bedrock Agents).

```bash
mkdir demo3-agentcore
cd demo3-agentcore
python3 -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit boto3
```

## Step 2 — Enable model access

In the [Amazon Bedrock console](https://console.aws.amazon.com/bedrock),
go to **Model access** and make sure you have access enabled for the model
you want to use. The original exercise used Amazon Nova Pro — that still
works here. If you'd rather use Claude (most Strands tutorials default to
this), enable a Claude model instead. Either is fine; just note the model
ID, you'll need it in Step 4.

## Step 3 — Turn your two Lambda functions into Python tools

Open `lambda/get_weather/lambda_function.py` and
`lambda/get_top_attractions/lambda_function.py` from your original exercise
files. Copy the logic inside each `lambda_handler` into a plain Python
function, and decorate it with `@tool`. The decorator reads your type hints
and docstring to build the tool definition automatically — no separate
"parameters" configuration screen needed.

Create `tools.py`:

```python
from strands import tool

MOCK_WEATHER = {
    "london": {
        "condition": "Light rain in the morning, clearing to partly cloudy by afternoon",
        "temperature_celsius": 11,
        "wind_mph": 12,
        "recommendation": "Bring a light jacket and umbrella for the morning",
    },
    "paris": {
        "condition": "Mostly sunny with light clouds",
        "temperature_celsius": 14,
        "wind_mph": 8,
        "recommendation": "Great day to be outdoors",
    },
    "new york": {
        "condition": "Clear skies, cold",
        "temperature_celsius": 5,
        "wind_mph": 15,
        "recommendation": "Dress warmly, especially in the wind",
    },
}

MOCK_ATTRACTIONS = {
    "london": [
        {"name": "British Museum", "type": "indoor", "family_friendly": True, "avg_visit_hours": 2},
        {"name": "Tower of London", "type": "outdoor/indoor", "family_friendly": True, "avg_visit_hours": 2.5},
        {"name": "Natural History Museum", "type": "indoor", "family_friendly": True, "avg_visit_hours": 2},
        {"name": "Hyde Park", "type": "outdoor", "family_friendly": True, "avg_visit_hours": 1.5},
        {"name": "Covent Garden", "type": "outdoor/indoor", "family_friendly": True, "avg_visit_hours": 1},
    ],
    "paris": [
        {"name": "Louvre Museum", "type": "indoor", "family_friendly": True, "avg_visit_hours": 3},
        {"name": "Eiffel Tower", "type": "outdoor/indoor", "family_friendly": True, "avg_visit_hours": 2},
        {"name": "Musée d'Orsay", "type": "indoor", "family_friendly": True, "avg_visit_hours": 2},
        {"name": "Luxembourg Gardens", "type": "outdoor", "family_friendly": True, "avg_visit_hours": 1.5},
        {"name": "Notre-Dame Cathedral", "type": "outdoor/indoor", "family_friendly": True, "avg_visit_hours": 1},
    ],
    "new york": [
        {"name": "Central Park", "type": "outdoor", "family_friendly": True, "avg_visit_hours": 2},
        {"name": "American Museum of Natural History", "type": "indoor", "family_friendly": True, "avg_visit_hours": 2.5},
        {"name": "The Metropolitan Museum of Art", "type": "indoor", "family_friendly": True, "avg_visit_hours": 3},
        {"name": "High Line", "type": "outdoor", "family_friendly": True, "avg_visit_hours": 1.5},
        {"name": "Brooklyn Bridge", "type": "outdoor", "family_friendly": True, "avg_visit_hours": 1},
    ],
}


@tool
def get_weather(city: str, date: str) -> dict:
    """Get the weather forecast for a city on a given date.

    Args:
        city: The city name, e.g. "London"
        date: The date in YYYY-MM-DD format
    """
    key = city.lower()
    if key not in MOCK_WEATHER:
        return {"error": f"Unknown city: '{city.title()}'. Supported cities are: London, Paris, New York."}
    result = dict(MOCK_WEATHER[key])  # copy so we don't mutate the shared dict
    result["city"] = city.title()
    result["date"] = date
    return result


@tool
def get_top_attractions(city: str) -> dict:
    """Get the top tourist attractions for a city.

    Args:
        city: The city name, e.g. "London"
    """
    key = city.lower()
    if key not in MOCK_ATTRACTIONS:
        return {"error": f"Unknown city: '{city.title()}'. Supported cities are: London, Paris, New York."}
    return {"city": city.title(), "attractions": MOCK_ATTRACTIONS[key]}
```

**What changed from your Lambda code, and why:**
- Removed the `event`/`context` parameters and the `parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}` line — that was unpacking Bedrock Agents' action-group payload format. A `@tool` function receives its arguments directly as normal Python parameters (`city`, `date`), so that unpacking step is gone.
- Removed the `messageVersion` / `response` / `functionResponse` wrapper — that was the response envelope Bedrock Agents required. A `@tool` function just returns a plain Python dict; Strands handles turning that into whatever the model needs.
- Removed `import json` and `json.dumps(result)` — no longer needed since you're not manually building a JSON string inside a wrapper; you just return the dict.
- Added `dict(MOCK_WEATHER[key])` instead of mutating `MOCK_WEATHER[key]` directly — your original code was fine for a one-shot Lambda invocation, but here the agent runs in a long-lived process, so mutating the shared `MOCK_WEATHER` dict in place would leak `city`/`date` from one call into the next lookup. Copying first avoids that.
- Both your `city.lower()` / `city.title()` logic and your "Unknown city" error message carried over unchanged — that logic wasn't Lambda-specific, so there was nothing to convert.

## Step 4 — Build the agent

Create `agent.py` in the same folder:

```python
from strands import Agent
from strands.models import BedrockModel
from tools import get_weather, get_top_attractions

AGENT_INSTRUCTION = """You are a helpful travel planning assistant. When a
user asks for travel recommendations, always use the available tools to
gather current weather conditions and top attractions before making any
suggestions. Always look up available attractions using a tool call. If the
weather is poor, prioritize indoor attractions. Always tailor suggestions to
any preferences the user mentions, such as traveling with family or having
limited time."""

model = BedrockModel(
    model_id="amazon.nova-pro-v1:0"  # or your Claude model ID from Step 2
)

agent = Agent(
    model=model,
    system_prompt=AGENT_INSTRUCTION,
    tools=[get_weather, get_top_attractions],
)

if __name__ == "__main__":
    response = agent("I'll be in London this Saturday with my family. What should we do?")
    print(response)
```

## Step 5 — Test locally

```bash
python agent.py
```

**Expected**, same as the original exercise: the agent should call
`get_weather` and `get_top_attractions` before answering, and the final
response should reference the weather and filter toward family-friendly
options. You'll see the tool calls logged in the terminal output as the
agent runs — this is your replacement for the console's **Test** panel.

If it responds without calling the tools, tighten the docstrings on your
`@tool` functions — the model decides whether to call a tool based on the
docstring and parameter descriptions, so vague ones get skipped.

Your mock data only covers London, Paris, and New York — testing with any
other city will correctly return the "Unknown city" error from both tools,
which is useful for confirming the agent surfaces tool errors instead of
inventing an answer.

## Step 6 (optional) — Deploy to AgentCore Runtime

The steps above satisfy "build and test an agent with tools" — the core of
the original exercise. If your assignment also asks you to *deploy* it
(the cloud equivalent of clicking **Save and exit** on a Bedrock Agent),
wrap the agent as an HTTP service and deploy it:

```python
# Add to the bottom of agent.py, replacing the __main__ block:
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "")
    response = agent(user_message)
    return {"result": str(response)}

if __name__ == "__main__":
    app.run()
```

Then deploy with the starter toolkit CLI:

```bash
agentcore configure --entrypoint agent.py
agentcore launch
```

This provisions a serverless AgentCore Runtime and gives you an endpoint
you can invoke the same way you'd have invoked a prepared Bedrock Agent.

**Heads-up:** AWS has been actively changing the AgentCore tooling — as of
mid-2026 there are reports of a newer CDK-based CLI (`@aws/agentcore-cli`)
starting to replace this starter-toolkit CLI in some docs. If
`agentcore configure` or `agentcore launch` doesn't work as shown, check
the current tutorial at
`docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html`
for the up-to-date command names — the local testing in Steps 1–5 will work
regardless of which CLI version is current.

---

## What you can drop from the original instructions

- Skip the Lambda console entirely (Step 1 of the original doc) — your
  functions now live in `tools.py` and run in-process.
- Skip creating action groups (Step 3 of the original doc) — the `@tool`
  decorator replaces that configuration.
- Skip **Prepare** — there's no separate build step; running the script
  *is* the test.
