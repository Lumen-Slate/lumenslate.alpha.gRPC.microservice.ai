# 📘 LumenSlate AI Microservice

A FastAPI-based microservice that powers an intelligent educational agent. It supports session-based conversations, assignment generation, and a seeded SQLite question database.

---

## 🚀 Features

- 🧠 Root Agent using `google.generativeai`
- 🗂️ Session storage via SQLite
- 📚 Question database with 150+ MCQs across English, Math, Science, History & Geography
- 🛠️ Question seeding script with difficulty levels
- 🔐 Firebase Authentication middleware
- 🌐 CORS support for frontend integration

---

## 🗂 Project Structure

```
.
├── app/
│   ├── agents/             # Root agent logic
│   ├── models/
│   │   ├── sqlite/         # SQLAlchemy models
│   │   └── pydantic/       # Pydantic schemas
|   |── data/               # Database storage (ignored in .git)
│   ├── utils/              # Utility scripts (e.g., populate\_questions.py)
│   └── main.py             # FastAPI entry point
├── requirements.txt
└── README.md
````

---

## 🧪 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
````

### 2. Run API Server

```bash
uvicorn main:api --reload
```

> API will be available at: `http://127.0.0.1:8000`

---

### 3. Populate the Question Database

```bash
python app/utils/populate_questions.py
```

> Seeds `my_agent_data.db` with 150 questions in 5 subjects, evenly distributed across 3 difficulty levels.

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_api_key_here
```

---

## 📦 Notes

* SQLite database file (`my_agent_data.db`) is **excluded** from Git (see `.gitignore`)
* You can regenerate the DB anytime using the seeding script
* Sessions and questions are stored in the same SQLite DB for simplicity

---

## 📜 License

MIT License