# 🩺 AI Doctor Companion

An intelligent, interactive healthcare consultation assistant.

AI Doctor Companion allows users to **describe their symptoms**, **upload lab reports**, and engage in a **multi-turn, conversational diagnostic workflow**.
The AI doctor responds intelligently, asks follow-up questions, analyzes uploaded reports, and finally suggests an appropriate **direction, medical advice, or next recommended step**.


## Features

### **Multi-Turn Medical Conversation**

Users can chat naturally with the AI doctor.
The agent continues asking medically relevant follow-up questions until the required information is complete.

### **Lab Report Uploads**

Users can upload lab reports (PDF, images).
The system extracts text (OCR), parses medical values, and includes them in the conversation.

### **Intelligent Agentic Workflow (LangGraph)**

The core logic is built using **LangGraph**, enabling:

* stateful conversations
* branching logic
* tool-calling
* follow-up question loops
* structured decision-making

### **Gemini-Flash 2.5 Model**

Ultra-fast and powerful medical reasoning powered by the **Gemini Flash 2.5 LLM**.

### **FastAPI Backend**

The entire AI doctor is served through a **FastAPI API** and **WebSocket real-time chat**, supporting:

* multiple simultaneous users
* session-based memory
* persistent conversation state

## Tech Stack

| Layer                 | Technology                  |
| --------------------- | --------------------------- |
| **AI Model**          | Gemini Flash 2.5            |
| **Workflow Engine**   | LangGraph                   |
| **Web Server**        | FastAPI                     |
| **WebSocket Chat**    | FastAPI WebSockets          |
| **OCR / Lab Parsing** | Custom tools                |
| **Frontend**          | HTML/CSS/JS (or any client) |


## How It Works

### 1 User sends a symptom message

The system stores it and appends it to the conversation graph.

### 2 AI Doctor analyzes context

LangGraph determines whether:

* more questions are required
* lab data is needed
* or a summary/diagnosis can be generated

### 3 User uploads labs (optional)

OCR + medical parsing enriches the patient profile.

### 4 Final Recommendation

AI provides:

* probable conditions
* risk assessment
* suggested next medical step
* lifestyle guidance
* urgency level

## Running the App

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI server:

```bash
uvicorn main:app --reload
```

Open in browser:

```
http://localhost:8000
```

## Environment Variables

Create a `.env`:

```
GEMINI_API_KEY=your_key
```

## Goal of the Project

AI Doctor Companion aims to provide:

* accessible initial medical guidance
* symptom triaging
* lab interpretation
* safe, structured, responsible medical conversation
  This is **not a replacement** for a real doctor but a **supportive, AI-powered companion**.

