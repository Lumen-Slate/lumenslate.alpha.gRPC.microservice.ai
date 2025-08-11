# Technology Stack

## Core Technologies

- **Python 3.12**: Primary language with Alpine Linux base
- **gRPC**: All API endpoints (no REST APIs)
- **Protocol Buffers**: Message serialization via `.proto` files
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and settings management
- **Google Generative AI**: Gemini 2.5 Flash Lite model integration

## Database

- **Development**: SQLite (`my_agent_data.db`)
- **Production**: PostgreSQL (via `DATABASE_URL`)
- **Migrations**: SQLAlchemy declarative models with automatic table creation

## Key Dependencies

- `google-genai`: Google AI integration
- `grpcio` & `grpcio-tools`: gRPC server and tooling
- `sqlalchemy`: Database ORM
- `pydantic-settings`: Configuration management
- `python-dotenv`: Environment variable loading

## Environment Configuration

Environment-specific settings in `app/config/settings/`:
- `dev.py`: Development configuration
- `test.py`: Testing configuration  
- `prod.py`: Production configuration

Required environment variables:
- `GOOGLE_API_KEY`: Google AI API key
- `DATABASE_URL`: PostgreSQL connection string (production)
- `GOOGLE_PROJECT_ID`: GCP project identifier
- `GOOGLE_CLOUD_LOCATION`: GCP region (default: us-central1)

## Common Commands

### Development Setup
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
```

### Database Setup
```bash
python setup_database.py  # PostgreSQL setup
python app/utils/populate_questions.py  # Seed questions
```

### Running Services
```bash
python -m app.grpc_server  # Start gRPC server (port 50051 or $PORT)
```

### Protocol Buffer Generation
```bash
python -m grpc_tools.protoc --proto_path=app/protos --python_out=app/grpc_generated --grpc_python_out=app/grpc_generated app/protos/ai_service.proto
```

## Deployment

- **Container**: Docker with Python 3.12 Alpine
- **Cloud**: Google Cloud Run (Knative service)
- **Port**: Uses `$PORT` environment variable (defaults to 50051)
- **Health Checks**: gRPC health checking service when available