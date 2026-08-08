pytho# Setup Guide — Step by Step

Follow these instructions to run the project on your computer.

## Prerequisites

You need to install these on your computer first:

### 1. Install Python 3.11+
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Verify: open Command Prompt / Terminal and type `python --version`

### 2. Install Docker Desktop (for Docker mode)
- Download from: https://www.docker.com/products/docker-desktop/
- Install and start Docker Desktop
- Verify: type `docker --version` in terminal

### 3. Install Git
- Download from: https://git-scm.com/downloads
- Verify: type `git --version` in terminal

---

## Option A: Run Locally 

Open TWO terminal windows:

### Terminal 1 — Backend
```bash
cd cloud-doc-management/backend
pip install -r requirements.txt
python main.py
```
You should see: `Uvicorn running on http://0.0.0.0:8000`

### Terminal 2 — Frontend
```bash
cd cloud-doc-management/frontend
python serve.py
```
You should see: `Frontend server running at http://localhost:3000`

### Open your browser
Go to: **http://localhost:3000**

You should see the login page. Use the demo credentials:
- Manager: `manager_user` / `manager123`
- Admin: `admin_user` / `admin123`

---

## Option B: Run with Docker

```bash
cd cloud-doc-management
docker compose up --build
```

Wait for both containers to start, then open: **http://localhost:3000**

To stop: press `Ctrl+C` in the terminal.

---

## Option C: Run with Google Cloud Storage (Production mode)

### Step 1: Create a GCP project
1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name it "doc-management-demo"
4. Click "Create"

### Step 2: Enable Cloud Storage
1. In the GCP console, go to "Storage" → "Browser"
2. Click "Create Bucket"
3. Name it: `doc-management-demo-bucket` (must be globally unique)
4. Region: choose any (e.g., europe-west1)
5. Click "Create"

### Step 3: Create service account credentials
1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Name: "demo-storage"
4. Role: "Storage Admin"
5. Click "Create"
6. Click on the service account → "Keys" → "Add Key" → "JSON"
7. A JSON file will download — save it somewhere safe

### Step 4: Run with GCS
```bash
cd cloud-doc-management/backend

# Set environment variables
# Windows (Command Prompt):
set STORAGE_BACKEND=gcs
set GCS_BUCKET_NAME=doc-management-demo-bucket
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your-credentials.json

# Mac/Linux:
export STORAGE_BACKEND=gcs
export GCS_BUCKET_NAME=doc-management-demo-bucket
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-credentials.json

# Start backend
pip install -r requirements.txt
python main.py
```

---

## Push to GitHub

### Step 1: Create a GitHub repository
1. Go to https://github.com and sign in
2. Click "New" repository
3. Name: "cloud-document-management"
4. Set to "Public" (so the CI/CD pipeline runs)
5. Click "Create repository"

### Step 2: Push your code
```bash
cd cloud-doc-management
git init
git add .
git commit -m "Initial commit - Cloud Document Management System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cloud-document-management.git
git push -u origin main
```

### Step 3: Verify CI/CD pipeline
1. Go to your repository on GitHub
2. Click "Actions" tab
3. You should see the CI/CD pipeline running
4. It should show green checkmarks for all 3 jobs:
   - Backend Tests
   - Frontend Validation
   - Docker Build Check

---

## Troubleshooting

### "Port already in use"
```bash
# Find and kill the process using port 8000
# Windows: netstat -ano | findstr :8000
# Mac/Linux: lsof -i :8000
```

### "Module not found"
```bash
cd backend
pip install -r requirements.txt
```

### "CORS error in browser"
Make sure the backend is running on port 8000. The frontend expects it there.

### Frontend loads but API calls fail
Check that the backend is running: open http://localhost:8000/docs in your browser.
You should see the Swagger API documentation.
