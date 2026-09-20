# JA Assure — AI Marketing Agent

> **An agentic AI marketing platform that researches, creates, localises, validates, reviews, publishes, and learns from marketing content.**

JA Assure is an AI-powered marketing automation platform designed for **JA Assure**, a Singapore-based InsurTech company.

The platform combines **multi-agent AI workflows**, human-in-the-loop approval, compliance validation, automated publishing, and feedback-driven learning into a single system.

---

## 🚀 Overview

JA Assure consists of two connected systems:

### 🧠 Project 1 — The Brain

The Brain is the core AI content-generation and decision-making system.

It transforms a marketing objective into ready-to-publish content through a sequence of specialised agents:

```text
Research
   ↓
Content Generation
   ↓
Localisation
   ↓
Video Generation
   ↓
Compliance Validation
   ↓
Human Review
   ↓
Approved / Rejected / Edited
```

The system also maintains a **learning memory** from human feedback.

Every human edit or rejection can become a lesson containing:

* Reason for the change
* Human feedback
* Original content
* Edited content
* Difference between the versions
* Brand/product context

This allows future generations to take previous human decisions into account.

---

### 🤖 Project 2 — The Hands

The Hands handles the automation that happens after human approval.

It continuously monitors the shared content queue:

```text
Approved Content
      ↓
Background Worker
      ↓
Publisher
      ↓
Social Media Platform
      ↓
Post ID + Publishing Status
      ↓
Analytics
      ↓
Database
```

Supported publishing backends can include:

* Buffer
* Ayrshare
* Dry-run mode for development

The worker can:

1. Detect approved content
2. Schedule/publish it
3. Store the external post ID
4. Update the content status
5. Retrieve engagement metrics
6. Store analytics in the database

---

## 🔗 Brain ↔ Hands Contract

The Brain and Hands communicate through a shared database table:

```text
content_assets
```

The most important field is:

```text
status
```

The content lifecycle is:

```text
draft
  ↓
pending_review
  ↓
approved
  ↓
scheduled
  ↓
published
```

A content asset can also be:

```text
rejected
```

This creates a clean separation between:

* **AI decision-making and content creation**
* **Human approval**
* **Automated publishing**

---

# 🏗️ System Architecture

```text
                         JA ASSURE
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Marketing Brief   │
                 └──────────┬──────────┘
                            │
                            ▼
        ╔════════════════════════════════════════╗
        ║          PROJECT 1 — THE BRAIN        ║
        ╚════════════════════════════════════════╝
                            │
                            ▼
                 ┌─────────────────┐
                 │ Research Agent  │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Content Agent   │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Localisation    │
                 │ Agent           │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Video Agent     │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Compliance      │
                 │ Agent           │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Human Review    │
                 └────────┬────────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
          Rejected                  Approved
             │                         │
             │                         ▼
             │                ┌────────────────┐
             │                │ content_assets │
             │                │    status      │
             │                │   = approved   │
             │                └───────┬────────┘
             │                        │
             │                        ▼
             │       ╔══════════════════════════╗
             │       ║ PROJECT 2 — THE HANDS   ║
             │       ╚══════════════════════════╝
             │                        │
             │                        ▼
             │               ┌─────────────────┐
             │               │ APScheduler     │
             │               │ Worker          │
             │               └────────┬────────┘
             │                        ▼
             │               ┌─────────────────┐
             │               │ Publisher       │
             │               │ Buffer/Ayrshare │
             │               └────────┬────────┘
             │                        ▼
             │               ┌─────────────────┐
             │               │ Social Platform │
             │               └────────┬────────┘
             │                        ▼
             │               ┌─────────────────┐
             │               │ Analytics       │
             │               └────────┬────────┘
             │                        ▼
             │               ┌─────────────────┐
             │               │ post_results    │
             │               └─────────────────┘
             │
             ▼
      ┌──────────────────────┐
      │ Learning Memory      │
      │                     │
      │ Human edits         │
      │ Rejection reasons   │
      │ Feedback            │
      │ Edited diffs        │
      └──────────┬───────────┘
                 │
                 └──────────────► Future AI Generations
```

