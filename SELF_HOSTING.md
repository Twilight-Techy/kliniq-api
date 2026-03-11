# 🚀 Self-Hosting the Kliniq API

This guide provides step-by-step instructions for getting the Kliniq backend running on your own infrastructure. We recommend **Render** for a smooth deployment experience.

## 📋 Prerequisites

- **Python**: 3.12.8 (Pinned via `.python-version`)
- **Database**: PostgreSQL 15+
- **Git**: For version control
- **Accounts**: GitHub, Render, and optionally [Google AI Studio](https://aistudio.google.com/) (for Gemini) or [Modal](https://modal.com) (for N-ATLaS).

---

## 🛠️ Local Development Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/kliniq-api.git
    cd kliniq-api
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Copy the template file and fill in your details:
    ```bash
    cp .env.example .env
    ```

5.  **Run Migrations**:
    Ensure your local Postgres is running, then applies the schema:
    ```bash
    alembic upgrade head
    ```

6.  **Start Server**:
    ```bash
    uvicorn src.main:app --reload
    ```

---

## ☁️ Deploying to Render

### 1. Database Setup
- Create a new **PostgreSQL** instance on Render.
- Copy the **Internal Database URL**.

### 2. Web Service Deployment
- Create a new **Web Service** on Render connected to your fork.
- **Runtime**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn -k uvicorn.workers.UvicornWorker src.main:app`

### 3. Required Environment Variables
Add these in the Render "Environment" tab:
- `DATABASE_URL`: Your Postgres URL.
- `LLM_PROVIDER`: `gemini` (default) or `natlas`.
- `GOOGLE_API_KEY`: Required if using Gemini.
- `JWT_SECRET`: A secure random string for authentication.
- `ALLOWED_ORIGINS`: Comma-separated list of permitted frontend URLs (e.g., `https://your-ui.vercel.app`).
- `RENDER_EXTERNAL_URL`: Your service's public URL (to enable the Self-Ping feature).

---

## 🤖 LLM Provider Configuration

### Option A: Google Gemini (Recommended)
- **Settings**: `LLM_PROVIDER=gemini`
- **Requirement**: A valid `GOOGLE_API_KEY`.
- **Pros**: Fast, highly reliable tool-calling, and extremely easy to set up.

### Option B: N-ATLaS (Specialist)
- **Settings**: `LLM_PROVIDER=natlas`
- **Requirement**: Modal deployment or access to existing N-ATLaS endpoints.
- **Endpoints**:
    - `MODAL_ENDPOINT_URL`: The inference endpoint.
    - `MODAL_ASR_URL`: The transcription endpoint.

---

## 💡 Pro-Tips

- **Keep-Alive**: The API includes a background task (`src/common/utils/self_ping.py`) that pings itself every 14 minutes. This prevents Render from spinning down your free instance.
- **Security**: Never commit your `.env` file. We have updated `.gitignore` to protect your credentials while allowing `.env.example` to be shared.

Happy Coding! 🏥🚀
