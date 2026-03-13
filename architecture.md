# Groww Playstore Reviews Analyser - Architecture Document

## 1. System Overview

### 1.1 Purpose

Automated system to fetch, analyze, and deliver Groww Playstore reviews insights via email to different stakeholders (Product, Support, UI/UX, Leadership).

### 1.2 Core Features

- Fetch reviews from Google Play Store with filtering (no PII, no duplicates, English only, min 5 words)
- AI-powered theme grouping and classification
- Role-based 1-pager generation
- Manual trigger via UI Dashboard
- Scheduler-based automated triggers (GitHub Actions)
- History tracking of email triggers only
- Preview mode (no email required, not logged in history)

---

## 2. Technology Stack


| Component      | Technology                   |
| -------------- | ---------------------------- |
| Backend        | Python (FastAPI)             |
| Frontend       | React with TypeScript        |
| Database       | PostgreSQL                   |
| Cache          | Redis                        |
| Task Queue     | Celery + Redis               |
| LLM APIs       | Groq API, Gemini API         |
| Email Service  | SMTP (Python smtplib)        |
| PDF Generation | ReportLab / WeasyPrint       |
| Play Store API | google-play-scraper (Python) |
| Scheduler      | GitHub Actions               |


---

## 3. Phase-wise Architecture

### PHASE 1: Data Ingestion Layer

**Objective**: Fetch and filter reviews from Google Play Store

#### Components:

1. **PlayStoreClient** - Wrapper around google-play-scraper
2. **ReviewFilter** - Applies all filtering rules
3. **DeduplicationService** - Prevents duplicate reviews
4. **ReviewRepository** - Stores cleaned reviews

#### Data Flow:

```
Trigger Request → PlayStoreClient → Raw Reviews → ReviewFilter → 
DeduplicationService → Clean Reviews → ReviewRepository
```

#### Filtering Rules (Applied in sequence):


| Rule          | Implementation                                                  |
| ------------- | --------------------------------------------------------------- |
| No PII        | Regex patterns for email, phone, PAN, Aadhaar removal/detection |
| No Duplicates | Hash-based dedup (content hash) + DB unique constraint          |
| English Only  | langdetect library + confidence threshold (>0.9)                |
| Min 5 Words   | Word count validation                                           |
| Date Range    | Filter by review date                                           |


#### LLM Usage in Phase 1: NONE

- All filtering is rule-based to save LLM tokens

#### Output Schema:

```json
{
  "review_id": "string",
  "content": "string",
  "rating": 1-5,
  "review_date": "datetime",
  "version": "string",
  "thumbs_up": "integer",
  "cleaned_content": "string"
}
```

#### Test Cases for Phase 1:


| Test ID | Description                            | Expected Result                     |
| ------- | -------------------------------------- | ----------------------------------- |
| P1-T01  | Fetch 100 reviews from Play Store      | Returns 100 reviews with all fields |
| P1-T02  | Filter reviews with PII (email, phone) | PII content flagged/removed         |
| P1-T03  | Duplicate review detection             | Second identical review rejected    |
| P1-T04  | Non-English review filtering           | Only English reviews retained       |
| P1-T05  | Short review filtering (<5 words)      | Reviews with <5 words rejected      |
| P1-T06  | Date range filtering                   | Only reviews within range returned  |
| P1-T07  | Empty result handling                  | Graceful empty response             |
| P1-T08  | Play Store API failure                 | Error handling and retry logic      |
| P1-T09  | Rate limiting from Play Store          | Exponential backoff implemented     |
| P1-T10  | Fetch max 1000 reviews                 | Pagination handled correctly        |


---

### PHASE 2: Theme Extraction & Classification

**Objective**: Group reviews into themes using LLM (Role-based, 3-5 themes only)

#### Components:

1. **BatchProcessor** - Handles review batching for LLM calls
2. **ThemeExtractor** (Groq LLM) - Extracts role-based themes from reviews
3. **ThemeClassifier** (Groq LLM) - Classifies reviews into themes
4. **ThemeRepository** - Stores theme mappings

#### LLM Strategy - Phase 2:


