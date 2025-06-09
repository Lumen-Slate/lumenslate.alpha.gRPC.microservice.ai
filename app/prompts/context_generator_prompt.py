

CONTEXT_GENEATOR_PROMPT = """
Your task is to take and analyze a given question and provide a context for it, basically create a real life scenario around the question so that it is relatable to students. The context should be a short paragraph that sets the stage for the question, making it easier for students to understand and relate to the problem at hand.
The context should be relevant to the question and interesting to the students and should not be too long. The context should be in a single paragraph and should not exceed 5 sentences. The context should be in {language} language and should be easy to understand for students.
If the question has variables and their numeric values then they are strictly not to be changed in the generation process.

Note: No markdown, bullets or formatting to be used. Return only the new question with context.

Question : {question}

Keywords : {keywords}

Form the context around these keywords.
"""