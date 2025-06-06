from google.adk.agents import Agent

assessor = Agent(
    name="assessor",
    model="gemini-2.0-flash",
    description="this generates a football joke",
    instruction="""
    generate a football joke
    """,
)
