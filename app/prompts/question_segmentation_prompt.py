

QUESTION_SEGMENTATION_PROMPT = """
You are a helpful assistant that segments questions into smaller parts.
Your task is to take a question and break it down into its component parts.
For example, if the question is "What is the capital of France and what is its population?",
you would break it down into two parts: "What is the capital of France?" and "What is its population?".

Please segment the following question into smaller parts in part a, b, c, etc. format.

Question: {question}

Return the new segmented question in your response only
"""
