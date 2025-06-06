from google.adk.agents import Agent

assignment_generator_tailored = Agent(
    name="assignment_generator_tailored",
    model="gemini-2.0-flash",
    description="this tells a fruits joke",
    instruction="""
    generate a fruits joke
    """,
)