| Task                 | LLM  | Model         | Reason                                   |
| -------------------- | ---- | ------------- | ---------------------------------------- |
| Theme Extraction     | Groq | llama-3.1-70b | Fast, cost-effective for bulk processing |
| Theme Classification | Groq | llama-3.1-70b | Consistent with extraction model         |


#### Why Groq for Phase 2:

- High throughput needed (processing many reviews)
- Lower cost for bulk operations
- Fast response times for batch processing
- No complex reasoning required

#### Theme Sampling Strategy:

- Analyze 150-200 reviews to identify distinct themes
- This sample size is sufficient for theme extraction
- All reviews are then classified into these themes

#### Batch Processing Logic:

```
Reviews → Sample (150-200) → Groq API → 3-5 Themes → 
Classify all reviews → Store mappings
```

#### Theme Extraction Prompt (Groq - Role-Based):

```
You are analyzing Groww app reviews for a {role}.
Identify exactly 3-5 distinct themes that are most relevant to a {role}.

For each theme provide:
- Theme name (short, descriptive)
- Description (what users are saying)
- Sentiment (positive/negative/mixed)
- Keywords that identify this theme

Focus areas for {role}:
{role_focus_areas}

Reviews: {sample_reviews}

Output JSON format:
{
  "themes": [
    {
      "name": "string",
      "description": "string",
      "sentiment": "positive|negative|mixed",
      "keywords": ["string"]
    }
  ]
}
```

#### Theme Classification Prompt (Groq):

```
Classify each review into one of these themes: {theme_list}

Reviews: {reviews}

Output JSON format:
{
  "classifications": [
    {
      "review_id": "string",
      "theme": "string",
      "confidence": 0.0-1.0
    }
  ]
}
```

**Note**: Reviews that don't fit any theme are excluded from the 1-pager. Only classified reviews are shown.

#### Output Schema:

```json
{
  "themes": [
    {
      "theme_id": "uuid",
      "name": "string",
      "description": "string",
      "sentiment": "string",
      "keywords": ["string"],
      "review_count": "integer",
      "avg_rating": "float"
    }
  ],
  "classifications": [
    {
      "review_id": "string",
      "theme_id": "uuid",
      "confidence": "float"
    }
  ]
}
```

#### Test Cases for Phase 2:


| Test ID | Description                         | Expected Result                      |
| ------- | ----------------------------------- | ------------------------------------ |
| P2-T01  | Extract themes from 150-200 reviews | Returns exactly 3-5 distinct themes  |
| P2-T02  | Theme extraction by role            | Themes are relevant to specific role |
| P2-T03  | Classify 100 reviews                | Each review assigned to theme        |
| P2-T04  | Low confidence classification       | Flagged for manual review            |
| P2-T05  | Groq API failure                    | Fallback to retry or error           |
| P2-T06  | Empty batch handling                | Graceful handling                    |
| P2-T07  | No "Other" theme                    | Unclassified reviews excluded        |
| P2-T08  | Large dataset (1000 reviews)        | Batch processing completes           |
| P2-T09  | Rate limit handling                 | Exponential backoff                  |
| P2-T10  | Invalid JSON response from LLM      | Retry with stricter prompt           |


---

### PHASE 3: Insight Generation

**Objective**: Generate role-based actionable insights using LLM

#### Components:

1. **InsightGenerator** (Gemini) - Generates actionable insights
2. **RoleContextBuilder** - Builds context for specific roles
3. **ExampleSelector** - Selects representative review examples
4. **InsightRepository** - Stores generated insights

#### LLM Strategy - Phase 3:


| Task               | LLM    | Model            | Reason                              |
| ------------------ | ------ | ---------------- | ----------------------------------- |
| Insight Generation | Gemini | gemini-2.0-flash | Better reasoning, structured output |
| Actionable Ideas   | Gemini | gemini-2.0-flash | Creative problem-solving required   |


#### Why Gemini for Phase 3:

- Complex reasoning needed for actionable insights
- Better at structured, role-specific outputs
- Higher quality creative suggestions
- Lower volume (themes vs individual reviews)

#### Role-Based Context:


