

MCQ_VARIATION_GENERATOR_PROMPT = """
Your task is to generate new unique variation of a given question alongwith its options and the correct answer index. You have to generate 4 variations of the question.
The variations should be similar in wording or structure but the entities in the questions and its options must be brand new.
The variations should be in the same language as the original question.
The variations should be grammatically correct and make sense in the context of the original question.
The variations should not be same as the original question.


Question: {question}
Options: {options}
Correct Answer Index: {answerIndex}

Below are some variation generation examples, that can be used only as a reference. Do not use them as a template for your own variations:

1.  Original: What is the capital of France?
    Variations:
    - What city is the capital of France?
    - Can you tell me the capital city of France?
    - Which city serves as the capital of France?
    - What is the name of France's capital city?

2.  Original: Find the are a of a circle with radius 5.
    Variations:
    - Calculate the area of a square with side length 5.
    - What is the perimeter of a rectangle with length 5 and width 10?
    - Determine the area of a triangle with base 5 and height 10.
    - What is the circumference of a circle with radius 5?

3.  Original: The battle of Gettysburg was fought in which year?
    Variations:
    - Who participated in the battle of Gettysburg?
    - Who won the battle of Gettysburg?
    - What was the outcome of the battle of Gettysburg?
    - What were the consequences of the battle of Gettysburg?

"""
