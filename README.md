# Djassapro MVP

A web application for generating and sharing ad messages with voice input capabilities.

## Project Structure
```
djassapro-mvp/
├── backend/         # FastAPI backend
└── frontend/        # Vue.js frontend
```

## Setup Instructions

### Backend Setup
1. Create a Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run the backend server:
```bash
uvicorn main:app --reload
```

### Frontend Setup
1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

## Features
- Voice input for ad message creation
- Text transcription and editing
- Ad message generation with emojis
- Media upload support
- WhatsApp sharing capability
