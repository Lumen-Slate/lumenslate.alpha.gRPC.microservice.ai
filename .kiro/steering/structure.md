# Project Structure

## Root Level Organization

- **app/**: Main application code
- **config/**: Empty directory (configuration is in app/config/)
- **venv/**: Python virtual environment (ignored in git)
- **requirements.txt**: Python dependencies
- **Dockerfile**: Container configuration
- **setup_database.py**: PostgreSQL database setup script
- **service.yaml**: Knative/Cloud Run deployment configuration

## Application Structure (`app/`)

### Core Components

- **grpc_server.py**: Main gRPC server entry point
- **protos/**: Protocol Buffer definitions
  - `ai_service.proto`: Service and message definitions
  - Generated Python files for gRPC
- **grpc_generated/**: Auto-generated gRPC Python code

### Business Logic

- **agents/**: AI agent implementations
  - `root_agent/`: Main conversational agent
  - `sub_agents/`: Specialized agents (assessor, assignment generators, report card)
- **logic/**: Core business logic modules
  - Context generation, question segmentation
  - Variable detection and randomization
  - MCQ/MSQ variation generators
- **services/**: gRPC service implementations
- **api/**: API handlers and routing

### Data Layer

- **models/**: Data models
  - `sqlite/models.py`: SQLAlchemy ORM models
  - `pydantic/models.py`: Request/response validation models
- **data/**: Static data files and documentation

### Configuration & Utilities

- **config/**: Application configuration
  - `config.py`: Main configuration loader
  - `logging_config.py`: Logging setup
  - `settings/`: Environment-specific configs (dev, test, prod)
- **utils/**: Utility functions and helpers
  - Database population, content handling
  - Authentication, multimodal processing
- **prompts/**: AI prompt templates for different services

## Naming Conventions

### Files & Directories
- **Snake_case**: All Python files and directories
- **Descriptive names**: `question_segmentation.py`, `mcq_variation_generator.py`
- **Agent pattern**: Agent classes in dedicated directories with `agent.py`

### Database Models
- **PascalCase**: Model class names (`UnalteredHistory`, `Questions`)
- **Enums**: Uppercase values (`Role.USER`, `Subject.MATH`)
- **Table names**: Snake_case (`unaltered_history`, `subject_report`)

### gRPC Services
- **PascalCase**: Service and message names (`AIService`, `AgentRequest`)
- **Descriptive methods**: `GenerateContext`, `DetectVariables`

## Key Patterns

### Agent Architecture
- Root agent delegates to specialized sub-agents
- Each agent has dedicated directory with `__init__.py` and `agent.py`
- Agents use dependency injection via `ServiceFactory`

### Configuration Management
- Environment-based configuration selection
- Pydantic settings for validation
- `.env` files for local development

### Database Access
- SQLAlchemy ORM with declarative models
- Automatic table creation on startup
- Support for both SQLite (dev) and PostgreSQL (prod)

### Error Handling
- Structured logging with different levels per component
- Graceful shutdown handling for gRPC server
- Health check endpoints when available