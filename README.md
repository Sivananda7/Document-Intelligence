# Document Intelligence System

## Overview
The Document Intelligence System is an intelligent, scalable pipeline designed to ingest scanned documents or photographs of physical documents, automatically classify them, and extract structured information. It features a modern, user-friendly interface that allows users to review the AI's confidence scores and correct any extracted data before final confirmation.

## Key Features
- **Document Upload**: Secure, drag-and-drop interface capable of handling multiple complex documents at once (PDF, JPEG, PNG, WEBP).
- **Automatic Document Classification**: Dynamically identifies the document type (e.g., Driver's License, Passport, Vehicle Power of Attorney).
- **OCR-based Text Extraction**: Utilizes state-of-the-art Computer Vision engines to extract raw text, even from blurry or complex images.
- **Structured Data Extraction**: Employs Large Language Models (LLMs) to map the raw OCR text perfectly into strict JSON schemas.
- **User Review and Correction Interface**: Clean dual-pane validation UI for human-in-the-loop review.
- **Metadata Storage**: Tracks document processing status, AI reasoning confidence, and completion percentages.
- **Secure Document Storage**: Immutable S3 Object Storage integration for raw document assets.

## Technology Stack
- **Frontend**: React.js, Vite, Framer Motion (Animations), Axios, Vanilla CSS
- **Backend**: Python 3, FastAPI, Uvicorn, Motor (Async MongoDB), Tenacity (Backoff Retries)
- **AI / OCR**: docTR (Computer Vision OCR), Google Gemini 3 Flash Preview (LLM Data Restructuring), PyMuPDF
- **Storage**: MongoDB (Document Metadata), IDrive e2 / S3-Compatible Storage (Blob Storage)

## Repository Structure
```text
.
├── backend/          # FastAPI server, AI pipeline scripts, S3 connections, and MongoDB Models
├── frontend/         # React application, Vite config, UI components, and styles
├── docs/             # Technical specifications, implementation plans, and architecture designs
└── docker-compose.yml# Production container orchestration
```

## Setup Instructions

### Option 1: Docker (Recommended)
The easiest way to run the application is using the provided Docker Compose configuration, which automatically sets up the Frontend, Backend, and MongoDB databases in isolated containers.

1. **Set up Environment Variables:**
   Ensure your `backend/.env` file is properly configured with your API keys (see *Environment Variables* section below).

2. **Deploy the fleet:**
   ```bash
   docker compose up --build -d
   ```

### Option 2: Run Locally (Manual Setup)

**1. Start MongoDB:**
Ensure you have a local instance of MongoDB running on port `27017`.

**2. Run the Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**3. Run the Frontend:**
```bash
cd ../frontend
npm install
npm run dev
```

## Environment Variables
To securely run this application, create a `.env` file in the `backend/` directory with the following configuration keys:

```env
# S3 / IDrive e2 Storage Configuration
AWS_ACCESS_KEY_ID="your_access_key"
AWS_SECRET_ACCESS_KEY="your_secret_key"
AWS_REGION="us-west-2"
S3_BUCKET_NAME="your-bucket-name"
S3_ENDPOINT_URL="https://s3.us-west-2.idrivee2.com"

# Google Gemini API
GEMINI_API_KEY="your_gemini_api_key_here"

# Database (Optional: defaults to localhost if running manually)
MONGODB_URL="mongodb://localhost:27017"
```

## Running the Application
Once the services are booted (either via Docker or manually), the application will be accessible directly from your browser:
- **Frontend UI:** Navigate to `http://localhost:5173`
- **Backend API Sandbox:** Navigate to `http://localhost:8000/docs` to test endpoints natively via Swagger UI.

## Example Workflow
1. **Upload Document**: Click or drag a scanned file into the dropzone. It is securely saved to S3.
2. **Extraction**: The FastAPI background worker routes the image through the docTR computer vision engine, grabs the messy text, and passes it to the Gemini 3 LLM layer to cleanly extract JSON according to a strict template.
3. **Review**: The User Interface dynamically renders the returned JSON key-values next to the original raw document.
4. **Confirm**: The user can safely edit the AI's predictions and successfully `Accept` the data, pushing it cleanly into MongoDB.

## Additional Documentation
- **Architecture and Scale:** Detailed system design, schema enforcement logic, architecture decisions, and scalability considerations for Enterprise loads are strictly documented inside `docs/DESIGN.md`.
- **System Integrations:** A conceptual breakdown mapping the pipeline within a strict Identity Verification environment is documented inside `docs/CONCEPTUAL.md`.