| Role       | Focus Areas                                      |
| ---------- | ------------------------------------------------ |
| Product    | Feature gaps, usability issues, feature requests |
| Support    | Common complaints, pain points, user frustration |
| UI/UX      | Navigation issues, design feedback, user flow    |
| Leadership | Overall sentiment, key metrics, trends           |


#### Insight Generation Prompt (Gemini):

```
Based on these themes from Groww app reviews, generate 3-5 actionable insights for a {role}.

Themes:
{themes_with_examples}

Requirements:
1. Insights must be specific and actionable
2. Include impact assessment (high/medium/low)
3. Include effort estimate (high/medium/low)
4. Reference specific user feedback

Output JSON format:
{
  "insights": [
    {
      "title": "string",
      "description": "string",
      "impact": "high|medium|low",
      "effort": "high|medium|low",
      "supporting_quotes": ["string"],
      "recommended_action": "string"
    }
  ]
}
```

#### Example Selection Strategy:

- Select 2-3 highest confidence reviews per theme
- Ensure examples show variety (different phrasings)
- Prioritize recent reviews
- Include mix of ratings if theme is mixed sentiment

#### Output Schema:

```json
{
  "insights": [
    {
      "insight_id": "uuid",
      "role": "string",
      "title": "string",
      "description": "string",
      "impact": "string",
      "effort": "string",
      "supporting_quotes": ["string"],
      "recommended_action": "string",
      "theme_ids": ["uuid"]
    }
  ],
  "examples": [
    {
      "theme_id": "uuid",
      "reviews": [
        {
          "review_id": "string",
          "content": "string",
          "rating": "integer",
          "date": "datetime"
        }
      ]
    }
  ]
}
```

#### Test Cases for Phase 3:


| Test ID | Description                           | Expected Result                 |
| ------- | ------------------------------------- | ------------------------------- |
| P3-T01  | Generate insights for Product role    | 3-5 Product-focused insights    |
| P3-T02  | Generate insights for Support role    | 3-5 Support-focused insights    |
| P3-T03  | Generate insights for UI/UX role      | 3-5 UI/UX-focused insights      |
| P3-T04  | Generate insights for Leadership role | 3-5 Leadership-focused insights |
| P3-T05  | Example selection quality             | Representative examples chosen  |
| P3-T06  | Gemini API failure                    | Retry or fallback handling      |
| P3-T07  | Invalid insight format                | Validation and retry            |
| P3-T08  | Empty themes handling                 | Graceful error                  |
| P3-T09  | Insight uniqueness                    | No duplicate recommendations    |
| P3-T10  | Impact/effort validation              | Valid values only               |


---

### PHASE 4: Report Generation

**Objective**: Generate Groww-themed 1-pager PDF

#### Components:

1. **ReportBuilder** - Assembles report data
2. **PDFGenerator** - Creates PDF using WeasyPrint/ReportLab
3. **TemplateEngine** - Jinja2 templates for role-based layouts
4. **AssetManager** - Groww brand assets (colors, logo)

#### Groww Brand Guidelines:


| Element         | Value                |
| --------------- | -------------------- |
| Primary Color   | #00D09C (Green)      |
| Secondary Color | #5367FF (Blue)       |
| Background      | #FFFFFF              |
| Text Primary    | #1A1A1A              |
| Text Secondary  | #6C6C6C              |
| Font            | Inter / System fonts |


#### Report Sections:

1. **Header**
  - Groww logo
  - Report title: "Reviews Insights Report"
  - Generation date
  - Role badge
2. **Metadata Section**
  - Number of reviews analyzed
  - Date range
  - Target role
  - Report date
3. **Top Themes Section**
  - Theme name
  - Review count & percentage
  - Average rating
  - 2-3 example reviews per theme
4. **Actionable Insights Section**
  - Insight title
  - Description
  - Impact/Effort tags
  - Supporting user quotes
  - Recommended action
5. **Footer**
  - Confidentiality notice
  - Page number

#### Template Structure:

```
templates/
├── base.html (common layout)
├── components/
│   ├── header.html
│   ├── metadata.html
│   ├── themes.html
│   ├── insights.html
│   └── footer.html
└── roles/
    ├── product.html
    ├── support.html
    ├── uiux.html
    └── leadership.html
```

