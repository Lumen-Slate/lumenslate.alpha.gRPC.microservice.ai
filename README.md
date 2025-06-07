# README.md

# AI Microservice

This is a simple AI microservice built with FastAPI.

## Features

- A single `/ping` endpoint that returns `{ "message": "ping" }`.
- Environment-based settings for `dev`, `test`, and `prod`.
- Logging configuration to track service events.
- Structured project directory for scalability.
- OpenAPI documentation available at `/docs` and `/redoc`.

## Installation

Please do create a python virtual enviornment first

```sh
pip install -r requirements.txt
```

## Running the Service

```sh
python main.py
```

## API Endpoints

Please import the endpoints on your postman desktop app, by importing Lumen_Slate.postman_collection.json

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET    | `/ping`  | Returns `{ "message": "pong" }` |
| POST   | `/generate-context` | Generates context using the Gemini-2.0-Flash model |
| POST   | `/generate-mcq-variations` | Generates variations of a given MCQ question using the Gemini-2.0-Flash model |
| POST   | `/generate-msq-variations` | Generates variations of a given MSQ question using the Gemini-2.0-Flash model |
| POST   | `/segment-question` | Segments a given question into smaller, meaningful parts using the Gemini-2.0-Flash model |
| POST   | `/detect-variables` | Identifies variables in a given question using the Gemini-2.0-Flash model |
| POST   | `/extract-and-randomize` | Extracts filters and values for variables from the question and user-defined prompt, then randomizes the variables |

## OpenAPI Documentation

Once the server is running, visit:

- [Swagger UI](http://127.0.0.1:8000/docs)
- [ReDoc UI](http://127.0.0.1:8000/redoc)

## Environment Variables

The service uses the following environment variable, ensure they are set in .env file:

- `GOOGLE_API_KEY`: API key required for accessing Gemini LLM used in the microservice.

## Logging

Logs are stored in `ai_microservice.log`.

## License

MIT