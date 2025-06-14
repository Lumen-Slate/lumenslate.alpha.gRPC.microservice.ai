from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import random

from app.prompts.variable_randomizer_prompt import VARIABLE_RANDOMIZER_PROMPT


# Define the request model


class FilterAndRandomizerRequest(BaseModel):
    question: str = Field(description="The question to analyze for variables.")
    userPrompt: str = Field(
        description="The user-defined prompt for extracting filters.")

# Define the structure for each variable


class VariableFilter(BaseModel):
    range: Optional[List[int]] = Field(
        description="The range filter as [min, max].", default=None)
    options: Optional[List[Union[int, str]]] = Field(
        description="The options filter as a list of possible values.", default=None)


class Variable(BaseModel):
    name: str = Field(description="The name of the variable.")
    value: Optional[Union[int, str]] = Field(
        description="The current value of the variable.")
    filters: VariableFilter = Field(
        description="The filters applied to the variable.")

# Define the response model


class FilterAndRandomizerResponse(BaseModel):
    variables: List[Variable] = Field(
        description="List of variables with their filters and values.")


# Initialize the LLM with structured output
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.75)
structured_llm = llm.with_structured_output(FilterAndRandomizerResponse)

# Create a prompt template
prompt_template = PromptTemplate.from_template(
    template=VARIABLE_RANDOMIZER_PROMPT)


def extract_and_randomize_logic(question: str, user_prompt: str) -> FilterAndRandomizerResponse:
    """
    Core logic for extracting filters and randomizing variables.

    Args:
        question (str): The question to analyze for variables.
        user_prompt (str): The user-defined prompt for extracting filters.

    Returns:
        FilterAndRandomizerResponse: A JSON object containing the variables with randomized values.
    """
    # Format the prompt using the question and user prompt
    formatted_prompt = prompt_template.format(
        question=question, userPrompt=user_prompt
    )
    # Create a HumanMessage with the formatted prompt
    message = HumanMessage(content=formatted_prompt)
    # Invoke the LLM with structured output
    response = structured_llm.invoke([message])

    randomized_variables = []
    for variable in response.variables:
        name = variable.name
        # Ensure filters is present, else use default
        filters = variable.filters if hasattr(variable, "filters") and variable.filters is not None else VariableFilter()
        randomized_value = None

        if filters.range:
            min_val, max_val = filters.range
            randomized_value = random.randint(min_val, max_val)
        elif filters.options:
            randomized_value = random.choice(filters.options)
        else:
            randomized_value = variable.value

        randomized_variables.append(Variable(
            name=name,
            value=randomized_value,
            filters=filters
        ))

    return FilterAndRandomizerResponse(variables=randomized_variables)
