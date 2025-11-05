# IC Memo Generator

An automated investment committee (IC) memo generation system that aggregates data from multiple sources and uses AI to produce comprehensive, data-driven investment analysis documents.

## 📋 Overview

The IC Memo Generator automates the creation of venture capital investment memos by:
- Gathering company data from Affinity CRM (via Crunchbase)
- Conducting comprehensive research using Perplexity AI
- Analyzing emails and documents (Gmail/Google Drive integration)
- Generating structured IC memos using GPT-4 with RAG (Retrieval-Augmented Generation)
- Supporting both **full comprehensive memos** and **short 1-page memos**
- Creating formatted Google Docs with proper citations and sharing

## 🏗️ Architecture

### Technology Stack

**Backend:**
- Python 3.9+ with FastAPI
- PostgreSQL (Google Cloud SQL)
- SQLAlchemy ORM with Alembic migrations
- OpenAI GPT-4 for text generation
- FAISS for vector similarity search
- Google OAuth 2.0 for authentication
- Google Cloud Secret Manager for secure token storage
- Google Docs API for document generation

**Frontend:**
- React.js
- Axios for API calls
- CSS3 for styling

**Infrastructure:**
- Google Cloud Run for deployment
- Cloud SQL for database
- Cloud SQL Proxy for local development

### System Components

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend API   │
│   (FastAPI)     │
└────────┬────────┘
         │
         ├──► Affinity CRM API (Company data)
         ├──► Perplexity API (Research)
         ├──► Google APIs (Gmail/Drive)
         ├──► OpenAI API (GPT-4, Embeddings)
         └──► PostgreSQL (Data storage)