---

# ✨ Key Features

## 1. Multi-Agent Content Generation

Different agents handle different responsibilities instead of relying on one large prompt.

### Research Agent

Collects relevant information from:

* Competitors
* Industry sources
* Market trends
* Relevant news
* Product information

### Content Agent

Uses research findings to create marketing content for different platforms.

### Localisation Agent

Adapts content based on:

* Market
* Audience
* Language
* Cultural context
* Platform

### Video Agent

Creates short-form marketing videos using:

* Generated scripts
* Text
* Images
* TTS narration
* Video composition

### Compliance Agent

Validates content against predefined compliance rules before it reaches human review.

### Lead Agent

Processes marketing interactions and helps identify potential leads.

### Feedback Agent

Converts human review decisions into reusable learning signals.

---

# 🧠 Learning Memory

One of the core ideas of JA Assure is that the system should **learn from human decisions**.

For example:

```text
AI Generated Content

        ↓

Human Reviewer

"Remove this claim because it is too strong."

        ↓

Feedback Memory

Reason:
Compliance / Unsupported Claim

Original:
"JA Assure guarantees complete protection."

Edited:
"JA Assure provides protection designed for your needs."

        ↓

Future Generation

AI receives the previous lesson
and avoids repeating the same mistake.
```

This creates a closed feedback loop:

```text
Generate
   ↓
Review
   ↓
Edit / Reject
   ↓
Store Lesson
   ↓
Retrieve Relevant Lessons
   ↓
Generate Better Content
```

---

# 🏢 JA Assure Brands

The system is designed around three JA Assure product areas.

### 💎 Jade

Jewellers block insurance.

### 🚚 Jaguar Transit

Insurance for high-value goods during transportation.

### 🩺 DoctorShield

Medical indemnity insurance.

The same agent architecture can be reused across all three products while maintaining different:

* Brand guidelines
* Target audiences
* Compliance rules
* Product information
* Content strategies

---

# 🛠️ Technology Stack

| Layer               | Technology                |
| ------------------- | ------------------------- |
| Frontend            | React + TypeScript + Vite |
| Styling             | Tailwind CSS              |
| Charts              | Recharts                  |
| Backend             | Python + FastAPI          |
| Agent Orchestration | LangGraph                 |
| LLM                 | GroqCloud API             |
| Research            | Tavily / Serper           |
| Web Scraping        | httpx + BeautifulSoup     |
| JS Rendering        | Playwright                |
| Database            | PostgreSQL                |
| Prototype Database  | SQLite                    |
| ORM                 | SQLAlchemy 2.0            |
| Validation          | Pydantic v2               |
| Video               | MoviePy + FFmpeg + Pillow |
| TTS                 | gTTS                      |
| Background Jobs     | APScheduler               |
| Publishing          | Buffer / Ayrshare         |
| API Documentation   | FastAPI / OpenAPI         |
| Deployment          | Render / Railway + Vercel |

---

# 📁 Project Structure