#### Output: PDF file (A4 size)

#### Test Cases for Phase 4:


| Test ID | Description                      | Expected Result                  |
| ------- | -------------------------------- | -------------------------------- |
| P4-T01  | Generate PDF for Product role    | Valid PDF with Product layout    |
| P4-T02  | Generate PDF for Support role    | Valid PDF with Support layout    |
| P4-T03  | Generate PDF for UI/UX role      | Valid PDF with UI/UX layout      |
| P4-T04  | Generate PDF for Leadership role | Valid PDF with Leadership layout |
| P4-T05  | Groww branding applied           | Correct colors and logo          |
| P4-T06  | Large content handling           | Multi-page if needed             |
| P4-T07  | PDF generation failure           | Error handling                   |
| P4-T08  | Template rendering               | All variables populated          |
| P4-T09  | File size optimization           | Reasonable file size             |
| P4-T10  | Mobile-friendly PDF              | Readable on mobile               |


---

### PHASE 5: Email Service

**Objective**: Send personalized emails with PDF attachment

#### Components:

1. **EmailComposer** - Builds email content (HTML body same as PDF content)
2. **PersonalizationEngine** - Adds receiver name, role context
3. **EmailSender** - SMTP integration (Python smtplib)
4. **EmailTracker** - Tracks delivery status

#### Email Content Strategy:

- **Email Body (HTML)**: Same content as PDF - includes Top Themes with examples and Actionable Insights
- **PDF Attachment**: Identical content for offline reading/sharing
- **No Content Modification**: Insights shown in email are exactly as generated in Phase 3

#### Email Template Structure:

```
Subject: Your Groww Reviews Insights Report - {Role}

Body (HTML):
- Greeting (Hi {ReceiverName})
- Report header with metadata
- Top Themes section (same as PDF)
- Actionable Insights section (same as PDF)
- Footer

Attachment: PDF with identical content
```

#### Email Templates by Role:


| Role       | Subject                                    | Tone           |
| ---------- | ------------------------------------------ | -------------- |
| Product    | "Product Insights: User Feedback Summary"  | Analytical     |
| Support    | "Customer Voice: Common Issues & Feedback" | Empathetic     |
| UI/UX      | "UX Insights: User Experience Feedback"    | Design-focused |
| Leadership | "Weekly Pulse: App Reviews Summary"        | Executive      |


#### Test Cases for Phase 5:


| Test ID | Description                        | Expected Result              |
| ------- | ---------------------------------- | ---------------------------- |
| P5-T01  | Send email with attachment         | Email delivered with PDF     |
| P5-T02  | Personalization with receiver name | Name appears in greeting     |
| P5-T03  | Invalid email address              | Validation error             |
| P5-T04  | Email service failure              | Retry logic triggered        |
| P5-T05  | Large attachment handling          | Size limits handled          |
| P5-T06  | Email tracking                     | Status updated in DB         |
| P5-T07  | Bounce handling                    | Bounce recorded              |
| P5-T08  | Multiple recipients                | Each gets personalized email |
| P5-T09  | Email template rendering           | All variables replaced       |
| P5-T10  | Rate limiting                      | Queue handling               |


---

### PHASE 6: UI Dashboard

**Objective**: Web interface for manual triggers and mail trigger history tracking.

#### Components:

1. **DashboardUI** - Vanilla JS frontend with dark/light theme support
2. **SendInsightsForm** - Modal form for manual mail triggers
3. **HistoryViewer** - Table display of mail triggers with status and actionables
4. **ThemeToggle** - Dark/Light mode switcher with persistence

#### Navigation Strategy:

- **Single Screen**: Header with CTAs + Main content area
- **Empty State**: Displayed when no triggers exist
- **History Table**: Displayed when triggers exist

#### Header Layout:

| Element                | Position | Description                           |
| ---------------------- | -------- | ------------------------------------- |
| Title + Subtitle       | Left     | "Reviews Analyser" branding           |
| Theme Toggle           | Right    | Dark/Light mode switcher              |
| Send Insights CTA      | Right    | Primary action - opens send form      |

