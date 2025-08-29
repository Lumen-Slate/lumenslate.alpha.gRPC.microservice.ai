VARIABLE_RANDOMIZER_PROMPT = """
Your task is to extract filters and values for variables from the given question and user-defined prompt. Each variable may have one of the following filters:

1. **Range**: A range is provided as [min, max].
2. **Options**: A list of possible values is provided.

If no filter is explicitly mentioned for a variable, leave the filters empty.

Here is an example:

User Prompt: "randomize width between 14 to 63 and length should be 4,78 or 90"

Question: "Calculate the area of a rectangle with width 5 and length 15"


Based on the above example, the output is a list of dictionaries where each dictionary contains the variable name and its associated filters. if any variable is not present in the question but is given in user prompt, it should be ignored.

User Prompt: {userPrompt}

Question: {question}

Output:
"""
