# 🚀 Self-Hosting the Kliniq API

So you want to run your own version of the Kliniq backend? Awesome! Here's a beginner-friendly guide to getting it up and running on **Render**.

### 1. Prerequisites
- A [GitHub](https://github.com) account.
- A [Render](https://render.com) account.
- A [Google AI Studio](https://aistudio.google.com/) API Key (for Gemini).

### 2. Database Setup (PostgreSQL)
1. In Render, click **New** -> **PostgreSQL**.
2. Give it a name (e.g., `kliniq-db`).
3. Click **Create Database**.
4. Once it's created, copy the **Internal Database URL** (or External if you want to connect from your local machine).

### 3. Deploying the API
1. Fork this repository to your GitHub.
2. In Render, click **New** -> **Web Service**.
3. Connect your forked repository.
4. **Environment:** `Python`
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `gunicorn -k uvicorn.workers.UvicornWorker src.main:app`
   - *Note: We've already added `gunicorn` to the requirements for you.*

### 4. Important Environment Variables
Click on **Environment** in Render and add these:
- `DATABASE_URL`: Your PostgreSQL URL.
- `LLM_PROVIDER`: `gemini` (Standard) or `natlas` (Specialist).
- `GOOGLE_API_KEY`: Your Gemini API key.
- `SECRET_KEY`: A random long string for security.
- `RENDER_EXTERNAL_URL`: The URL Render gives you for this service.
- `ALLOWED_ORIGINS`: Your Vercel URL (e.g., `https://your-ui.vercel.app`).

### 5. Switching to N-ATLaS (The Specialist Route)
If you want to use the custom Nigerian-adapted model:
1. Sign up for [Modal](https://modal.com).
2. Deploy the code in `src/common/llm/modal_app.py` to your Modal account.
3. Update your Render variables:
   - `LLM_PROVIDER=natlas`
   - `MODAL_ENDPOINT_URL=https://your-modal-app.modal.run/generate`

### 💡 Pro-Tip: The "Self-Ping"
We've included a script (`src/common/utils/self_ping.py`) that pings your API every 14 minutes. This keeps your Render "Free" instance awake so users don't have to wait for it to wake up!

Happy coding! 🏥
