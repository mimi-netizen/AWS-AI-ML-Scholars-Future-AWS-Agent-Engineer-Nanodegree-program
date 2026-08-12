# Restaurant Recommendation Agent — Built on Amazon Bedrock AgentCore

This exercise asks you to build a restaurant recommendation agent using
Amazon Bedrock Agents — a console-based, action-group-and-Lambda service
that has since been retired. This guide builds the equivalent agent using
AgentCore instead: a code-first approach where you write the agent and its
tools directly in Python using the Strands Agents SDK, then optionally
deploy that code to AgentCore Runtime.

Your three Lambda functions become three Python functions, your agent
instruction becomes a system prompt, and the CloudFormation deploy step
disappears entirely — there's nothing to provision in AWS just to get a
working agent.

---

## Concept mapping (old → new)

| Bedrock Agents (old) | AgentCore (new) |
|---|---|
| `template.yaml` CloudFormation deploy | Not needed — no Lambda to provision |
| Agent created in console | `strands.Agent` object in Python |
| "Agent instruction" field | `system_prompt` string |
| Action Group + Lambda (`get-cuisines`) | `@tool` function `get_cuisines` |
| Action Group + Lambda (`search-restaurants`) | `@tool` function `search_restaurants` |
| Action Group + Lambda (`get-availability`) | `@tool` function `get_availability` |
| Underscore-vs-hyphen warning in function names | Not applicable — Python function names are already valid identifiers |
| **Prepare** button | Not needed |
| Console **Test** panel | Run the Python script locally |

---

## Step 1 — Set up your project

```bash
mkdir restaurant-agentcore
cd restaurant-agentcore
python3 -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

pip install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit boto3
```

## Step 2 — Enable model access and configure AWS credentials

