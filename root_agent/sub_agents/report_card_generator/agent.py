from google.adk.agents import Agent

report_card_generator = Agent(
    name="report_card_generator",
    model="gemini-2.0-flash",
    description="this generates delhi jokes",
    instruction="""
    just tell a scienc joke
    """,
)