# 🤖 AI Automation System

An AI-powered customer-support and business-automation portfolio project built with **Python, FastAPI, Groq LLM, Retrieval-Augmented Generation (RAG), FAISS, SQLAlchemy, Streamlit, and n8n**.

The system is designed to classify customer requests, retrieve relevant knowledge-base information, support order/refund workflows, handle escalations, send notifications, and expose APIs for external integrations.

## 🚀 Demo

**[🌐 Open Live Streamlit Demo](YOUR_STREAMLIT_DEMO_URL)**




## 🚀 Features

- AI-powered customer-intent classification
- Customer-support automation
- Order-status workflow
- Refund-request workflow
- Human-escalation workflow
- RAG-based knowledge retrieval
- FAQ knowledge base
- PDF, Markdown, and text document support
- FAISS vector similarity search
- Sentence Transformer embeddings
- Email notifications and webhook integrations
- SQLAlchemy database layer
- FastAPI REST API
- Streamlit monitoring dashboard
- n8n workflow integration
- Input validation and AI guardrails
- Structured logging
- Automated tests with `pytest`

## 🏗️ Architecture

```text
Customer
   |
   v
n8n / External Client
   |
   v
FastAPI
   |
   v
AI Intent Classifier
   |
   +------------------+-------------------+
   |                  |                   |
   v                  v                   v
RAG System        Workflow Router      Escalation
   |                  |                   |
   v                  v                   v
FAISS Vector      Business Workflows   Human Review
Store                 |
                      +--------+--------+
                      |        |        |
                      v        v        v
                   Database   Email   Webhooks
```

## 📁 Project Structure

```text
ai-automation-system/
├── main.py
├── config.py
├── api/
│   ├── routes.py
│   └── webhooks.py
├── ai/
│   ├── classifier.py
│   ├── generator.py
│   ├── prompts.py
│   └── guardrails.py
├── automation/
│   ├── router.py
│   ├── order_workflow.py
│   ├── refund_workflow.py
│   ├── escalation.py
│   └── notification.py
├── rag/
│   ├── loader.py
│   ├── embeddings.py
│   ├── retriever.py
│   └── vectorstore.py
├── integrations/
│   ├── order_api.py
│   ├── email.py
│   └── webhook.py
├── database/
│   ├── database.py
│   ├── models.py
│   └── repository.py
├── utils/
│   ├── logger.py
│   ├── validators.py
│   └── exceptions.py
├── data/
│   ├── faq/
│   └── documents/
├── workflows/
│   └── n8n/
├── tests/
├── dashboard/
│   └── streamlit_app.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| FastAPI | REST API |
| Groq | LLM inference |
| Sentence Transformers | Text embeddings |
| FAISS | Vector similarity search |
| RAG | Knowledge-grounded responses |
| SQLAlchemy | Database ORM |
| SQLite | Development database |
| Streamlit | Monitoring dashboard |
| n8n | Workflow automation |
| pytest | Testing |
| Docker | Containerization |
| GitHub Actions | Continuous integration |

## ⚙️ Setup and Installation

### 1. Prerequisites

- Python 3.11 or 3.12 (use a version supported by your dependencies)
- Git
- A Groq API key if you use the Groq-powered LLM
- Docker Desktop only if you plan to use Docker

### 2. Clone the repository

Replace the example URL with your actual GitHub repository URL.

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd ai-automation-system
```

If the project is already on your computer, open PowerShell in the project folder and continue.

### 3. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run this in the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

