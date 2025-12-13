# FormFlow - AI-Powered Form Builder

FormFlow is an AI-powered form builder that enables users to create, edit, and manage forms through natural language and document uploads.

## Features

- Create forms using natural language descriptions
- Upload documents (PDF, TXT) to extract form content
- AI-assisted form editing
- Version control with undo functionality
- Public form sharing and submission
- Response collection and export

## Tech Stack

### Frontend
- React 18 with React Router
- Tailwind CSS for styling
- Firebase Authentication
- Axios for API calls

### Backend
- Flask (Python)
- Firebase Admin SDK
- Anthropic Claude API
- PyPDF2/pdfplumber for PDF processing

### Infrastructure
- Google App Engine (Frontend + Backend)
- Firebase Firestore (Database)
- Firebase Authentication

## Project Structure

```
formflow/
├── frontend/           # React frontend
│   ├── src/
│   │   ├── components/ # Reusable components
│   │   ├── pages/      # Page components
│   │   ├── context/    # React context (Auth)
│   │   └── services/   # API services
│   ├── public/
│   └── app.yaml        # App Engine config
│
├── backend/            # Flask backend
│   ├── app/
│   │   ├── routes/     # API endpoints
│   │   ├── services/   # Business logic
│   │   └── utils/      # Utilities
│   ├── tests/
│   └── app.yaml        # App Engine config
│
├── mcp-server/         # MCP integration
├── firestore.rules     # Firestore security rules
├── dispatch.yaml       # App Engine routing
└── cloudbuild.yaml     # CI/CD config
```

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.12+
- Firebase project
- Claude API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials

# Run development server
python main.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your Firebase config

# Run development server
npm start
```

## Deployment

### Prerequisites

- Google Cloud SDK installed
- Google Cloud project with App Engine enabled
- Firebase project linked to GCP project

### Deploy

```bash
# Backend
cd backend
gcloud app deploy app.yaml

# Frontend
cd frontend
npm run build
gcloud app deploy app.yaml

# Routing rules
gcloud app deploy dispatch.yaml

# Firestore rules
firebase deploy --only firestore:rules
```

### Environment Setup

1. Create secrets in Secret Manager:
```bash
echo -n "your-claude-api-key" | gcloud secrets create claude-api-key --data-file=-
```

2. Grant App Engine access:
```bash
gcloud secrets add-iam-policy-binding claude-api-key \
  --member=serviceAccount:PROJECT_ID@appspot.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/verify` | POST | Yes | Verify Firebase token |
| `/api/forms/create` | POST | Yes | Create new form |
| `/api/forms/` | GET | Yes | List user's forms |
| `/api/forms/:id` | GET | No | Get form (public) |
| `/api/forms/:id/edit` | POST | Yes | AI edit form |
| `/api/forms/:id/save` | POST | Yes | Manual save |
| `/api/forms/:id/undo` | POST | Yes | Undo last change |
| `/api/forms/:id/submit` | POST | No | Submit response |
| `/api/forms/:id/responses` | GET | Yes | Get responses |

## License

MIT
