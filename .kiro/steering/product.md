# LumenSlate AI Microservice

LumenSlate is an AI-powered educational microservice designed for intelligent educational applications. It provides session-based interactions, assignment generation, and multiple AI-powered endpoints using Google's Gemini 2.5 Flash Lite model.

## Core Features

- **Root Agent**: Contextual AI conversations using Google Generative AI
- **Session Management**: SQLite/PostgreSQL-based session storage with conversation history
- **Educational Content**: Pre-seeded database with 150+ MCQs across English, Math, Science, History & Geography
- **Content Generation**: Context generation, question segmentation, and variable detection
- **Authentication**: Firebase Authentication middleware
- **gRPC-Only Architecture**: All endpoints exposed via gRPC protocol

## Key Capabilities

- Assignment generation (general and tailored)
- Assessment and report card generation
- MCQ/MSQ variation generation
- Variable detection and randomization
- RAG (Retrieval-Augmented Generation) with corpus management
- Multi-subject educational content support

## Target Users

Educational platforms, teachers, and educational content creators who need AI-powered assignment generation, assessment tools, and intelligent tutoring capabilities.