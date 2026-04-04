# Git Agent

> Automating social media content generation from GitHub commit logs using AI.

## 🧠 Overview

The Git Agent is a Flask-based application designed to streamline the process of sharing daily coding progress on social media platforms. It automatically generates concise and engaging posts for Twitter/X, Facebook, and LinkedIn by analyzing GitHub commit logs. This project frees developers from the manual burden of content creation, allowing them to focus more on coding while consistently showcasing their work.

## 🔨 What I Built

This project delivers an intelligent agent capable of:

- **Automated Commit Analysis:** Fetches and processes GitHub commit history to extract key daily coding activities.
- **AI-Powered Content Generation:** Utilizes Google's Gemini LLM via Langchain to summarize commit data and compose platform-specific social media posts.
- **Multi-Platform Posting:** Seamlessly posts generated content to Twitter/X, LinkedIn, and includes a placeholder for Facebook.
- **Asynchronous Processing:** Employs RQ (Redis Queue) for background task execution, ensuring that webhook triggers and content generation are handled efficiently without blocking the main application.
- **Robust Workflow Management:** Leverages LangGraph to define and manage a stateful workflow for commit processing and content composition, with PostgreSQL checkpointing for resilience.
- **RESTful API:** Provides a comprehensive API for user management, post management, and authentication, secured with Flask-HTTPAuth for both basic and token-based access.

## 💭 Thought Process

I approached the problem of automating social media updates from commit logs by designing a modular Flask application. A key architectural decision was the use of Flask Blueprints to organize different functionalities like `agent_call`, `api`, `errors`, and `posting`, which promotes a clean and scalable codebase.

For the core logic of commit processing and content generation, I chose LangGraph to define a stateful workflow. This allows for a robust and traceable process, handling various stages from commit extraction to platform-specific content composition. Integrating `PostgresSaver` with LangGraph was crucial for ensuring the persistence of the graph's state, making the workflow resilient to interruptions and allowing for checkpointing.

Asynchronous processing was a critical consideration due to the nature of webhooks and potentially long-running LLM calls. RQ (Redis Queue) was implemented to offload these tasks, preventing the main Flask application from blocking and improving responsiveness.

The API design follows REST principles, providing clear endpoints for managing users and posts. Authentication is handled securely using Flask-HTTPAuth, supporting both basic authentication for token issuance and token-based authentication for subsequent API calls. Pydantic was incorporated to enforce structured outputs from the LLMs, which is vital for reliable parsing and content formatting. I also focused on comprehensive error handling across the API to provide consistent and informative feedback to clients.

## 🛠️ Tools & Tech Stack

| Layer          | Technology                    |
|----------------|-------------------------------|
| Language       | Python 3.x                    |
| Web Framework  | Flask                         |
| AI / LLM       | Google Gemini LLM (via Langchain) |
| Workflow       | LangGraph, Langchain          |
| Database       | PostgreSQL (Primary), SQLite (Fallback) |
| ORM            | Flask-SQLAlchemy              |
| Async Tasks    | RQ (Redis Queue), Redis       |
| Authentication | Flask-Login, Flask-HTTPAuth   |
| API Clients    | Requests, Requests-OAuthlib   |
| Data Handling  | Pandas, Pydantic              |
| Utilities      | python-dotenv, tenacity, Werkzeug, Psycopg |

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- A Google Gemini API Key
- A GitHub Personal Access Token
- Access to a PostgreSQL database
- A running Redis instance

### Installation

```bash
git clone https://github.com/rashadmin/git-agent.git
cd git-agent
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root directory and populate it with your credentials:

```env
DATABASE_URL="postgresql://user:password@host:port/database"
REDIS_URL="redis://localhost:6379/0" # Or your Redis connection string
GOOGLE_API_KEY="your_gemini_api_key"
GITHUB_TOKEN="your_github_personal_access_token"
SECRET_KEY="a_strong_secret_key_for_flask"
X_API_KEY="your_twitter_api_key"
X_API_SECRET="your_twitter_api_secret"
X_ACCESS_TOKEN="your_twitter_access_token"
X_ACCESS_TOKEN_SECRET="your_twitter_access_token_secret"
LINKEDIN_ACCESS_TOKEN="your_linkedin_access_token"
LINKEDIN_PERSON_URN="urn:li:person:YOUR_LINKEDIN_URN" # e.g., urn:li:person:123456789
```

### Run

**1. Initialize Database Migrations (first time setup):**

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

**2. Start the Flask Application:**

```bash
flask run
```
(For production, consider using a WSGI server like Gunicorn.)

**3. Start the RQ Worker (in a separate terminal):**

```bash
rq worker
```

## 📖 Usage

### Triggering Content Generation via GitHub Webhook

Configure a GitHub webhook for `push` events to point to your deployed `/agent` endpoint. When a push event occurs, the Git Agent will:
1. Fetch recent commits for the repository.
2. Process the commit data asynchronously using RQ.
3. Summarize the changes using the Gemini LLM.
4. Compose social media posts for Twitter/X and LinkedIn.
5. Store the generated posts in the database.

### Example: Manual Content Composition (via API)

You can manually trigger post composition or retrieve posts via the API. For example, to get all posts:

```bash
curl -H "Authorization: Bearer <your_api_token>" http://localhost:5000/api/v1/posts
```

### Interacting with the Flask Shell

For development and debugging, you can access the application context and LangGraph directly:

```bash
flask shell
```
Inside the shell, you can interact with models and the graph:
```python
>>> from app.models import User, Post
>>> from app.extensions import graph_context, run_graph
>>> # ... your commands
```

## 📚 Resources

- [Flask Documentation](https://flask.palletsprojects.com/en/latest/) — Web framework
- [Langchain Documentation](https://python.langchain.com/docs/) — AI framework
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) — State management for LLM applications
- [Google Gemini API Docs](https://ai.google.dev/docs) — LLM API reference
- [RQ (Redis Queue) Documentation](https://python-rq.org/) — Python background job library
- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/) — ORM for Flask
- [Flask-Login Documentation](https://flask-login.readthedocs.io/en/latest/) — User session management
- [Flask-HTTPAuth Documentation](https://flask-httpauth.readthedocs.io/en/latest/) — HTTP authentication for Flask
- [Pandas Documentation](https://pandas.pydata.org/docs/) — Data analysis and manipulation
- [Pydantic Documentation](https://docs.pydantic.dev/latest/) — Data validation and settings management
- [Psycopg Documentation](https://www.psycopg.org/docs/) — PostgreSQL adapter for Python
- [Tenacity Documentation](https://tenacity.readthedocs.io/en/latest/) — Retry library
- [Requests Library](https://requests.readthedocs.io/en/latest/) — HTTP library
- [Requests-OAuthlib](https://requests-oauthlib.readthedocs.io/en/latest/) — OAuth workflow for Requests
- [GitHub API Docs](https://docs.github.com/en/rest) — GitHub REST API
- [Twitter/X API Docs](https://developer.twitter.com/en/docs/twitter-api) — Twitter/X API
- [LinkedIn API Docs](https://developer.linkedin.com/docs/guide/v2/content-publishing/creating-posts) — LinkedIn API
