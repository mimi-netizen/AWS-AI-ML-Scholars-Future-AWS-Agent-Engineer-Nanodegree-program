import boto3

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

MODEL_ID = "amazon.nova-lite-v1:0"

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

# Task 1: System prompt.
SYSTEM_PROMPT = """\
You are a travel planning assistant that helps users plan visits to cities.

You must call the available tools before making any recommendation. Never
answer from memory or your own general knowledge of a city's weather or
attractions — even if you believe you already know the answer. For every
travel planning question, call get_weather and get_top_attractions for the
relevant city before responding, and base your recommendation only on what
those tools actually return.

If a tool returns no data for a city or date, say so explicitly rather than
filling in the gap with your own knowledge. If the weather is poor,
prioritize indoor attractions. Tailor your suggestions to any preferences
the user mentions, such as traveling with family, traveling with friends,
or having limited time.
"""

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------
WEATHER_DATA = {
    ("london", "2026-03-14"): {
        "city": "London",
        "date": "2026-03-14",
        "condition": "Light rain in the morning, clearing to partly cloudy by afternoon",
        "temperature_celsius": 11,
        "wind_mph": 12,
        "recommendation": "Bring a light jacket and umbrella for the morning",
    },
    ("london", "2026-03-15"): {
        "city": "London",
        "date": "2026-03-15",
        "condition": "Clear and sunny throughout the day",
        "temperature_celsius": 14,
        "wind_mph": 8,
        "recommendation": "Great day to spend time outdoors",
    },
}

ATTRACTIONS_DATA = {
    "london": {
        "city": "London",
        "attractions": [
            {"name": "British Museum",        "type": "indoor",          "family_friendly": True, "avg_visit_hours": 2.0},
            {"name": "Tower of London",       "type": "outdoor/indoor",  "family_friendly": True, "avg_visit_hours": 2.5},
            {"name": "Natural History Museum","type": "indoor",          "family_friendly": True, "avg_visit_hours": 2.0},
            {"name": "Hyde Park",             "type": "outdoor",         "family_friendly": True, "avg_visit_hours": 1.5},
            {"name": "Covent Garden",         "type": "outdoor/indoor",  "family_friendly": True,  "avg_visit_hours": 1.0},
            {"name": "The Comedy Store",      "type": "indoor",          "family_friendly": False, "avg_visit_hours": 2.0},
            {"name": "Soho Nightlife",        "type": "outdoor/indoor",  "family_friendly": False, "avg_visit_hours": 3.0},
            {"name": "Shoreditch Bar Crawl",  "type": "outdoor/indoor",  "family_friendly": False, "avg_visit_hours": 4.0},
        ],
    }
}

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "toolSpec": {
            "name": "get_weather",
            "description": "Returns current weather conditions and forecast for a given city and date.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        # Task 2: define the two input properties — city and date
                        "city": {
                            "type": "string",
                            "description": "The city to get weather for",
                        },
                        "date": {
                            "type": "string",
                            "description": "The date in YYYY-MM-DD format",
                        },
                    },
                    "required": ["city", "date"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_top_attractions",
            "description": "Returns a list of top-rated attractions in a given city.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        # Task 2: define the one input property — city
                        "city": {
                            "type": "string",
                            "description": "The city to get attractions for",
                        },
                    },
                    "required": ["city"],
                }
            },
        }
    },
]

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
def get_weather(city: str, date: str) -> dict:
    # Task 3: look up (city.lower(), date) in WEATHER_DATA.
    key = (city.lower(), date)
    if key in WEATHER_DATA:
        return WEATHER_DATA[key]
    return {"city": city, "date": date, "condition": "No data available"}


def get_top_attractions(city: str) -> dict:
    # Task 3: look up city.lower() in ATTRACTIONS_DATA.
    key = city.lower()
    if key in ATTRACTIONS_DATA:
        return ATTRACTIONS_DATA[key]
    return {"city": city, "attractions": []}


def execute_tool(name: str, tool_input: dict) -> dict:
    if name == "get_weather":
        return get_weather(tool_input["city"], tool_input["date"])
    elif name == "get_top_attractions":
        return get_top_attractions(tool_input["city"])
    return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Converse loop
# ---------------------------------------------------------------------------
def run_chat() -> None:
    messages = []

    print("Travel Planner")
    print("=" * 40)
    print("Ask me to help plan your visit to a city.\n")

    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not user_input:
        print("No input provided.")
        return

    messages.append({"role": "user", "content": [{"text": user_input}]})

    while True:
        response = bedrock.converse(
            modelId=MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": TOOLS},
        )

        stop_reason = response["stopReason"]
        output_message = response["output"]["message"]
        messages.append(output_message)

        if stop_reason == "end_turn":
            for block in output_message["content"]:
                if "text" in block:
                    print(f"\nAssistant: {block['text']}\n")
            break

        elif stop_reason == "tool_use":
            tool_results = []

            for block in output_message["content"]:
                if "toolUse" in block:
                    tool_name = block["toolUse"]["name"]
                    tool_input = block["toolUse"]["input"]
                    tool_use_id = block["toolUse"]["toolUseId"]

                    print(f"  [tool call] {tool_name}({tool_input})")
                    result = execute_tool(tool_name, tool_input)
                    print(f"  [tool result] {result}")

                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [{"json": result}],
                        }
                    })

            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run_chat()
