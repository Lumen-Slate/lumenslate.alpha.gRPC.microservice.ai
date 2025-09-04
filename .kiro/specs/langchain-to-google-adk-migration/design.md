# Design Document

## Overview

This design outlines the migration of 7 independent agents from LangChain to Google Agent Development Kit (ADK). The migration will replace LangChain's `ChatGoogleGenerativeAI` and related components with Google ADK's native agent framework while preserving all existing functionality, interfaces, and structured output capabilities.

The current independent agents use LangChain for prompt templating, message handling, and structured output generation. Google ADK provides equivalent capabilities through its agent framework, with better integration with Google's AI services and improved performance characteristics.

## Architecture

### Current Architecture (LangChain-based)

```
Independent Agent
├── LangChain Components
│   ├── ChatGoogleGenerativeAI (model interface)
│   ├── PromptTemplate (prompt formatting)
│   ├── HumanMessage (message wrapping)
│   └── structured_output (Pydantic model binding)
├── Prompt Templates (separate .py files)
├── Pydantic Models (request/response validation)
└── Agent Function (main logic)
```

### Target Architecture (Google ADK-based)

```
Independent Agent
├── Google ADK Components
│   ├── Agent (core agent instance)
│   ├── Model (Gemini 2.5 Flash Lite)
│   ├── generate_content (content generation)
│   └── structured_output (JSON schema validation)
├── Prompt Templates (preserved structure)
├── Pydantic Models (unchanged)
└── Agent Function (updated implementation)
```

### Migration Strategy

1. **Direct Replacement**: Replace LangChain imports with Google ADK equivalents
2. **Interface Preservation**: Maintain existing function signatures and return types
3. **Structured Output**: Use Google ADK's JSON schema generation from Pydantic models
4. **Configuration Reuse**: Leverage existing environment variables and configuration patterns

## Components and Interfaces

### Core Migration Components

#### 1. Model Initialization
**Current (LangChain)**:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
structured_llm = llm.with_structured_output(ResponseModel)
```

**Target (Google ADK)**:
```python
import google.genai as genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
model = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    config=types.GenerateContentConfig(
        response_schema=ResponseModel.model_json_schema()
    )
)
```

#### 2. Prompt Processing
**Current (LangChain)**:
```python
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

