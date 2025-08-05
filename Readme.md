# 📘 LumenSlate AI Microservice

An AI microservice designed for intelligent educational applications. It supports session-based interactions, assignment generation, and multiple AI-powered endpoints using gemini-2.5-flash-lite.

---

## 🚀 Features

- 🧠 Root Agent using `google.generativeai` for contextual AI conversations
- 🗂️ Session storage via SQLite
- 📚 Pre-seeded database with 150+ MCQs across English, Math, Science, History & Geography
- 🛠️ Context generation, question segmentation, and variable detection via gemini-2.5-flash-lite
- 🔐 Firebase Authentication middleware
- 📁 Structured project layout for scalability
- 📜 Environment-based config for `dev`, `test`, `prod`
- 🛰️ **Supports gRPC endpoints only**

---

## 🗂 Project Structure

```

.
├── app/
│   ├── agents/
│   │   ├── requirements.txt
│   │   └── root_agent/
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       └── sub_agents/
│   │           ├── assessor/
│   │           │   ├── __init__.py
│   │           │   └── agent.py
│   │           ├── assignment_generator_general/
│   │           │   ├── __init__.py
│   │           │   └── agent.py
│   │           ├── assignment_generator_tailored/
│   │           │   ├── __init__.py
│   │           │   └── agent.py
│   │           └── report_card_generator/
│   │               ├── __init__.py
│   │               └── agent.py
│   ├── api/
│   │   └── primary_agent_handler.py
│   ├── data/
│   │   └── README.txt
│   ├── grpc_generated/
│   │   └── app/
│   │       └── protos/
│   │           ├── ai_service_pb2_grpc.py
│   │           └── ai_service_pb2.py
│   ├── logic/
│   │   ├── agent_service.py
│   │   ├── context_generator.py
│   │   ├── mcq_variation_generator.py
│   │   ├── msq_variation_generator.py
│   │   ├── question_segmentation.py
│   │   ├── variable_detector.py
│   │   └── variable_randomizer.py
│   ├── models/
│   │   ├── pydantic/
│   │   │   └── models.py
│   │   └── sqlite/
│   │       ├── __init__.py
│   │       └── models.py
│   ├── prompts/
│   │   ├── context_generator_prompt.py
│   │   ├── mcq_variation_generator_prompt.py
│   │   ├── msq_variation_generator_prompt.py
│   │   ├── question_segmentation_prompt.py
│   │   ├── variable_detector_prompt.py
│   │   └── variable_randomizer_prompt.py
│   ├── protos/
│   │   ├── ai_service_pb2_grpc.py
│   │   ├── ai_service_pb2.py
│   │   └── ai_service.proto
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── assessment_handler.py
│   │   ├── clean_text.py
│   │   ├── content_summarizer.py
│   │   ├── history_manager.py
│   │   ├── multimodal_handler.py
│   │   ├── populate_questions.py
│   │   ├── question_retriever.py
│   │   ├── report_card_tools.py
│   │   └── subject_handler.py
│   ├── services/
│   │   └── grpc_service.py
│   └── grpc_server.py
├── config/
│   ├── __init__.py
│   ├── config.py
│   ├── logging_config.py
│   └── settings/
│       ├── __init__.py
│       ├── dev.py
│       ├── prod.py
│       └── test.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── Lumen_Slate.postman_collection.json
├── service.yaml
├── start.py
└── README.md

```

---

## 🧪 Setup Instructions

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # For Unix
venv\Scripts\activate      # For Windows
```

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

## ▶️ Running the gRPC Server

```bash
python -m app.grpc_server
```

> gRPC endpoints are available as defined in `app/grpc_server.py`.

---

## 🧠 Populate the Question Database

```bash
python app/utils/populate_questions.py
```

> Seeds `my_agent_data.db` with 150+ MCQs (5 subjects, 3 difficulty levels).

---

## 🛰️ gRPC API Endpoints

The service exposes the following gRPC methods via the `AIService` service (see `app/protos/ai_service.proto`):

| Method                | Description                                      |
|-----------------------|--------------------------------------------------|
| GenerateContext       | Generates contextual passage                     |
| DetectVariables       | Identifies variables in a question               |
| SegmentQuestion       | Breaks a question into smaller parts             |
| GenerateMCQVariations | Creates MCQ variations                           |
| GenerateMSQVariations | Creates MSQ variations                           |
| FilterAndRandomize    | Extracts and randomizes variable filters         |
| Agent                 | Root AI agent for assignment/response generation |

> See the `.proto` file for message/request/response details.

---

## 📚 API Documentation

* The gRPC service and message definitions are in [`app/protos/ai_service.proto`](app/protos/ai_service.proto).
* Use tools like [grpcurl](https://github.com/fullstorydev/grpcurl) or [Postman gRPC](https://blog.postman.com/postman-supports-grpc/) for testing.

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