**Note**: Schedule Insights functionality has been moved to GitHub Actions (Phase 7). No scheduler configuration in UI.

#### Send Insights Form Fields:

| Field             | Type       | Required | Default | Validation             |
| ----------------- | ---------- | -------- | ------- | ---------------------- |
| Number of Reviews | Number     | Yes      | 1000    | Min: 10, Max: 2000     |
| Time Period       | Dropdown   | Yes      | 7 weeks | Options: 1-12 weeks    |
| Role              | Dropdown   | Yes      | -       | Product/Support/UI/UX/Leadership |
| Receiver Name     | Text       | Yes      | -       | Non-empty              |
| Receiver Email    | Email      | Yes      | -       | Valid email format     |

Form Actions: Cancel, Send Mail (triggers phases 1-5)

#### Status Workflow:

| Status Stage        | Description                                      |
| ------------------- | ------------------------------------------------ |
| Started             | Started Data Ingestion                           |
| Data Fetched        | Reviews fetched from Play Store                  |
| Themes Created      | Themes created from sample reviews               |
| Reviews Classified  | Reviews classified into themes                   |
| Insight Generation  | Actionable insights generated                    |
| Report Generated    | Groww-themed PDF generated                       |
| Mail Sent           | Email delivered successfully with attachment     |
| {Status}(Failed)    | Error occurred in the specified phase            |

**Note**: If a phase is retrying internally, it is not marked as "Failed". Failure status is only applied after all retry attempts are exhausted.

#### Mail Trigger History Table:

Columns:
1. Trigger Time (Date and time)
2. Type (Manual/Scheduler)
3. Role
4. Reviews
5. Time Period
6. Receiver Name
7. Receiver Email
8. Status (with colored badge)
9. Actionables

#### Action Logic:

| Trigger Position | Status      | Actionable | Behavior                                      |
| ---------------- | ----------- | ---------- | --------------------------------------------- |
| Most Recent      | Mail Sent   | View PDF   | Opens existing PDF from Phase 4               |
| Most Recent      | Failed      | Retry      | Resumes process from previous successful phase|
| Other            | Any         | Delete     | Shows confirmation modal, removes from history|

**Note**: No actionables for in-progress statuses (Started through Report Generated).

#### Empty State:

When no triggers exist:
- Centered inbox icon
- Heading: "No triggers yet"
- Subtext: "Start by triggering a new review analysis for your stakeholders."
- CTA: "Send Insights" button

#### Theme Support:

- Light theme (default): Groww brand colors with light backgrounds
- Dark theme: Dark backgrounds with adjusted brand colors
- Theme preference persisted in localStorage
- Smooth transitions between themes


---

### PHASE 7: Scheduler Service (GitHub Actions)

**Objective**: Automated scheduled report generation using GitHub Actions with fixed configuration.

#### Overview:

The scheduler runs entirely via GitHub Actions without UI configuration. All parameters are hardcoded in the workflow file.

#### Fixed Schedule Configuration:

| Parameter        | Value                              |
| ---------------- | ---------------------------------- |
| Weeks            | 9                                  |
| Reviews          | 1000                               |
| Role             | Product                            |
| Recipient Name   | Nihal                              |
| Recipient Email  | nihalreddyb1997@gmail.com          |
| Frequency        | Weekly (configurable in cron)      |

#### Components:

1. **GitHub Actions Workflow** - Cron-based scheduling with hardcoded parameters
2. **SchedulerAPI** - Endpoint to receive trigger from GitHub Actions
3. **ExecutionLogger** - Logs scheduled executions in triggers table

#### Why Task Queue (Celery + Redis)?

The Task Queue serves several critical purposes:

1. **Asynchronous Processing**: Report generation involves multiple long-running operations (fetching reviews, LLM calls, PDF generation). The task queue allows the API to return immediately while processing happens in the background.
2. **Reliability**: If a worker crashes or restarts, queued tasks persist in Redis and can be retried.
3. **Rate Limiting Protection**: LLM APIs have rate limits. The queue allows controlled processing with delays between requests.
4. **Scalability**: Multiple Celery workers can process tasks in parallel when needed.
5. **Retry Logic**: Failed tasks (e.g., LLM timeout) can be automatically retried with exponential backoff.
6. **Scheduler Integration**: GitHub Actions triggers the API, which queues the job for background processing.

