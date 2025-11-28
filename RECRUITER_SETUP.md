# Quick Setup Guide for Recruiters

## Test This Demo in 5 Minutes

### Step 1: Get Your API Key (2 minutes)

**IMPORTANT:** You need your own free Google Gemini API key.

1. Visit: **https://aistudio.google.com/app/apikey**
2. Click "Create API Key"
3. Copy the key

### Step 2: Configure the Project (1 minute)

Create a file named `.env` in the project root folder and add:

```
GEMINI_API_KEY=paste_your_api_key_here
```

**Or** copy `.env.example` to `.env` and edit it.

### Step 3: Run the Demo (2 minutes)

**Windows:**
```batch
demo_setup.bat    # Run once (installs dependencies)
start_demo.bat    # Starts the server + opens browser
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Browser opens automatically at **http://localhost:8000**
You can upload documents from the `demo_samples/` folder and ask questions.

## API Documentation

Visit **http://localhost:8000/docs** to see:
- Interactive API playground
- All endpoints and schemas
- Request/response examples

---


