from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import get_weather, get_top_attractions

AGENT_INSTRUCTION = """You are a helpful travel planning assistant. You must
call BOTH the get_weather tool and the get_top_attractions tool for every
travel question before responding — this applies even if you believe you
already know the answer, the weather, or the attractions for a city. Do not
answer from your own knowledge, and do not claim you are unable to provide
weather or attraction information without first attempting to call the
corresponding tool. If a tool call fails or returns an error, say so
explicitly in your response rather than silently omitting that part of the
answer. If the weather is poor, prioritize indoor attractions. Always
tailor suggestions to any preferences the user mentions, such as traveling
with family, traveling with friends, or having limited time."""

model = BedrockModel(
    model_id="us.amazon.nova-pro-v1:0"
)

agent = Agent(
    model=model,
    system_prompt=AGENT_INSTRUCTION,
    tools=[get_weather, get_top_attractions],
)

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "")
    response = agent(user_message)
    return {"result": str(response)}

if __name__ == "__main__":
    app.run()