```text
JA-Assure-Agent/
│
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml
│   │
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── db.py
│       ├── models.py
│       ├── schemas.py
│       ├── deps.py
│       ├── llm.py
│       ├── seed.py
│       │
│       ├── agents/
│       │   ├── state.py
│       │   ├── graph.py
│       │   ├── research_agent.py
│       │   ├── content_agent.py
│       │   ├── compliance_agent.py
│       │   ├── video_agent.py
│       │   ├── localization_agent.py
│       │   ├── lead_agent.py
│       │   ├── feedback_agent.py
│       │   └── prompts.py
│       │
│       ├── services/
│       │   ├── search.py
│       │   ├── scraper.py
│       │   ├── media.py
│       │   ├── tts.py
│       │   └── publisher.py
│       │
│       ├── routers/
│       │   ├── content.py
│       │   ├── review.py
│       │   ├── leads.py
│       │   ├── research.py
│       │   ├── analytics.py
│       │   └── health.py
│       │
│       └── workers/
│           ├── scheduler.py
│           └── publish_worker.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── api.ts
│       ├── types.ts
│       │
│       ├── components/
│       │   ├── ui.tsx
│       │   ├── Layout.tsx
│       │   └── AssetCard.tsx
│       │
│       └── pages/
│           ├── Dashboard.tsx
│           ├── Generate.tsx
│           ├── ReviewQueue.tsx
│           ├── ContentLibrary.tsx
│           ├── Leads.tsx
│           ├── Research.tsx
│           ├── Publishing.tsx
│           └── Analytics.tsx
│
├── media/
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

# ⚙️ Prerequisites

Install the following before running the project:

### Required

* Python 3.12+
* Node.js 20+
* npm
* PostgreSQL
* Git

### Optional

* FFmpeg
* Playwright Chromium
* Tavily API key
* Serper API key
* Buffer API key
* Ayrshare API key

---

# 🔐 Environment Configuration

Create:

```text
.env
```

in the **project root**:

```text
JA-Assure-Agent/
├── .env
├── backend/
└── frontend/
```

Example:

```env
ENVIRONMENT=development

DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ja_assure

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=https://api.groq.com/openai/v1

LLM_MODEL=openai/gpt-oss-120b
LLM_FAST_MODEL=openai/gpt-oss-20b

# Research
TAVILY_API_KEY=
SERPER_API_KEY=

# Publishing
PUBLISHER_BACKEND=dry_run
BUFFER_API_KEY=
BUFFER_PROFILE_IDS={"linkedin":"","instagram":"","x":"","tiktok":""}
AYRSHARE_API_KEY=

# Media
MEDIA_DIR=./media
PUBLIC_MEDIA_BASE_URL=http://localhost:8000/media
ENABLE_VIDEO_RENDER=false

# Worker
ENABLE_SCHEDULER=false
PUBLISH_POLL_SECONDS=10
MAX_COMPLIANCE_RETRIES=2
```

> **Never commit `.env` to Git.**

Add the following to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
node_modules/
dist/
media/
*.db
```

---

# 🗄️ Database Setup

The project uses PostgreSQL for development and production.

Create the database:

```sql
CREATE DATABASE ja_assure;
```

The connection string follows this format:

```text
postgresql+psycopg2://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

For example:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ja_assure
```

### SQLite Alternative

For a quick prototype, PostgreSQL can be replaced with:

```env
DATABASE_URL=sqlite:///./ja_assure.db
```

No PostgreSQL server is required when using SQLite.

---

# 🧠 Backend Setup

Open PowerShell:

```powershell
cd D:\Projects\JA-Assure-Agent\backend
```

Activate the virtual environment:

```powershell
D:\Projects\JA-Assure-Agent\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

If using Playwright:

```powershell
playwright install chromium
```

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

FastAPI Swagger documentation:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

# 💻 Frontend Setup

Open another terminal:

```powershell
cd D:\Projects\JA-Assure-Agent\frontend
```

Install dependencies:

```powershell
npm install
```

Start Vite:

```powershell
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

---

# 🔄 Running the Complete System

You need two terminals during development.

### Terminal 1 — Backend

```powershell
cd D:\Projects\JA-Assure-Agent\backend

D:\Projects\JA-Assure-Agent\.venv\Scripts\Activate.ps1

uvicorn app.main:app --reload --port 8000
```

### Terminal 2 — Frontend

```powershell
cd D:\Projects\JA-Assure-Agent\frontend

npm run dev
```

Then open:

```text
http://localhost:5173
```

---

# 🧪 Development Modes

The project supports safe development modes before connecting external services.

### Dry-run Publishing

Keep:

```env
PUBLISHER_BACKEND=dry_run
```

This allows the publishing workflow to be tested without actually posting to social media.

### Disable Video Rendering

During initial development:

```env
ENABLE_VIDEO_RENDER=false
```

Enable it after the content pipeline is working:

```env
ENABLE_VIDEO_RENDER=true
```

### Disable Scheduler

During development:

```env
ENABLE_SCHEDULER=false
```

Enable the background worker when the publishing pipeline is ready:

```env
ENABLE_SCHEDULER=true
```

---

# 📊 Content Lifecycle

Each piece of content moves through a controlled lifecycle.

```text
┌──────────┐
│  DRAFT   │
└────┬─────┘
     ▼
┌────────────────┐
│ PENDING_REVIEW │
└───────┬────────┘
        │
    ┌───┴────┐
    │        │
    ▼        ▼
APPROVED  REJECTED
    │
    ▼
SCHEDULED
    │
    ▼
PUBLISHED
```

Human edits are stored as learning signals.

---

# 👤 Human-in-the-Loop Review

AI-generated content is not automatically published.

The review workflow allows a human reviewer to:

### Approve

```text
AI Content → Approved
```

### Edit

```text
AI Content
    ↓
Human Edit
    ↓
Edited Content
    ↓
Approved
```

### Reject

```text
AI Content
    ↓
Rejection Reason
    ↓
Learning Memory
```

This ensures that compliance-sensitive marketing content remains under human control.

---

# 🔍 Research Workflow

The Research Agent can combine multiple sources:

```text
Marketing Brief
      ↓
Search
      ↓
Source Collection
      ↓
Web Scraping
      ↓
Information Extraction
      ↓
Research Summary
      ↓
Content Agent
```

Tavily is the preferred research provider, with Serper available as an alternative/fallback.

---

# 📱 Frontend Modules

The dashboard contains the following major sections:

### Dashboard

Provides an overview of:

* Content generated
* Pending reviews
* Approved content
* Published content
* System status
* Publishing status

### Generate

Create a new marketing brief and trigger the AI workflow.

### Review Queue

Review AI-generated content and:

* Approve
* Edit
* Reject

### Content Library

View previously generated marketing assets.

### Research

View research results and source information.

### Leads

View and manage marketing leads.

### Publishing

Track:

* Approved content
* Scheduled posts
* Published posts
* External post IDs

### Analytics

View engagement metrics retrieved from published content.

---

# 🔌 API Structure

The FastAPI backend is divided into routers:

```text
/api/content
/api/review
/api/leads
/api/research
/api/analytics
/api/health
```

The complete API specification is available through:

```text
http://localhost:8000/docs
```

---

# 🧩 Agent Architecture

The agent workflow is orchestrated through LangGraph.

Conceptually:

```text
                    ┌───────────────┐
                    │ Marketing     │
                    │ Brief         │
                    └───────┬───────┘
                            ▼
                    ┌───────────────┐
                    │   Research    │
                    └───────┬───────┘
                            ▼
                    ┌───────────────┐
                    │    Content    │
                    └───────┬───────┘
                            ▼
                    ┌───────────────┐
                    │ Localisation  │
                    └───────┬───────┘
                            ▼
                    ┌───────────────┐
                    │     Video     │
                    └───────┬───────┘
                            ▼
                    ┌───────────────┐
                    │  Compliance   │
                    └───────┬───────┘
                            ▼
                    ┌───────────────┐
                    │ Human Review  │
                    └───────────────┘
```

The graph maintains shared state throughout the workflow.

---

# 📈 Analytics Loop

Published content produces engagement information.

```text
Published Post
      ↓
External Platform
      ↓
Engagement Data
      ↓
Analytics Worker
      ↓
Database
      ↓
Dashboard
```

Possible metrics include:

* Impressions
* Likes
* Comments
* Shares
* Clicks
* Engagement rate

These metrics can eventually be used to improve future content strategies.

---

# 🛡️ Compliance-First Design

Insurance marketing requires careful handling of claims and product information.

The Compliance Agent evaluates generated content against configurable rules such as:

* Unsupported claims
* Misleading statements
* Missing disclaimers
* Product-specific restrictions
* Excessive guarantees
* Sensitive wording
* Brand requirements