prompt_template = PromptTemplate.from_template(template=PROMPT)
formatted_prompt = prompt_template.format(**kwargs)
message = HumanMessage(content=formatted_prompt)
response = llm.invoke([message])
```

**Target (Google ADK)**:
```python
# Prompt templates remain the same
formatted_prompt = PROMPT.format(**kwargs)
response = model.generate_content(
    contents=[types.Content(parts=[types.Part.from_text(formatted_prompt)])]
)
```

#### 3. Structured Output Handling
**Current (LangChain)**:
```python
structured_llm = llm.with_structured_output(ResponseModel)
response = structured_llm.invoke([message])
return response  # Already a Pydantic model
```

**Target (Google ADK)**:
```python
response = model.generate_content(
    contents=[...],
    config=types.GenerateContentConfig(
        response_schema=ResponseModel.model_json_schema()
    )
)
return ResponseModel.model_validate_json(response.text)
```

### Agent-Specific Interfaces

#### 1. Context Generator
- **Input**: `ContextRequest(question: str, keywords: list[str], language: str)`
- **Output**: `str` (generated context)
- **Migration**: Direct string response, no structured output needed

#### 2. Variable Detector
- **Input**: `VariableDetectorRequest(question: str)`
- **Output**: `VariableDetectorResponse` with structured Variable objects
- **Migration**: Requires JSON schema generation for structured output

#### 3. MCQ/MSQ Variation Generators
- **Input**: Question, options, answer index
- **Output**: Structured variations with MCQQuestion/MSQQuestion objects
- **Migration**: Complex structured output with nested lists

#### 4. Question Segment Generator
- **Input**: Question text
- **Output**: Segmented question parts
- **Migration**: Structured output for question segments

#### 5. Variable Randomizer
- **Input**: Variables and randomization parameters
- **Output**: Randomized variable values
- **Migration**: Structured output for variable mappings

#### 6. Assignment Generator General
- **Input**: Assignment parameters
- **Output**: Generated assignment content
- **Migration**: String or structured assignment format

## Data Models

### Preserved Pydantic Models

All existing Pydantic models will be preserved without modification:

- `ContextRequest`
- `VariableDetectorRequest`, `VariableDetectorResponse`, `Variable`
- `MCQRequest`, `MCQVariation`, `MCQQuestion`
- `MSQRequest`, `MSQVariation`, `MSQQuestion`
- Additional models for other agents

### JSON Schema Generation

Google ADK requires JSON schemas for structured output. These will be generated automatically from Pydantic models using:

```python
schema = ResponseModel.model_json_schema()
```

### Response Validation

Responses from Google ADK will be validated against Pydantic models:

```python
validated_response = ResponseModel.model_validate_json(response.text)
```

## Error Handling

### Migration Strategy

1. **Preserve Error Types**: Maintain same exception types and error messages
2. **Google ADK Error Mapping**: Map Google ADK exceptions to equivalent LangChain errors where needed
3. **Graceful Degradation**: Handle API failures with same fallback behavior
4. **Validation Errors**: Maintain Pydantic validation error handling

### Error Scenarios

- **API Key Issues**: Same environment variable validation
- **Model Unavailable**: Same error handling as current LangChain implementation
- **Structured Output Failures**: JSON parsing and validation error handling
- **Rate Limiting**: Preserve existing retry logic if any

## Testing Strategy

### Unit Testing Approach

1. **Function-Level Tests**: Test each agent function with same inputs/outputs
2. **Mock Google ADK**: Create mocks for Google ADK client and model responses
3. **Structured Output Validation**: Test JSON schema generation and response parsing
4. **Error Condition Testing**: Verify error handling matches LangChain behavior

### Integration Testing

1. **End-to-End Agent Testing**: Test complete agent workflows
2. **gRPC Service Integration**: Verify agents work with existing gRPC endpoints
3. **Performance Benchmarking**: Compare response times with LangChain implementation
4. **Structured Output Validation**: Test complex nested response structures

### Test Data Strategy

1. **Preserve Test Cases**: Use same test inputs and expected outputs
2. **Add ADK-Specific Tests**: Test Google ADK-specific features and error conditions
3. **Schema Validation Tests**: Test JSON schema generation and validation
4. **Performance Tests**: Measure and compare performance metrics

## Implementation Phases

### Phase 1: Foundation Setup
- Update dependencies in requirements.txt
- Create Google ADK client initialization utilities
- Implement JSON schema generation helpers
- Set up testing framework for Google ADK

### Phase 2: Simple Agents Migration
- Migrate context_generator (string output only)
- Migrate assignment_generator_general (simple structured output)
- Validate basic functionality and performance

### Phase 3: Complex Structured Output Agents
- Migrate variable_detector (complex structured output)
- Migrate mcq_variation_generator and msq_variation_generator
- Implement and test nested JSON schema handling

### Phase 4: Remaining Agents
- Migrate question_segment_generator
- Migrate variable_randomizer
- Complete integration testing

### Phase 5: Cleanup and Optimization
- Remove LangChain dependencies
- Optimize Google ADK configurations
- Performance tuning and final validation

## Configuration Management

### Environment Variables
- Reuse existing `GOOGLE_API_KEY`
- Leverage existing `GOOGLE_PROJECT_ID` and `GOOGLE_CLOUD_LOCATION`
- Maintain compatibility with current configuration patterns

### Model Configuration
- Use same model: "gemini-2.5-flash-lite"
- Preserve temperature settings where applicable
- Maintain existing timeout and retry configurations

### Deployment Considerations
- Docker container updates for new dependencies
- Google Cloud Run compatibility verification
- Health check endpoint updates if needed