```

## 📊 Database Schema

### Core Tables

**users**
- `id`: Primary key
- `email`: User email (unique)
- `google_id`: Google OAuth ID
- `name`: User's full name
- `created_at`: Account creation timestamp

**sources**
- `id`: Primary key
- `user_id`: Foreign key to users
- `company_name`: Company name
- `company_description`: Optional description for search disambiguation
- `affinity_data`: JSON (Crunchbase data via Affinity)
- `perplexity_data`: JSON (Research results)
- `gmail_data`: JSON (Email analysis)
- `drive_data`: JSON (Document analysis)
- `created_at`: Timestamp

**document_embeddings**
- `id`: Primary key
- `source_id`: Foreign key to sources
- `chunk_text`: Text chunk (800 words)
- `embedding`: Vector embedding (1536 dimensions)
- `category`: Data category (e.g., "market_analysis")
- `chunk_type`: Type (research, statistics, crm)
- `sources`: JSON array of citation sources
- `chunk_metadata`: JSON metadata

**memo_requests**
- `id`: Primary key
- `user_id`: Foreign key to users
- `source_id`: Foreign key to sources
- `memo_type`: Type of memo ("full" or "short")
- `company_name`: Company name for display
- `status`: Generation status (pending, in_progress, completed, failed)
- `created_at`: Request timestamp
- `completed_at`: Completion timestamp

**memo_sections**
- `id`: Primary key
- `memo_request_id`: Foreign key to memo_requests
- `section_name`: Section identifier
- `content`: Generated content (Markdown)
- `data_sources`: JSON array of sources used
- `status`: Section status (pending, completed, failed)


## 📄 Memo Types

### Full Comprehensive Memo
- **Length:** 8-12 pages
- **Sections:** Executive Summary, Company Snapshot, Team & Leadership, Market Opportunity, Competitive Landscape, Product & Technology, Financial Analysis, Traction & Validation, Deal Considerations
- **Assessment:** Detailed 1-10 ratings for each category with justification
- **Format:** Professional Google Doc with custom styling (size 12pt headers, size 10pt body text), formatted sections, and sources
- **Sharing:** Automatically shared with `wyldvc.com` domain with edit access
- **Use case:** Complete investment committee review, due diligence documentation

### Short 1-Page Memo
- **Length:** 1 page
- **Sections:** Problem/Solution table, Company Brief, Startup Overview, Founder Team, Deal & Traction, Competitive Landscape, Remarks
- **Format:** Concise bullet points and short paragraphs (40-100 words per section)
- **Note:** Short memo functionality is currently disabled in the frontend
- **Use case:** Quick initial assessment, partner updates, preliminary screening

### Key Differences

| Feature | Full Memo | Short Memo |
|---------|-----------|------------|
| **Generation Time** | 5-10 minutes | 2-3 minutes |
| **Token Usage** | ~2000 tokens/section | ~150 tokens/section |
| **RAG Context** | 8 chunks per section | 4 chunks per section |
| **System Prompt** | 300-500 words/section | 40-100 words/section |
| **Document Format** | Multi-page Google Doc with formatted sections | Single page with problem/solution table (currently disabled) |
| **Use Case** | Final IC review | Initial screening |

## 🔧 Configuration & Customization

### Memo Prompts

Edit `backend/schemas/memo_prompts.json` to customize section prompts:

```json
{
  "executive_summary": "Your custom prompt here...",
  "market_opportunity": "Another custom prompt...",
  "assessment_summary": {
    "people": "Assessment prompt...",
    "market_opportunity": "Assessment prompt..."
  }
}
```

### System Messages & Reasoning Frameworks

Modify [`backend/services/memo_generation_service.py`](backend/services/memo_generation_service.py):

**Firm Investment Philosophy:**
```python
base_system = """You are a senior investment analyst at...

OUR FIRM'S INVESTMENT PHILOSOPHY:
- We invest $2-10M in Series A/B rounds...
- We focus on technical founding teams...
...
"""
```

### RAG Configuration

Adjust retrieval settings in [`backend/services/rag_service.py`](backend/services/rag_service.py):

**Chunk size** (line 32):
```python
chunk_size = 800  # Words per chunk
```

**Embedding model** (line 16):
```python
self.embedding_model = "text-embedding-3-small"  # or "text-embedding-3-large"
self.dimension = 1536  # Must match model dimensions
```

**Number of retrieved chunks** (in [`memo_generation_service.py`](backend/services/memo_generation_service.py)):
```python
top_k=8  # Number of most relevant chunks to retrieve
```

### Perplexity Search Configuration

Edit [`backend/services/perplexity_service.py`](backend/services/perplexity_service.py):

**Search categories:**
```python
categories = [
    "company_overview",
    "market_analysis", 
    "competitive_landscape",
    # Add more categories...
]
```

**Statistics categories:**
```python
stats_categories = [
    "funding_history",
    "revenue_metrics",
    # Add more stats categories...
]
```

**Search model:**
```python
model = "llama-3.1-sonar-large-128k-online"  # or other Perplexity models
```

### Document Generation

Modify [`backend/services/document_service.py`](backend/services/document_service.py):

**Section order:**
```python
section_order = [
    "executive_summary",
    "company_snapshot",
    "people",
    # Customize order...
]
```

**Styling** (fonts, colors, spacing):
```python
# Executive Summary styling
heading.font.bold = True
heading.font.size = Pt(16)
heading.font.color.rgb = RGBColor(0, 32, 96)
```

## 📁 Key Files & What They Do

### Backend Services (`backend/services/`)

**[`memo_generation_service.py`](backend/services/memo_generation_service.py)** - Core memo generation logic
- **What it does:** Orchestrates the entire memo generation process using RAG
- **Key functions:**
  - `generate_comprehensive_memo()`: Full 8-12 page memos
  - `generate_short_memo()`: 1-page concise memos
  - `generate_memo_section_with_rag()`: Full memo sections (2000 tokens)
  - `generate_short_memo_section_with_rag()`: Short memo sections (150 tokens)
- **When to modify:**
  - Change system prompts or firm investment philosophy
  - Adjust reasoning frameworks for analytical sections
  - Modify temperature/token limits for GPT
  - Change section generation order or add new sections
  - Adjust short memo length constraints (currently 40-100 words)

**[`rag_service.py`](backend/services/rag_service.py)** - Retrieval-Augmented Generation
- **What it does:** Creates embeddings, builds FAISS index, retrieves relevant context
- **When to modify:**
  - Adjust chunk size (currently 800 words)
  - Change embedding model or dimensions
  - Modify number of retrieved chunks (`top_k`)
  - Add Crunchbase/Affinity data to embeddings
  - Change citation deduplication logic

**[`perplexity_service.py`](backend/services/perplexity_service.py)** - Web research via Perplexity
- **What it does:** Searches the web for company information in specific categories
- **When to modify:**
  - Add/remove research categories
  - Change search prompts to be more specific
  - Adjust model (currently `llama-3.1-sonar-large-128k-online`)
  - Add company description for better disambiguation
  - Modify citation extraction logic

**[`gpt_service.py`](backend/services/gpt_service.py)** - OpenAI GPT API wrapper
- **What it does:** Handles all GPT-4 API calls for text generation
- **When to modify:**
  - Change default model, temperature, or max_tokens
  - Add retry logic or error handling
  - Modify how company data is formatted for prompts
  - Add streaming support for real-time generation

**[`affinity_service.py`](backend/services/affinity_service.py)** - Affinity CRM integration
- **What it does:** Fetches company data from Affinity (which pulls from Crunchbase)
- **When to modify:**
  - Add new fields to extract from Affinity
  - Change API endpoints or authentication
  - Add error handling for missing data
  - Modify data transformation/cleaning logic

**[`document_service.py`](backend/services/document_service.py)** - Google Docs generation
- **What it does:** Compiles memo sections into formatted Google Docs
- **Key functions:**
  - `generate_google_doc()`: Full memo as Google Doc with formatted sections
  - `build_section_blocks()`: Structures content into blocks for Google Docs API
  - `parse_formatted_content()`: Parses markdown and detects headings/paragraphs
  - `process_markdown_bold()`: Handles inline bold formatting (`**text**`)
- **Document formatting:**
  - Title: Size 12pt, bold, format: `IC Memo_[company name] DD_MM_YYYY`
  - Section headers: Size 12pt, bold
  - Body text: Size 10pt, not bold
  - Bold headers (subsections): Size 10pt, bold
  - Inline bold: Detected from `**text**` patterns
- **When to modify:**
  - Change document styling (font sizes, bold formatting)
  - Modify section order or headers
  - Add/remove sections from final document
  - Change citation formatting
  - Adjust markdown parsing logic
  - Modify document title format

**[`google_service.py`](backend/services/google_service.py)** - Google Drive/Docs/Gmail integration
- **What it does:** Searches Drive for files, extracts content, analyzes emails, creates Google Docs
- **Key functions:**
  - `get_drive_service()`: Returns authenticated Drive service
  - `get_docs_service()`: Returns authenticated Docs service
  - `create_google_doc_from_blocks()`: Creates formatted Google Doc from structured blocks
  - `_get_creds_from_secret_manager()`: Retrieves OAuth tokens from Google Cloud Secret Manager
  - `_get_user_creds()`: Gets credentials (Secret Manager first, then user tokens)
- **Authentication:**
  - Primary: Uses Google Cloud Secret Manager token for `investments@wyldvc.com`
  - Fallback: User's stored OAuth tokens (if Secret Manager fails)
  - Required scopes: Drive read, Drive file, full Drive access, Documents
- **Document sharing:**
  - Documents are automatically shared with `wyldvc.com` domain with edit access
- **When to modify:**
  - Add more file types to search for
  - Change search query logic
  - Modify content extraction methods
  - Add email filtering/analysis logic
  - Adjust OAuth scopes
  - Change document sharing permissions
  - Modify Google Docs formatting logic

**[`data_gathering_service.py`](backend/services/data_gathering_service.py)** - Orchestrates data collection
- **What it does:** Coordinates gathering data from all sources (Affinity, Perplexity, Drive, Gmail)
- **When to modify:**
  - Add new data sources
  - Change data gathering order or parallel processing
  - Modify error handling for failed sources
  - Add data validation or cleaning steps
  - Store additional metadata

### Backend Core Files (`backend/`)

**[`app.py`](backend/app.py)** - FastAPI application entry point
- **What it does:** Initializes FastAPI app, registers routes, CORS settings
- **When to modify:**
  - Add new route modules
  - Change CORS settings for frontend URL
  - Add middleware (logging, authentication, rate limiting)
  - Modify startup/shutdown events

**[`auth.py`](backend/auth.py)** - Authentication logic
- **What it does:** Handles Google OAuth flow, JWT token generation/validation
- **When to modify:**
  - Change JWT expiration time
  - Add additional OAuth providers
  - Modify user session management
  - Add role-based access control

**[`database.py`](backend/database.py)** - Database connection
- **What it does:** Creates SQLAlchemy engine and session factory
- **When to modify:**
  - Change database URL or connection pooling
  - Add connection retry logic
  - Modify session lifecycle management

**[`.env`](backend/.env)** - Environment variables
- **What it does:** Stores API keys, database credentials, secrets
- **When to modify:**
  - Update API keys (OpenAI, Perplexity, Affinity)
  - Change database connection string
  - Modify JWT secret or algorithm
  - Update Google OAuth credentials

### Backend Routes (`backend/routes/`)

**[`memo.py`](backend/routes/memo.py)** - Memo generation endpoints
- **What it does:** API endpoints for starting memo generation, checking status, downloading
- **When to modify:**
  - Add new memo-related endpoints
  - Change response formats
  - Add background task handling
  - Modify error responses

**[`data.py`](backend/routes/data.py)** - Data gathering endpoints
- **What it does:** API endpoints for triggering data collection from sources
- **When to modify:**
  - Add new data source endpoints
  - Change request validation
  - Add bulk data gathering
  - Modify company description handling

**[`user.py`](backend/routes/user.py)** - User management endpoints
- **What it does:** User profile, settings, authentication endpoints
- **When to modify:**
  - Add user preferences storage
  - Add team/organization management
  - Modify user data returned

### Database Models (`backend/db/`)

**[`models.py`](backend/db/models.py)** - SQLAlchemy ORM models
- **What it does:** Defines database schema (tables, columns, relationships)
- **When to modify:**
  - Add new tables or columns
  - Change column types or constraints
  - Add indexes for performance
  - Modify relationships between tables

**After modifying models, run:**
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend Components (`frontend/src/components/`)

**[`MemoGenerator.js`](frontend/src/components/MemoGenerator.js)** - Main memo generation UI
- **What it does:** Form for inputting company data, triggering memo generation
- **When to modify:**
  - Add new input fields (e.g., company stage, sector)
  - Change UI layout or styling
  - Add validation logic
  - Modify API call handling

**[`InputForm.js`](frontend/src/components/InputForm.js)** - Company data input form
- **What it does:** Collects company name, Affinity ID, description
- **When to modify:**
  - Add new form fields
  - Change validation rules
  - Modify field labels or placeholders
  - Add conditional fields based on user input

**[`StatusDisplay.js`](frontend/src/components/StatusDisplay.js)** - Generation progress display
- **What it does:** Shows real-time status of memo generation
- **When to modify:**
  - Change polling interval for status updates
  - Modify progress indicators or messages
  - Add estimated time remaining
  - Change error display formatting

## 🔄 Common Modification Scenarios

### Scenario 1: Change Memo Tone or Style

**Files to modify:**
1. [`backend/services/memo_generation_service.py`](backend/services/memo_generation_service.py) - Update `base_system` prompt
2. [`backend/schemas/memo_prompts.json`](backend/schemas/memo_prompts.json) - Adjust section-specific prompts

### Scenario 2: Add a New Data Source

**Files to modify:**
1. Create new service file (e.g., `backend/services/linkedin_service.py`)
2. [`backend/services/data_gathering_service.py`](backend/services/data_gathering_service.py) - Add new data gathering function
3. [`backend/db/models.py`](backend/db/models.py) - Add new column to `sources` table (e.g., `linkedin_data`)
4. Create migration: `alembic revision --autogenerate -m "Add LinkedIn data"`
5. [`backend/routes/data.py`](backend/routes/data.py) - Add endpoint if needed

### Scenario 3: Modify Research Categories

**Files to modify:**
1. [`backend/services/perplexity_service.py`](backend/services/perplexity_service.py) - Update `categories` and `stats_categories` lists
2. Modify category-specific prompts in the search functions

### Scenario 4: Change Document Formatting

**Files to modify:**
1. [`backend/services/document_service.py`](backend/services/document_service.py) - Modify styling functions:
   - `create_google_doc_from_blocks()`: Adjust font sizes, bold formatting
   - `parse_formatted_content()`: Change markdown parsing logic
   - `process_markdown_bold()`: Modify inline bold detection
2. [`backend/services/google_service.py`](backend/services/google_service.py) - Modify Google Docs API calls:
   - `create_google_doc_from_blocks()`: Change text styling, paragraph formatting
   - Document title format: Currently `IC Memo_[company name] DD_MM_YYYY`

### Scenario 5: Adjust RAG Retrieval

**Files to modify:**
1. [`backend/services/rag_service.py`](backend/services/rag_service.py) - Change `chunk_size`, `top_k`, or embedding model
2. [`backend/services/memo_generation_service.py`](backend/services/memo_generation_service.py) - Adjust how context is used in prompts

### Scenario 6: Add New Memo Section

**Files to modify:**
1. [`backend/schemas/memo_prompts.json`](backend/schemas/memo_prompts.json) - Add section prompt
2. [`backend/services/memo_generation_service.py`](backend/services/memo_generation_service.py) - Add to `main_sections` list
3. [`backend/services/document_service.py`](backend/services/document_service.py) - Add to `section_order`

### Scenario 7: Improve Citation Handling

**Files to modify:**
1. [`backend/services/rag_service.py`](backend/services/rag_service.py) - Modify `format_context_with_sources()` deduplication logic
2. [`backend/services/perplexity_service.py`](backend/services/perplexity_service.py) - Change `extract_citations_from_content()`
3. [`backend/services/document_service.py`](backend/services/document_service.py) - Modify `add_sources_section()`

### Scenario 8: Adjust Short Memo Length Constraints

**Files to modify:**
1. [`backend/services/memo_generation_service.py`](backend/services/memo_generation_service.py) - Modify `generate_short_memo_section_with_rag()`:
   - Change `max_tokens=150` to desired token limit
   - Adjust system message for different length requirements
   - Modify `top_k=4` for RAG context retrieval
2. [`backend/schemas/memo_prompts.json`](backend/schemas/memo_prompts.json) - Update word count specifications in prompts

### Scenario 9: Customize Table Column Ratios

**Files to modify:**
1. [`backend/services/document_service.py`](backend/services/document_service.py) - Modify `add_short_problem_solution_table()`:
   - Change `table.columns[0].width = Inches(1.0)` for header column
   - Change `table.columns[1].width = Inches(5.0)` for content column
   - Adjust `table.width = Inches(6.0)` to match total width

## 🚀 Deployment

### Prerequisites

- Google Cloud Platform account with billing enabled
- Firebase account (uses same GCP project)
- Domain name (optional, for custom URLs)
- Docker installed locally
- Node.js 16+ installed

### Quick Deployment

#### 1. Backend Deployment to Cloud Run

**From the root directory, run:**
```bash
./infra/deploy.sh
```

**For Windows users, modify `infra/deploy.sh` first:**
```bash
# Change line endings and paths if needed
# The script uses Unix commands - you may need to adjust for Windows
```

**What the deploy script does:**
- ✅ Builds Docker image for backend
- ✅ Deploys to Google Cloud Run
- ✅ Configures environment variables from Secret Manager
- ✅ Sets up Cloud SQL connection
- ✅ Configures CPU, memory, and scaling limits
- ✅ Installs required packages including `google-cloud-secret-manager`

**Manual deployment (if script fails):**
```bash
# One-time setup: Store secrets in Secret Manager
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-
echo -n "YOUR_PERPLEXITY_API_KEY" | gcloud secrets create perplexity-api-key --data-file=-
echo -n "YOUR_AFFINITY_API_KEY" | gcloud secrets create affinity-api-key --data-file=-
echo -n "YOUR_GOOGLE_CLIENT_ID" | gcloud secrets create google-client-id --data-file=-
echo -n "YOUR_GOOGLE_CLIENT_SECRET" | gcloud secrets create google-client-secret --data-file=-
echo -n "RANDOM_JWT_SECRET" | gcloud secrets create jwt-secret-key --data-file=-
echo -n "YOUR_DB_PASSWORD" | gcloud secrets create db-password --data-file=-