In the [Amazon Bedrock console](https://console.aws.amazon.com/bedrock), go
to **Model access** and confirm you have access to Amazon Nova Pro (the
model the original exercise specifies).

Configure your AWS credentials if you haven't already:

```bash
aws configure
```

You'll need an Access Key ID, Secret Access Key, and default region (get
these from the IAM console, or from your course-provided lab credentials if
you're working in a sandbox account). Confirm it worked:

```bash
aws sts get-caller-identity
```

You should get back a JSON block with your account details.

**Note on model invocation:** some Bedrock models, including Nova Pro,
can't be invoked directly by their bare model ID anymore — you need a
cross-region inference profile instead. Confirm the correct profile ID for
your region before writing `agent.py`:

```bash
aws bedrock list-inference-profiles --region <your-region> --query "inferenceProfileSummaries[?contains(inferenceProfileId, 'nova-pro')].inferenceProfileId"
```

This typically returns something like `us.amazon.nova-pro-v1:0` — use
whatever it actually prints, not a guessed value.

## Step 3 — Write the three tools

Create `tools.py`, using your actual Lambda logic ported into plain Python
functions:

```python
from strands import tool

RESTAURANTS = [
    {"id": "r1", "name": "Trattoria Bella", "cuisine": "Italian",  "rating": 4.6},
    {"id": "r2", "name": "Osteria Romana",  "cuisine": "Italian",  "rating": 4.4},
    {"id": "r3", "name": "Sakura Garden",   "cuisine": "Japanese", "rating": 4.7},
    {"id": "r4", "name": "Ramen Yuki",      "cuisine": "Japanese", "rating": 4.9},
    {"id": "r5", "name": "El Mercado",      "cuisine": "Mexican",  "rating": 4.3},
    {"id": "r6", "name": "Spice Route",     "cuisine": "Indian",   "rating": 4.6},
    {"id": "r7", "name": "Le Bistro",       "cuisine": "French",   "rating": 4.8},
    {"id": "r8", "name": "The Grill House", "cuisine": "American", "rating": 4.2},
]

AVAILABILITY = {
    "r1": True,
    "r2": False,
    "r3": True,
    "r4": False,
    "r5": True,
    "r6": True,
    "r7": False,
    "r8": True,
}


@tool
def get_cuisines() -> dict:
    """Return the list of cuisine types available."""
    cuisines = sorted(set(r["cuisine"] for r in RESTAURANTS))
    return {"cuisines": cuisines}


@tool
def search_restaurants(cuisine: str = "") -> dict:
    """Search for restaurants. Returns all restaurants if no cuisine is specified.

    Args:
        cuisine: The cuisine type to filter by (e.g. "Italian", "Japanese").
            Leave empty to return all restaurants.
    """
    cuisine = cuisine.lower()
    if cuisine:
        restaurants = [r for r in RESTAURANTS if r["cuisine"].lower() == cuisine]
        if not restaurants:
            return {"error": f"No {cuisine.title()} restaurants found."}
        return {"restaurants": restaurants}
    return {"restaurants": RESTAURANTS}


@tool
def get_availability(restaurant_id: str) -> dict:
    """Check whether a specific restaurant has availability for tonight.

    Args:
        restaurant_id: The unique ID of the restaurant.
    """
    available = AVAILABILITY.get(restaurant_id, False)
    return {"restaurant_id": restaurant_id, "available": available}
```

This is a direct port of the original Lambda logic — same data, same field
names (`available`, not `available_tonight`), same behavior. Two details
carried over deliberately, not accidentally:

- **`get_availability` never errors.** An unknown `restaurant_id` silently
  returns `{"available": False}` instead of an explicit error, unlike
  `search_restaurants`, which does return an error for an unmatched
  cuisine. A typo'd ID looks identical to a real, fully-booked restaurant.
  This asymmetry exists in the original Lambda logic — it's preserved here
  rather than "fixed," since matching the specified tool behavior is
  presumably what's being evaluated.
- **Two Italian restaurants exist**, one available (`r1`, Trattoria Bella)
  and one not (`r2`, Osteria Romana). This makes "find me an Italian
  restaurant" a genuine multi-step tool-chaining test: the agent has to
  search, get two results back, and check availability on at least one of
  them — ideally both — before it can recommend correctly. A shallow
  implementation will just recommend whichever restaurant came back first
  from the search, without checking if it's actually free.

## Step 4 — Build the agent

Create `agent.py`. The system prompt is the single most important part of
this exercise — it needs to leave the model no room to skip a tool call or
recommend an unconfirmed restaurant:

```python
from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import get_cuisines, search_restaurants, get_availability

AGENT_INSTRUCTION = """You are a restaurant recommendation assistant. You
must use the available tools before making any recommendation — do not
answer from your own knowledge or assumptions. When a user asks for a
restaurant recommendation, search for restaurants matching their request,
then check get_availability for each candidate restaurant returned by the
search — a cuisine can match more than one restaurant, and not all of them
will be available. Only recommend a restaurant you have explicitly
confirmed is available tonight via get_availability; if the first match
isn't available, check the next one before giving up. If no matching
restaurant is available, say so explicitly rather than recommending an
unavailable one or inventing an alternative. Base your final answer only on
what the tools actually returned."""

model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0"  # use the inference profile ID from Step 2
)

agent = Agent(
    model=model,
    system_prompt=AGENT_INSTRUCTION,
    tools=[get_cuisines, search_restaurants, get_availability],
)

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "")
    response = agent(user_message)
    return {"result": str(response)}

if __name__ == "__main__":
    app.run()
```

A vague instruction like "use the tools before responding" tends to let
the model rationalize its way out of a tool call it doesn't think it needs
("I already know Italian restaurants exist, so I'll just answer") — this
system prompt is written to close that gap explicitly, including the
specific failure case of stopping at the first search result without
checking whether it's actually available.

## Step 5 — Test locally

Create a separate `test_local.py` so you can run quick checks without
starting the AgentCore server each time:

```python
from agent import agent

response = agent("Find me an Italian restaurant for tonight.")
print(response)
```

Run it:

```bash
python test_local.py
```

**Expected:** the agent should call `search_restaurants` (filtered to
Italian, returning both Trattoria Bella and Osteria Romana), then call
`get_availability` on at least one of them — ideally both, since Osteria
Romana (`r2`) is not available and Trattoria Bella (`r1`) is — before
recommending Trattoria Bella specifically. This is the real test of
whether the system prompt is doing its job: a weaker prompt will often
just recommend whichever restaurant came back first from the search
without checking if it's actually free tonight.

### Test more than the one example prompt

A single passing prompt doesn't prove the agent is reliably grounded in
tool output rather than getting lucky. Worth trying a range of cases:

```python
test_prompts = [
    "Find me an Italian restaurant for tonight.",
    "What cuisines are available?",
    "Find me a restaurant for tonight, I don't care about cuisine.",
    "Is Trattoria Bella available tonight?",  # tests name-to-ID resolution, see below
    "Find me a Thai restaurant.",  # no Thai in the data — tests honest failure
]
for prompt in test_prompts:
    print(f"\n--- {prompt} ---")
    print(agent(prompt))
```

**Two things specifically worth watching for:**

- **Name-to-ID resolution.** `get_availability` only accepts `restaurant_id`
  (`r1`, `r2`, etc.), not a name. If a user asks "Is Trattoria Bella
  available?", the model has to call `search_restaurants` first to find
  that Trattoria Bella is `r1`, then call `get_availability("r1")`. Watch
  the tool-call log to confirm it does this rather than guessing an ID.
- **Honest failure on an unmatched cuisine.** "Thai" isn't in the data, so
  `search_restaurants` will correctly return
  `{"error": "No Thai restaurants found."}`. The agent should relay that
  plainly, not invent a Thai restaurant or silently substitute a different
  cuisine.

## Step 6 (optional) — Deploy to AgentCore Runtime

The steps above satisfy "build and test an agent with tools" — the core of
the exercise. If your assignment also requires deployment, wrap and deploy
with the starter toolkit CLI:

```bash
agentcore configure --entrypoint agent.py
agentcore deploy
```

(Some versions of the CLI use `launch` instead of `deploy` — try whichever
command the CLI itself suggests after `configure` completes.)

**Heads-up for sandbox/lab AWS accounts:** deployment provisions real AWS
resources — an ECR repository, an IAM execution role, and a CodeBuild
project to build the container image. Locked-down lab accounts (common in
course environments) often restrict IAM role creation or CodeBuild access
specifically, even when they allow everything needed for local testing. If
`agentcore deploy` fails with an `AccessDeniedException`, that's an account
permissions boundary, not a bug in your code — check with your course
provider whether cloud deployment is actually required, or whether a
working local agent satisfies the exercise.

If a deploy attempt partially succeeds before failing, clean up what it did
create:

```bash
aws ecr delete-repository --repository-name <repo-name> --region <region> --force
aws iam list-attached-role-policies --role-name <role-name>   # then detach-role-policy for each
aws iam list-role-policies --role-name <role-name>             # then delete-role-policy for each
aws iam delete-role --role-name <role-name>
```

(IAM roles can't be deleted while policies are still attached — detach or
delete those first.)

---

## What to submit as your deliverable

Per the exercise's requirements:
- **Your agent instruction prompt** — that's the `AGENT_INSTRUCTION` string
  in Step 4.
- **A screenshot or copy of the chat history showing the agent using the
  tools** — that's your terminal output from Step 5. Strands prints tool
  invocations as they happen, which satisfies this requirement without
  needing the Bedrock console's chat view.

## What you can skip from the original console-based instructions

- Skip the CloudFormation deploy step entirely — nothing to provision.
- Skip the underscore/hyphen naming warning — not applicable to Python
  function names.
- Skip **Prepare** — there's no separate build step; running the script
  *is* the test.
- Skip `aws cloudformation delete-stack` in cleanup — there's no stack,
  since no Lambda functions were ever created in AWS. If you did deploy via
  `agentcore deploy` for Step 6, use the ECR/IAM cleanup commands above
  instead.
