<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Modal-AI-FF6B6B?style=for-the-badge" alt="Modal"/>
</p>

# 🏥 Kliniq API

**Backend API for AI-Powered Multilingual Healthcare Platform**

> *Powering intelligent healthcare with N-ATLaS — our custom multilingual AI model for Nigerian languages and medical contexts.*

---

## 🌟 Overview

**Kliniq API** is a production-ready FastAPI backend that powers the Kliniq healthcare platform. It provides secure, scalable APIs for:

- 🤖 **AI-powered symptom triage** with N-ATLaS multilingual model
- 🎤 **Voice transcription and translation** across 4 Nigerian languages
- 👥 **Patient and clinician management** with role-based access
- 🏥 **Hospital integration** and appointment scheduling
- 📊 **Real-time health analytics** and medical records

---

## 🧠 N-ATLaS: The AI Engine

At the heart of Kliniq is **N-ATLaS** (Nigerian-Adapted Translation and Language System), a custom AI model deployed on Modal cloud infrastructure:

### Capabilities

| Feature | Description |
|---------|-------------|
| 🗣️ **Multilingual Chat** | Fluent in English, Hausa, Igbo, and Yoruba |
| 🩺 **Medical Triage** | Symptom assessment with urgency classification |
| 🔧 **Tool Calling** | Structured function calls for appointments and triage creation |
| 📝 **Context Awareness** | Incorporates patient history, doctor notes, and appointments |
| 🔄 **Translation** | Seamless translation between all supported languages |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Kliniq Frontend                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Kliniq API (FastAPI)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Dashboard  │  │  Clinician  │  │   Messages Module   │  │
│  │   Module    │  │   Module    │  │   (Voice + Text)    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          ▼                                   │
│              ┌───────────────────────┐                       │
│              │     LLM Service       │                       │
│              │  (N-ATLaS Interface)  │                       │
│              └───────────┬───────────┘                       │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │   Modal Cloud GPU     │
              │   (N-ATLaS Model)     │
              └───────────────────────┘
```

---

## 🔗 API Modules

### 🔐 Authentication (`/auth`)
- JWT-based authentication with refresh tokens
- Email verification and password reset
- Role-based access control (Patient, Nurse, Doctor)

### 📊 Patient Dashboard (`/dashboard`)
- Personal health dashboard data
- AI chat with conversation history
- Hospital linking via codes
- Medical notes and vitals tracking

### 👩‍⚕️ Clinician Portal (`/clinician`)
- Nurse/Doctor dashboard with statistics
- Patient list with triage status
- Detailed patient profiles with AI analysis
- Appointment request management
- Gamification with points system

### 💬 Messages (`/messages`)
- Real-time messaging between patients and clinicians
- Voice message support with transcription
- Multi-language translation

### 🏥 Appointments (`/appointments`)
- Appointment scheduling and management
- Calendar integration
- Automated reminders

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Framework** | FastAPI 0.115 |
| **Database** | PostgreSQL 15 + SQLAlchemy 2.0 |
| **Async** | asyncpg, aiohttp |
| **Authentication** | PyJWT, bcrypt, passlib |
| **AI/LLM** | Modal (GPU cloud), Custom N-ATLaS model |
| **Validation** | Pydantic 2.10 |
| **Migrations** | Alembic |
| **Email** | aiosmtplib |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Modal account (for AI features)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/kliniq-api.git
cd kliniq-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/kliniq

# JWT Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (optional)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@kliniq.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Modal AI Endpoint
MODAL_ENDPOINT_URL=https://your-modal-endpoint.modal.run/generate
```

### Database Setup

```bash
# Create database
createdb kliniq

# Run migrations
alembic upgrade head

# Seed test data (optional)
python -m scripts.seed_test_data
```

### Run Development Server

```bash
uvicorn src.main:app --reload --port 8001
```

API documentation available at:
- **Swagger UI**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **ReDoc**: [http://localhost:8001/redoc](http://localhost:8001/redoc)

---

## 📂 Project Structure

```
kliniq-api/
├── src/
│   ├── main.py              # FastAPI application entry
│   ├── auth/                # Authentication module
│   │   ├── dependencies.py  # Auth dependencies
│   │   └── auth_controller.py
│   ├── common/
│   │   ├── database/        # Database configuration
│   │   └── llm/             # N-ATLaS LLM service
│   │       ├── llm_service.py
│   │       ├── modal_app.py # Modal deployment
│   │       └── tool_executor.py
│   ├── models/
│   │   └── models.py        # SQLAlchemy models
│   ├── modules/
│   │   ├── dashboard/       # Patient dashboard
│   │   ├── clinician/       # Clinician portal
│   │   ├── messages/        # Messaging system
│   │   └── appointments/    # Appointment management
│   └── router/
│       └── routers.py       # API router aggregation
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
└── requirements.txt
```

---

## 🔑 Key Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user |

### Patient Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Get dashboard data |
| POST | `/dashboard/chat` | Send AI chat message |
| GET | `/dashboard/chat/history` | Get chat history |
| POST | `/dashboard/hospitals/link` | Link to hospital |

### Clinician Portal
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/clinician` | Get clinician dashboard |
| GET | `/clinician/patients` | List patients |
| GET | `/clinician/patient/{id}` | Patient detail with AI analysis |
| GET | `/clinician/requests` | Get appointment requests |
| POST | `/clinician/requests/{id}/approve` | Approve request |
| GET | `/clinician/doctors/{hospital_id}` | Get doctors by hospital |

---

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src
```

---

## 🏆 Hackathon Highlights

This API was built for **Awarri Developer Challenge 2025** demonstrating:

1. **AI Innovation** — Custom N-ATLaS model for Nigerian healthcare
2. **Production Quality** — Async architecture, proper error handling, migrations
3. **Security** — JWT auth, role-based access, input validation
4. **Scalability** — Modular design, cloud AI deployment on Modal
5. **Real Impact** — Solving language barriers in Nigerian healthcare

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with ❤️ for Nigerian Healthcare</strong>
</p>
