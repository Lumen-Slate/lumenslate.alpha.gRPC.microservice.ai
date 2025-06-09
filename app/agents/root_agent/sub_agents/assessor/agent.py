from google.adk.agents import Agent

assessor = Agent(
    name="assessor",
    model="gemini-2.0-flash",
    description="dummy agent",
    instruction="""
    dummy agent
    """,
)
