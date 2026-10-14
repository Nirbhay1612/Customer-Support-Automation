# 🤖 AI Automation System

An AI-powered customer support and business automation system built with **Python, FastAPI, Groq LLM, RAG, FAISS, SQLAlchemy, Streamlit, and n8n**.

The system can classify customer requests, retrieve information from a knowledge base, automate order and refund workflows, send notifications, handle escalations, and expose APIs for external integrations.

## 🚀 Streamlit App Demo

**[🌐 Open Live Streamlit Demo](YOUR_STREAMLIT_DEMO_URL)**




## 🚀 Features

- AI-powered customer intent classification
- Customer support automation
- Order status automation
- Refund request workflow
- Human escalation workflow
- RAG-based knowledge retrieval
- FAQ knowledge base
- PDF, Markdown, and text document support
- FAISS vector search
- Sentence Transformer embeddings
- Email notifications
- Webhook integrations
- SQLAlchemy database layer
- FastAPI REST API
- Streamlit monitoring dashboard
- n8n workflow integration
- Input validation and AI guardrails
- Structured logging
- Automated tests with pytest

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │      Customer       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      n8n / API      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI API     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    AI Classifier    │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
           ┌──────────┐  ┌──────────┐  ┌──────────┐
           │   RAG    │  │ Workflow │  │Escalation│
           │  System  │  │  Router  │  │  System  │
           └────┬─────┘  └────┬─────┘  └──────────┘
                │             │
                ▼             ▼
           ┌──────────┐  ┌──────────┐
           │  FAISS   │  │ Business │
           │ Vector DB│  │ Workflows│
           └──────────┘  └────┬─────┘
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                 Database   Email   Webhooks
```

---

## 📁 Project Structure

```text
ai-automation-system/
│
├── main.py
├── config.py
│
├── api/
│   ├── routes.py
│   └── webhooks.py
│
├── ai/
│   ├── classifier.py
│   ├── generator.py
│   ├── prompts.py
│   └── guardrails.py
│
├── automation/
│   ├── router.py
│   ├── order_workflow.py
│   ├── refund_workflow.py
│   ├── escalation.py
│   └── notification.py
│
├── rag/
│   ├── loader.py
│   ├── embeddings.py
│   ├── retriever.py
│   └── vectorstore.py
│
├── integrations/
│   ├── order_api.py
│   ├── email.py
│   └── webhook.py
│
├── database/
│   ├── database.py
│   ├── models.py
│   └── repository.py
│
├── utils/
│   ├── logger.py
│   ├── validators.py
│   └── exceptions.py
│
├── data/
│   ├── faq/
│   └── documents/
│
├── workflows/
│   └── n8n/
│       ├── customer_support.json
│       ├── refund.json
│       └── escalation.json
│
├── tests/
│   ├── test_ai.py
│   ├── test_rag.py
│   ├── test_api.py
│   └── test_workflows.py
│
├── dashboard/
│   └── streamlit_app.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 🛠️ Tech Stack

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) | Core development |
| [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) | REST API |
| [![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/) | LLM inference |
| [![Sentence Transformers](https://img.shields.io/badge/Sentence_Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://www.sbert.net/) | Text embeddings |
| [![FAISS](https://img.shields.io/badge/FAISS-0467DF?style=for-the-badge&logo=meta&logoColor=white)](https://github.com/facebookresearch/faiss) | Vector similarity search |
| [![RAG](https://img.shields.io/badge/RAG-6C47FF?style=for-the-badge&logo=databricks&logoColor=white)](https://www.ibm.com/think/topics/retrieval-augmented-generation) | Knowledge-grounded responses |
| [![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/) | Database ORM |
| [![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/) | Development database |
| [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/) | Monitoring dashboard |
| [![n8n](https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)](https://n8n.io/) | Workflow automation |
| [![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/) | Testing |
| [![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/) | Containerization |
| [![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://docs.github.com/en/actions) | Continuous integration |


## 📚 RAG Pipeline

The RAG system follows this flow:

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

Knowledge sources are stored in:

```text
data/faq/
data/documents/
```

---

## 🔄 Automation Workflows

### Order Workflow

```text
Customer Request
      ↓
Intent Classification
      ↓
Order ID Validation
      ↓
Order API
      ↓
Order Information
      ↓
Customer Response
      ↓
Optional Email Notification
```

### Refund Workflow

```text
Refund Request
      ↓
Validate Order
      ↓
Get Order Information
      ↓
Check Refund Eligibility
      ↓
Create Refund Request
      ↓
Notification
      ↓
Customer Update
```

### Escalation Workflow

```text
Customer Issue
      ↓
AI / Rule Detection
      ↓
Escalation
      ↓
Priority Assignment
      ↓
Support Notification
      ↓
Human Review
```

---

## 🔗 n8n Integration

n8n workflow exports are stored in:

```text
workflows/n8n/
```

Available workflows:

```text
customer_support.json
refund.json
escalation.json
```

These workflows can be imported into n8n and connected to the FastAPI backend.

---

## 🗄️ Database

The system uses SQLAlchemy for database operations.

**Current development database:** SQLite

Database models include:

- Customer
- Order
- RefundRequest
- Escalation
- AutomationLog

---

## 🧪 Testing

Run all tests:

```bash
python -m pytest tests/ -v
```

Run AI tests:

```bash
python -m pytest tests/test_ai.py -v
```

Run RAG tests:

```bash
python -m pytest tests/test_rag.py -v
```

Run API tests:

```bash
python -m pytest tests/test_api.py -v
```

Run workflow tests:

```bash
python -m pytest tests/test_workflows.py -v
```

---

## 🔁 Continuous Integration (CI)

GitHub Actions can automatically run the test suite when code is pushed or a pull request is opened.

The CI workflow helps catch regressions and verify that changes do not break existing tests.

---

## 🐳 Docker

Build the Docker image:

```bash
docker build -t ai-automation-system .
```

Run the container using the port and command configured for your application.

For Docker Compose, use:

```bash
docker compose up --build
```

*Ensure your Dockerfile and `docker-compose.yml` match the actual application entry points and required environment variables.*

---

## 🛡️ Guardrails

The system includes basic AI safety and reliability checks:

- Input validation
- Message length validation
- Prompt-injection detection
- Intent validation
- Confidence threshold validation
- AI response validation
- Required-data validation
- Human escalation
- Error handling

The AI should not invent:

- Order information
- Refund decisions
- Delivery dates
- Company policies
- Payment information

---

## 📈 Future Improvements

Planned improvements include:

- Production authentication and authorization
- Rate limiting
- Redis caching
- PostgreSQL support
- Better observability and metrics
- Advanced RAG evaluation
- Document chunking optimization
- Automated vector-store ingestion
- Real order-management API integration
- Production-grade refund API integration
- Role-based access control
- Improved Docker deployment
- Expanded CI/CD pipeline
- Cloud deployment

---

## 🔒 Security

Do not commit sensitive credentials.

The following should remain private:

```text
.env
API keys
Database credentials
SMTP passwords
Webhook secrets
Customer sensitive information
```

For production, configure authentication, authorization, rate limiting, secret management, and appropriate data-access controls.

---

## 👨‍💻 Project Purpose

This project demonstrates practical implementation of:

- Python backend development
- AI/LLM integration
- RAG systems
- Vector databases
- API development
- Workflow automation
- External integrations
- Database design
- Testing
- Monitoring
- AI guardrails
- Containerization and CI

It is designed as a portfolio project demonstrating how AI can be integrated into real-world customer-support and business automation workflows.

---

## 📄 License

This project is licensed under the MIT License.

See the `LICENSE` file for details.