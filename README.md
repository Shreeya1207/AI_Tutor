# 🧠 Socratic Multimodal Tutor

An AI-powered mathematics tutor that uses the **Socratic learning method** to guide students toward solving problems instead of directly revealing the final answer.

The student can provide a mathematics problem, including an image of a handwritten or printed problem, and interact with the tutor through a step-by-step conversation.

## 🚀 Features

- 📷 **Multimodal Problem Input** — Understand mathematics problems provided through images.
- 🧠 **Socratic Tutoring** — Guides students using questions and hints rather than immediately providing the solution.
- 💡 **Step-by-Step Guidance** — Breaks complex problems into smaller reasoning steps.
- 🔍 **Reasoning Checks** — Evaluates the student's response and determines what guidance is needed next.
- 🎯 **Adaptive Hints** — Provides progressively helpful hints when the student is stuck.
- 📚 **Conceptual Learning** — Focuses on understanding the reasoning behind the solution rather than answer memorization.

## 🏗️ How It Works

```text
              Student
                 │
                 ▼
        Problem / Image Input
                 │
                 ▼
        Multimodal AI Processing
                 │
                 ▼
          Socratic Engine
        ┌────────┼─────────┐
        │        │         │
        ▼        ▼         ▼
     Reasoning  Hint    Question
       Check   Generation Strategy
        │        │         │
        └────────┼─────────┘
                 ▼
          Guided Response
                 │
                 ▼
              Student
                 │
                 └──────► Next Step
```

Instead of:

```text
Problem → AI → Final Answer
```

the system aims for:

```text
Problem → AI → Question → Student Reasoning
                  ↓
               Hint
                  ↓
          Student Reasoning
                  ↓
             Next Question
                  ↓
             Final Answer
```

## 🛠️ Tech Stack

### Backend
- **Python**
- **FastAPI**
- REST API architecture

### AI
- **OpenRouter**
- Large Language Model for problem understanding and tutoring
- Multimodal input processing

### Frontend
- HTML
- CSS
- JavaScript

### Development
- Git & GitHub
- VS Code

## 🔄 Core Interaction Flow

1. The student uploads or enters a mathematics problem.
2. The backend receives the request through an API endpoint.
3. The problem is processed by the AI model.
4. The Socratic tutoring instructions control how the model responds.
5. Instead of directly revealing the answer, the tutor asks a guiding question.
6. The student submits their reasoning.
7. The system evaluates the response.
8. The tutor provides feedback, a hint, or the next guiding question.
9. The cycle continues until the student reaches the solution.

## 🎯 Example

### Traditional AI Tutor

```text
Student:
"What is the final answer?"

AI:
"The answer is 20."
```

### Socratic Tutor

```text
Student:
"What is the final answer?"

Tutor:
"Let's work it out together.
First, is the root node a MAX node or a MIN node?"
```

The goal is to make the **student perform the reasoning**, rather than making the AI perform the entire problem for them.

## 📁 Project Structure

```text
socratic-multimodal-tutor/
│
├── backend/
│   ├── ...
│   └── ...
│
├── frontend/
│   ├── ...
│   └── ...
│
├── requirements.txt
├── .gitignore
└── README.md
```

> The exact structure may vary as the project evolves.

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
```

**Never commit your `.env` file or API keys to GitHub.**

### 5. Start the backend

Use the project's configured FastAPI startup command.

For example:

```bash
uvicorn main:app --reload
```

## 🔐 Security

API credentials are stored using environment variables and should not be committed to the repository.

The `.gitignore` file excludes sensitive configuration files such as `.env`.

## 🔮 Future Improvements

- Persistent student learning history
- Personalized difficulty progression
- Better misconception detection
- Subject expansion beyond mathematics
- Voice-based interaction
- More advanced multimodal inputs
- Student performance analytics
- Redis-based session/state management
- Authentication and user profiles
- Deployment to a cloud platform

## 💡 Vision

Most AI educational tools optimize for **getting the answer**.

Socratic Multimodal Tutor aims to optimize for **understanding how to get the answer**.

> **Don't just give the student the answer. Teach them how to think.**

---

## 👤 Project

Built as a solo hackathon project.