# Google Drive OAuth tokens (generate first using generate_drive_token.py)
gcloud secrets create google-drive-oauth-tokens --data-file=backend/scripts/drive_tokens.json

# Build and deploy from root directory
./infra/deploy.sh
```

**Get your backend URL:**
```bash
gcloud run services describe icmemo-backend --region us-central1 --format='value(status.url)'
```

#### 2. Frontend Deployment to Firebase Hosting

**One-time setup:**
```bash
cd frontend
npm install -g firebase-tools
firebase login
firebase init hosting
# Select: build, Yes (SPA), No (GitHub), No (overwrite)
```

**Deploy frontend:**
```bash
# Get backend URL
BACKEND_URL=$(gcloud run services describe icmemo-backend --region us-central1 --format='value(status.url)')

# Set environment variable
echo "REACT_APP_API_URL=$BACKEND_URL" > .env.production

# Build and deploy
npm run build
firebase deploy --only hosting
```

**Your frontend is now live at** `https://YOUR-PROJECT.web.app`!

### Environment Variables Setup

**Required secrets in Google Secret Manager:**
- `openai-api-key`: Your OpenAI API key
- `perplexity-api-key`: Your Perplexity API key  
- `affinity-api-key`: Your Affinity CRM API key
- `google-client-id`: Google OAuth client ID
- `google-client-secret`: Google OAuth client secret
- `jwt-secret-key`: Random string for JWT signing
- `db-password`: Database password
- `google-drive-oauth-tokens`: JSON object with OAuth tokens for `investments@wyldvc.com` (see below)

**Google Drive OAuth Token Setup:**
1. Run the token generator script:
   ```bash
   cd backend/scripts
   python generate_drive_token.py
   ```
2. This creates `drive_tokens.json` with OAuth tokens
3. Upload the JSON content to Secret Manager:
   ```bash
   gcloud secrets create google-drive-oauth-tokens --data-file=drive_tokens.json
   # Or if secret already exists:
   gcloud secrets versions add google-drive-oauth-tokens --data-file=drive_tokens.json
   ```
4. Ensure the Cloud Run service account has "Secret Manager Secret Accessor" role
5. The JSON should contain: `token`, `refresh_token`, `client_id`, `client_secret`, `scopes`

**Frontend environment variables:**
- `REACT_APP_API_URL`: Your Cloud Run backend URL
- 'REACT_APP_GOOGLE_CLIENT_ID': Google OAuth client ID

### Windows-Specific Notes

**If running on Windows:**
1. Install Git Bash or WSL for Unix commands
2. Modify `infra/deploy.sh` to use Windows-compatible commands
3. Use PowerShell for gcloud commands if needed
4. Ensure Docker Desktop is running