The system does not bypass human review.

Instead:

```text
AI Generation
      ↓
Compliance Gate
      ↓
Human Review
      ↓
Publication
```

---

# 🚀 Future Improvements

Potential extensions include:

* Advanced long-term agent memory
* More social media integrations
* Automated A/B testing
* Campaign-level analytics
* Audience segmentation
* Multilingual content generation
* Voice-based marketing briefs
* Improved video generation
* Retrieval-Augmented Generation (RAG)
* Vector-based learning memory
* Automated campaign optimisation
* Role-based access control
* Production-grade authentication

---

# 🧪 Testing

Backend tests can be added under:

```text
backend/tests/
```

Frontend tests can be added using the project's preferred React testing framework.

Before committing changes, verify:

```powershell
# Backend
python -m compileall app

# Frontend
npm run build
```

---

# 🐛 Troubleshooting

## PostgreSQL connection error

If you see:

```text
database "ja_assure" does not exist
```

create the database:

```sql
CREATE DATABASE ja_assure;
```

Then verify your `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ja_assure
```

---

## Tailwind unknown utility error

If Tailwind reports:

```text
Cannot apply unknown utility class
```

check the custom theme definitions in:

```text
frontend/src/index.css
```

Custom colors such as:

```text
bg-ink-950
bg-ink-900
border-ink-800
text-accent-soft
```

must be defined in the Tailwind v4 `@theme` section.

---

## Groq fallback

If the dashboard shows:

```text
LLM: fallback
```

check:

```env
GROQ_API_KEY=your_actual_key
```

and verify:

```env
LLM_MODEL=openai/gpt-oss-120b
LLM_FAST_MODEL=openai/gpt-oss-20b
```

---

## Frontend cannot connect to backend

Make sure FastAPI is running:

```text
http://localhost:8000
```

and Vite is running:

```text
http://localhost:5173
```

Also verify:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

# 🔒 Security

Never commit:

```text
.env
API keys
Database passwords
Publishing credentials
Access tokens
```

Use:

```text
.env.example
```

for sharing configuration templates.

---

# 📌 Project Status

### Project 1 — The Brain

| Component          | Status            |
| ------------------ | ----------------- |
| Research Agent     | 🚧 In Development |
| Content Agent      | 🚧 In Development |
| Localisation Agent | 🚧 In Development |
| Video Agent        | 🚧 In Development |
| Compliance Agent   | 🚧 In Development |
| Human Review       | 🚧 In Development |
| Learning Memory    | 🚧 In Development |

### Project 2 — The Hands

| Component         | Status            |
| ----------------- | ----------------- |
| Content Queue     | 🚧 In Development |
| Background Worker | 🚧 In Development |
| Publisher         | 🚧 In Development |
| Post Tracking     | 🚧 In Development |
| Analytics         | 🚧 In Development |

> Update the status indicators as each module is completed.

---

# 🎯 Hackathon Demonstration Flow

A complete demonstration can follow this sequence:

```text
1. Create Marketing Brief
          ↓
2. Research Agent gathers information
          ↓
3. Content Agent generates content
          ↓
4. Localisation Agent adapts the content
          ↓
5. Video Agent generates media
          ↓
6. Compliance Agent validates the asset
          ↓
7. Human reviews the content
          ↓
8. Human edits/rejects/approves
          ↓
9. Learning Memory stores the decision
          ↓
10. Approved asset enters publishing queue
          ↓
11. Background worker publishes it
          ↓
12. External Post ID is stored
          ↓
13. Analytics are retrieved
          ↓
14. Results appear in the dashboard
```

This demonstrates the complete **Brain → Human → Hands → Analytics → Learning** loop.

---

# 👥 Team

**Project:** JA Assure — AI Marketing Agent

**Hackathon:** JA-Assure Hackathon

### Core Concept

> **The Brain thinks. The Human decides. The Hands execute. The System learns.**

---

## 📄 License

This project is developed for the JA Assure hackathon/project demonstration.

All rights reserved unless otherwise specified.
