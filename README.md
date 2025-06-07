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

| Method | Endpoint | Description                     |
| ------ | -------- | ------------------------------- |
| GET    | `/ping`  | Returns `{ "message": "ping" }` |

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