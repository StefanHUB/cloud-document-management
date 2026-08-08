# Cloud-Enhanced Engineering Document Management System

A cloud-native document management system extending the research by Yu (2024) with cost-aware and carbon-aware cloud region selection.

## Research Paper

Yu, J. (2024) 'Design and implementation of Engineering Document Management Information System', *Proceedings of the 2024 5th International Conference on Big Data Economy and Information Management*, pp. 136–142. DOI: [10.1145/3724154.3724177](https://doi.org/10.1145/3724154.3724177)

## Project Extension

This project extends the original research paper by:

1. **Migrating from on-premises storage to cloud-native architecture** — replacing local database with Google Cloud Storage integration
2. **Adding cost-aware region selection** — automatically selecting the cheapest cloud data centre region for document storage
3. **Adding carbon-aware region selection** — allowing users to choose greener data centres with lower carbon footprints
4. **Containerization with Docker** — separate frontend and backend containers for scalable deployment
5. **CI/CD pipeline** — automated testing and validation with GitHub Actions

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (HTML/Bootstrap/JS)              │
│                   Port 3000 - serves static UI               │
├──────────────┬───────────────────┬────────────────────────┤
│  Login Page  │  Upload + Regions  │  Document List/Review  │
└──────┬───────┴───────────┬───────┴────────────────────────┘
       │                   │
       │    REST API       │
       ▼                   ▼
┌──────────────────────────────────────────────────────────────┐
│              Backend (FastAPI - Python)                      │
│                    Port 8000                                 │
├──────────┬──────────────┬───────────────┬──────────────────┤
│  Auth    │  Documents   │   Regions     │   Storage         │
│  Module  │  CRUD        │   Module      │   Adapter         │
├──────────┴──────────────┴───────────────┴──────────────────┤
│  JWT Token Auth │ SQLite DB  │ Region Data  │ Local/GCS    │
│  (Firebase-ready)│           │ (cost/carbon)│  Storage      │
└──────────────────────────────────────────────────────────────┘
       │                                         │
       ▼                                         ▼
┌──────────────┐                    ┌────────────────────────┐
│   SQLite     │                    │   Google Cloud Storage  │
│   Database   │                    │   (or Local Storage)    │
│   (metadata) │                    │   (document files)      │
└──────────────┘                    └────────────────────────┘
```

## Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Backend | FastAPI (Python) | High-performance async framework with automatic OpenAPI/Swagger docs; ideal for REST APIs |
| Frontend | HTML5 + Bootstrap 5 + JavaScript | Clean, responsive UI without heavy framework overhead; fast to develop and deploy |
| Database | SQLite | Lightweight metadata storage; production would use Cloud SQL (managed MySQL/PostgreSQL) |
| Cloud Storage | Google Cloud Storage | Scalable object storage with regional buckets enabling cost/carbon-aware placement |
| Containerization | Docker | Consistent deployment environments; separates frontend/backend into independent scalable containers |
| CI/CD | GitHub Actions | Automated testing on every push; validates backend imports, API functionality, and Docker builds |
| Version Control | Git/GitHub | Collaborative development with full history tracking |
| Auth | JWT tokens (Firebase-ready) | Role-based access control; production integrates Firebase Authentication for managed identity |

## Cloud Usage Justification

### Why Cloud Storage?
The original research paper uses on-premises storage which limits scalability and accessibility. Google Cloud Storage provides:
- **Durability**: 99.999999999% (11 nines) data durability
- **Scalability**: Automatic scaling without capacity planning
- **Global access**: Documents accessible from any location
- **Region selection**: Choose storage location for cost/carbon optimization

### Cost-Aware Region Selection
Different GCP regions have different storage costs. The system automatically selects the cheapest region:
- Compares storage cost per GB/month across 8 regions
- Recommends the most cost-effective region
- Displays cost comparison data to users

### Carbon-Aware Region Selection
Data centres have different carbon footprints based on local energy grids. The system selects the greenest region:
- Uses carbon intensity data (gCO2eq/kWh) for each region
- Considers renewable energy percentage
- Calculates a sustainability score combining both metrics
- Recommends the region with the lowest environmental impact

### Cost and Resource Minimization
- Local storage mode for development (zero cloud cost)
- Free tier GCS usage (5GB free) for demonstration
- Region selection feature directly minimizes operational costs
- Docker containers optimize resource usage

## Setup Instructions

### Option 1: Run with Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd cloud-doc-management

# Build and run both containers
docker compose up --build

# Access the application:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

### Option 2: Run Locally (Development)

```bash
# Terminal 1: Start backend
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2: Start frontend
cd frontend
python serve.py

# Access: http://localhost:3000
```

### Option 3: Run with GCS (Production mode)

```bash
# Set environment variables
export STORAGE_BACKEND=gcs
export GCS_BUCKET_NAME=your-bucket-name
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Start backend
cd backend
pip install -r requirements.txt
python main.py
```

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Document Manager | `manager_user` | `manager123` |
| Document Administrator | `admin_user` | `admin123` |

## Features

### Document Manager Role
- Upload engineering documents with title and description
- Select cost-aware or carbon-aware storage region
- View all documents and their storage regions
- Download documents

### Document Administrator Role
- View all submitted documents
- Approve or reject documents
- Download documents
- Delete documents

### Region Selection
- View all 8 cloud regions with cost and carbon metrics
- Cost-aware mode: recommends cheapest region
- Carbon-aware mode: recommends greenest region
- Each upload stores the selected region in document metadata

## API Endpoints

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| POST | `/auth/login` | Authenticate user | Public |
| GET | `/auth/demo-users` | Get demo credentials | Public |
| GET | `/regions` | List all cloud regions | Authenticated |
| GET | `/regions/recommend?mode=cost\|carbon` | Get region recommendation | Authenticated |
| GET | `/documents` | List documents | Authenticated |
| POST | `/documents/upload` | Upload document | Manager |
| GET | `/documents/{id}/download` | Download document | Authenticated |
| GET | `/documents/{id}` | Get document details | Authenticated |
| POST | `/documents/{id}/review` | Approve/reject document | Admin |
| DELETE | `/documents/{id}` | Delete document | Admin |
| GET | `/health` | Health check | Public |
| GET | `/docs` | Swagger API documentation | Public |

## DevOps Pipeline

The GitHub Actions CI/CD pipeline (`.github/workflows/ci.yml`) performs:
1. **Backend tests**: Installs dependencies, validates imports, runs API smoke tests
2. **Frontend validation**: Checks required files exist
3. **Docker build**: Validates both Dockerfiles build successfully

## Project Structure

```
cloud-doc-management/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py          # FastAPI application with all endpoints
│   ├── auth.py           # Authentication and role-based access
│   ├── database.py       # SQLite database operations
│   ├── storage.py        # Storage adapter (local + GCS)
│   └── regions.py        # Cloud region data and recommendations
├── frontend/
│   ├── Dockerfile
│   ├── serve.py          # Static file server
│   └── src/
│       ├── index.html     # Main application page
│       ├── css/style.css   # Custom styles
│       └── js/app.js       # Frontend logic
├── .github/workflows/
│   └── ci.yml            # CI/CD pipeline
├── docker-compose.yml    # Docker Compose configuration
├── .gitignore
└── README.md
```

## References

- Yu, J. (2024) 'Design and implementation of Engineering Document Management Information System', *Proceedings of the 2024 5th International Conference on Big Data Economy and Information Management*, pp. 136–142. DOI: [10.1145/3724154.3724177](https://doi.org/10.1145/3724154.3724177)
- Husain, M.E. et al. (2023) 'Transitioning from data centers to cloud', *Proceedings of the 5th International Conference on Information Management & Machine Intelligence*. DOI: [10.1145/3647444.3652491](https://doi.org/10.1145/3647444.3652491)
- Hyun, D. et al. (2024) 'Green cloud: Supporting sustainable behavior', *Extended Abstracts of the CHI Conference*. DOI: [10.1145/3613905.3647968](https://doi.org/10.1145/3613905.3647968)
- Liu, S. et al. (2025) 'SkyStore: Cost-optimized object storage across regions and clouds', *Proceedings of the VLDB Endowment*, 18(7), pp. 2084–2096. DOI: [10.14778/3734839.3734846](https://doi.org/10.14778/3734839.3734846)

## Generative AI Usage Declaration

This project was developed with AI assistance for:
- Architecture design and documentation
- Code comments and justifications


