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