Create `.env` from `.env.example`.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Open `.env` and use the exact variable names expected by `config.py`. For example, if your project uses these names:

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
LLM_MODEL=your_supported_groq_model
```

Use a valid model supported by your provider and the configuration in your project. Never add real API keys to the README or commit `.env` to GitHub.

### 6. Add knowledge-base documents

Put FAQ and document files in the configured folders, for example:

```text
data/faq/
data/documents/
```

Check `rag/loader.py` and `rag/vectorstore.py` for supported formats and the actual ingestion procedure. If a separate command is needed to build the FAISS index, run it before testing RAG queries.

### 7. Run the application

Use the command matching the entry point implemented in your project.

**FastAPI** (if `main.py` exposes an ASGI object named `app`):

```powershell
uvicorn main:app --reload
```

**Streamlit dashboard:**

```powershell
streamlit run dashboard/streamlit_app.py
```

Streamlit prints its local URL in the terminal. FastAPI commonly runs at `http://127.0.0.1:8000`; interactive docs are commonly available at `http://127.0.0.1:8000/docs` when enabled.

> If your actual dashboard path or FastAPI entry point differs, update the command to match your code.

## 🧠 RAG Pipeline

```text
Documents
   ↓
Document Loader
   ↓
Text Processing
   ↓
Embeddings
   ↓
FAISS Vector Store
   ↓
Similarity Search
   ↓
Relevant Context
   ↓
LLM
   ↓
Grounded Response
```

Knowledge sources may be stored in `data/faq/` and `data/documents/`.

## 🔄 Automation Workflows

### Order workflow

```text
Customer Request → Intent Classification → Order ID Validation
→ Order Lookup → Order Information → Customer Response
→ Optional Email Notification
```

### Refund workflow

```text
Refund Request → Order Validation → Eligibility Check
→ Refund Request Creation → Notification → Customer Update
```

### Escalation workflow

```text
Customer Issue → AI / Rule Detection → Priority Assignment
→ Support Notification → Human Review
```

## 🔗 n8n Integration

Workflow exports can be stored in `workflows/n8n/`. Import the relevant JSON files into n8n and configure API URLs, credentials, and webhook settings for your environment. Never commit webhook secrets or credentials.

## 🗄️ Database

The project uses SQLAlchemy for database operations and lists SQLite as the development database. Models may include customers, orders, refund requests, escalations, and automation logs, depending on the implemented schema.

## 🧪 Testing

Activate the virtual environment and run:

**All tests:**

```powershell
python -m pytest tests/ -v
```

**AI tests:**

```powershell
python -m pytest tests/test_ai.py -v
```

**RAG tests:**

```powershell
python -m pytest tests/test_rag.py -v
```

**API tests:**

```powershell
python -m pytest tests/test_api.py -v
```

**Workflow tests:**

```powershell
python -m pytest tests/test_workflows.py -v
```

Some tests may require environment variables or external services. Check the relevant modules if a test needs additional setup.

## 🐳 Docker

If the Docker configuration matches your application entry points:

```bash
docker build -t ai-automation-system .
docker compose up --build
```

Review `Dockerfile` and `docker-compose.yml` for expected ports, commands, environment variables, and services.

## 🛡️ Guardrails and Security

The project describes checks such as input validation, message-length validation, prompt-injection detection, intent validation, confidence thresholds, response validation, required-data validation, error handling, and human escalation.

The AI should not invent order information, refund decisions, delivery dates, company policies, or payment information.

**Security checklist:**
- Keep `.env` out of version control.
- Never commit API keys, database credentials, SMTP passwords, webhook secrets, or sensitive customer data.
- Use `.env.example` for placeholder variable names only.
- Configure authentication, authorization, rate limiting, and secret management before production use.

## 📈 Future Improvements

Potential next steps include production authentication and authorization, rate limiting, Redis caching, PostgreSQL support, improved observability, RAG evaluation, document-chunking improvements, automated vector-store ingestion, real order-management API integration, production-grade refund API integration, role-based access control, expanded CI/CD, and cloud deployment.

## 👨‍💻 Project Purpose

This portfolio project demonstrates practical work with Python backend development, LLM integration, RAG, vector search, API development, workflow automation, external integrations, database design, testing, monitoring, AI guardrails, and containerization.

## 📄 License

This project states that it is licensed under the MIT License. See the `LICENSE` file for details.

See the `LICENSE` file for details.