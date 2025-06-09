# 📘 LumenSlate AI Microservice

A FastAPI-based AI microservice designed for intelligent educational applications. It supports session-based interactions, assignment generation, and multiple AI-powered endpoints using Gemini-2.0-Flash.

---

## 🚀 Features

- 🧠 Root Agent using `google.generativeai` for contextual AI conversations
- 🗂️ Session storage via SQLite
- 📚 Pre-seeded database with 150+ MCQs across English, Math, Science, History & Geography
- 🛠️ Context generation, question segmentation, and variable detection via Gemini-2.0-Flash
- 🔐 Firebase Authentication middleware
- 🌐 CORS support for frontend integration
- 📊 OpenAPI documentation via Swagger & ReDoc
- 📁 Structured project layout for scalability
- 📜 Environment-based config for `dev`, `test`, `prod`

---

## 🗂 Project Structure

```

.
├── app/
│   ├── agents/             # Root agent logic
│   ├── models/
│   │   ├── sqlite/         # SQLAlchemy models
│   │   └── pydantic/       # Pydantic schemas
│   ├── data/               # Local DB storage (excluded from Git)
│   ├── routes/             # FastAPI endpoints
│   ├── utils/              # Utility functions and scripts
│   └── main.py             # FastAPI entrypoint
├── requirements.txt
├── Dockerfile
├── .env.example
├── Lumen\_Slate.postman\_collection.json
└── README.md

````

---

## 🧪 Setup Instructions

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # For Unix
venv\Scripts\activate      # For Windows
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Environment File

Copy the example file:

```bash
cp .env.example .env
```

Add your Gemini API key in `.env`:

```env
GOOGLE_API_KEY=your_api_key_here
```

---

## ▶️ Running the API

### Using Python

```bash
python main.py
```

### Using Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> API available at: [http://localhost:8000](http://localhost:8000)

---

## 🧠 Populate the Question Database

```bash
python app/utils/populate_questions.py
```

> Seeds `my_agent_data.db` with 150+ MCQs (5 subjects, 3 difficulty levels).

---

## 📨 API Endpoints

> Import the collection file: `Lumen_Slate.postman_collection.json` into Postman.

| Method | Endpoint                   | Description                                      |
| ------ | -------------------------- | ------------------------------------------------ |
| GET    | `/ping`                    | Health check: returns `{ "message": "pong" }`    |
| POST   | `/agent`                   | Root AI agent for assignment/response generation |
| POST   | `/generate-context`        | Generates contextual passage                     |
| POST   | `/generate-mcq-variations` | Creates MCQ variations                           |
| POST   | `/generate-msq-variations` | Creates MSQ variations                           |
| POST   | `/segment-question`        | Breaks a question into smaller parts             |
| POST   | `/detect-variables`        | Identifies variables in a question               |
| POST   | `/extract-and-randomize`   | Extracts and randomizes variable filters         |

---

## 📚 OpenAPI Documentation

* [Swagger UI](http://localhost:8000/docs)
* [ReDoc UI](http://localhost:8000/redoc)

---

## 📝 Logging

Logs are stored in:

```txt
ai_microservice.log
```

---

## 📦 Notes

* SQLite DB (`my_agent_data.db`) is ignored in Git
* DB can be regenerated anytime using the populate script
* Sessions and question data are stored in the same DB

---