#### GitHub Actions Workflow Structure:

```yaml
# .github/workflows/scheduled-reports.yml
name: Scheduled Reports
on:
  schedule:
    - cron: '0 9 * * 1'  # Weekly Monday 9 AM IST (configurable)
  workflow_dispatch:     # Manual trigger option

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Report API
        run: |
          curl -X POST "${{ secrets.API_ENDPOINT }}/api/triggers/scheduled" \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{
              "weeks": 9,
              "reviews_count": 1000,
              "role": "Product",
              "recipient_name": "Nihal",
              "recipient_email": "nihalreddyb1997@gmail.com",
              "mode": "email",
              "type": "Scheduler"
            }'
```

#### Required GitHub Secrets:

| Secret Name    | Description                          |
| -------------- | ------------------------------------ |
| API_ENDPOINT   | Backend API URL (e.g., http://host:8001) |
| API_TOKEN      | Authentication token for API access  |

#### API Endpoint for Scheduler:

**POST** `/api/triggers/scheduled`

Authentication: Bearer token (from GitHub Secrets)

Request Body:
```json
{
  "weeks": 9,
  "reviews_count": 1000,
  "role": "Product",
  "recipient_name": "Nihal",
  "recipient_email": "nihalreddyb1997@gmail.com",
  "mode": "email",
  "type": "Scheduler"
}
```

#### Scheduler Trigger Record:

Scheduled triggers are logged in the `triggers` table with:
- `mode`: "scheduler"
- `type`: "Scheduler"
- Same fields as manual triggers (review_count, period_weeks, role, receiver_email, receiver_name)

#### Modifying Schedule Parameters:

To change schedule parameters, edit the workflow file directly:
1. Update `.github/workflows/scheduled-reports.yml`
2. Modify the cron expression for frequency changes
3. Modify the JSON payload for parameter changes
4. Commit and push changes

#### Test Cases for Phase 7:

| Test ID | Description                   | Expected Result               |
| ------- | ----------------------------- | ----------------------------- |
| P7-T01  | GitHub Actions trigger        | Workflow runs on schedule     |
| P7-T02  | API authentication            | Valid token accepted          |
| P7-T03  | Trigger at scheduled time     | Job executes on time          |
| P7-T04  | Manual workflow dispatch      | Trigger works via UI button   |
| P7-T05  | Fixed parameters applied      | Correct params in trigger     |
| P7-T06  | Scheduler logged in history   | Appears in trigger table      |
| P7-T07  | Failed API call handling      | Error logged in Actions       |
| P7-T08  | Email delivery                | Report sent to fixed email    |


---

## 4. Database Schema

### Tables:

#### reviews

```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY,
    review_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    cleaned_content TEXT,
    rating INTEGER NOT NULL,
    review_date TIMESTAMP NOT NULL,
    app_version VARCHAR(50),
    thumbs_up INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### themes

```sql
CREATE TABLE themes (
    id UUID PRIMARY KEY,
    trigger_id UUID REFERENCES triggers(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sentiment VARCHAR(50),
    keywords JSONB,
    review_count INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### review_themes

```sql
CREATE TABLE review_themes (
    id UUID PRIMARY KEY,
    review_id UUID REFERENCES reviews(id),
    theme_id UUID REFERENCES themes(id),
    confidence DECIMAL(3,2),
    UNIQUE(review_id, theme_id)
);
```

#### insights

```sql
CREATE TABLE insights (
    id UUID PRIMARY KEY,
    trigger_id UUID REFERENCES triggers(id),
    role VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    impact VARCHAR(20),
    effort VARCHAR(20),
    supporting_quotes JSONB,
    recommended_action TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### triggers

```sql
CREATE TABLE triggers (
    id UUID PRIMARY KEY,
    mode VARCHAR(20) NOT NULL, -- 'manual' or 'scheduler'
    review_count INTEGER,
    period_start DATE,
    period_end DATE,
    role VARCHAR(50),
    receiver_email VARCHAR(255),
    receiver_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'data_ingestion',
    pdf_path VARCHAR(500),
    error_message TEXT,
    current_phase VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

#### schedules (Deprecated)

**Note**: The schedules table is no longer used. GitHub Actions workflow contains the fixed schedule configuration directly in the YAML file. All scheduler parameters are hardcoded in `.github/workflows/scheduled-reports.yml`.

Historical schema (for reference):
```sql
-- This table is retained for backward compatibility but not actively used
CREATE TABLE schedules (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    github_cron VARCHAR(100),
    parameters JSONB,
    is_active BOOLEAN DEFAULT true,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. API Endpoints

### Reviews

- `GET /api/reviews/fetch` - Trigger review fetch
- `GET /api/reviews` - List stored reviews

### Themes

- `POST /api/themes/extract` - Extract themes from reviews
- `GET /api/themes` - List themes

### Insights

- `POST /api/insights/generate` - Generate insights
- `GET /api/insights/:id` - Get insight details

### Reports

- `POST /api/reports/generate` - Generate PDF report
- `GET /api/reports/:id/preview` - Preview report
- `GET /api/reports/:id/download` - Download PDF

### Triggers

- `POST /api/triggers` - Create new trigger
- `GET /api/triggers` - List trigger history (email triggers only)
- `GET /api/triggers/:id` - Get trigger details
- `POST /api/triggers/:id/retry` - Retry failed trigger
- `POST /api/triggers/scheduled` - Endpoint for GitHub Actions

### Scheduler (GitHub Actions)

- `POST /api/triggers/scheduled` - Endpoint for GitHub Actions to trigger scheduled reports (fixed parameters)

---

## 6. LLM Rate Limiting Strategy

### Groq Limits (assumed):

- Requests per minute: 100
- Tokens per minute: 100,000

### Gemini Limits (assumed):

- Requests per minute: 60
- Tokens per minute: 60,000

### Mitigation Strategies:

1. **Batch Processing**: Process reviews in batches of 50
2. **Token Estimation**: Pre-calculate tokens before API call
3. **Exponential Backoff**: Retry with delays on rate limit
4. **Queue System**: Use Celery for async processing
5. **Circuit Breaker**: Fail fast if service unavailable
6. **Caching**: Cache theme extractions for similar review sets

---

## 7. Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **PII Handling**: Strip before storage, audit logs
3. **Email Validation**: Validate receiver emails
4. **Rate Limiting**: API endpoints rate-limited
5. **Authentication**: Dashboard behind auth (future)
6. **Audit Logging**: All triggers logged with user info

---

## 8. Deployment Architecture

```
┌─────────────────┐
│   Nginx/ALB     │
└────────┬────────┘
         │
┌────────▼────────┐
│  React Frontend │
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI Backend│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌──▼────┐
│PostgreSQL│  │ Redis │
└─────────┘  └───┬───┘
                 │
            ┌────┴────┐
            │  Celery │
            │ Workers │
            └─────────┘
```

---

## 9. Monitoring & Logging

### Metrics to Track:

- Reviews fetched per trigger
- LLM API latency (Groq, Gemini)
- LLM token usage
- PDF generation time
- Email delivery rate
- Trigger success/failure rate

### Alerts:

- LLM rate limit approaching
- Play Store API failures
- Email delivery failures
- High error rate

---

## 10. Future Enhancements

1. Multi-language support (Hindi, etc.)
2. Sentiment trend analysis over time
3. Competitor comparison
4. Slack/Teams integration
5. Custom theme definitions
6. ML-based theme clustering
7. Real-time review streaming
8. User authentication & RBAC

---

## 11. Implementation Phases Priority


| Phase   | Priority | Dependencies |
| ------- | -------- | ------------ |
| Phase 1 | P0       | None         |
| Phase 2 | P0       | Phase 1      |
| Phase 3 | P0       | Phase 2      |
| Phase 4 | P0       | Phase 3      |
| Phase 5 | P0       | Phase 4      |
| Phase 6 | P1       | Phase 1-5    |
| Phase 7 | P2       | Phase 1-6    |


---

*Document Version: 2.0*
*Last Updated: March 9, 2026*