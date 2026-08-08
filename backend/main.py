"""
Main FastAPI application for the Cloud-Enhanced Engineering Document Management System.

This is the central API that powers the document management system with:
- Role-based authentication (document manager / document administrator)
- Document upload, download, and viewing
- Cost-aware and carbon-aware cloud region selection
- Integration with Google Cloud Storage (with local fallback for development)

Architecture:
- FastAPI provides RESTful endpoints with automatic Swagger/OpenAPI documentation
- SQLite stores document metadata (production would use Cloud SQL)
- Storage adapter abstracts local vs GCS document storage
- Region selection module provides cost and carbon intensity data for cloud regions

Based on the research paper:
Yu, J. (2024) 'Design and implementation of Engineering Document Management
Information System', Proceedings of the 2024 5th International Conference on
Big Data Economy and Information Management, pp. 136-142.
DOI: https://doi.org/10.1145/3724154.3724177
"""

import os
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import io

from auth import authenticate, get_user_from_token, DEMO_USERS
from database import init_db, create_document, get_document, get_all_documents, update_document_status, delete_document
from storage import get_storage
from regions import get_all_regions, recommend_regions

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize database on import (ensures tables exist before any request)
init_db()
logger.info("Database initialized on startup")

# Initialize FastAPI app
app = FastAPI(
    title="Cloud-Enhanced Engineering Document Management System",
    description="""
    A cloud-native document management system extending the research by Yu (2024)
    with cost-aware and carbon-aware cloud region selection.

    ## Features
    - Role-based authentication (Document Manager / Document Administrator)
    - Document upload, download, and viewing
    - Cost-aware storage: selects cheapest cloud data centre regions
    - Carbon-aware storage: selects greenest cloud data centre regions
    - Google Cloud Storage integration with local development fallback

    ## Roles
    - **Document Manager**: Can upload, download, and view engineering documents
    - **Document Administrator**: Can review, approve, or reject submitted documents
    """,
    version="1.0.0",
)

# CORS configuration - allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Dependency ---

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI dependency to extract and verify the authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        return get_user_from_token(authorization)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_role(required_role: str):
    """Create a dependency that requires a specific role."""
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {required_role}, your role: {user['role']}"
            )
        return user
    return role_checker


# --- Pydantic Models ---

class LoginRequest(BaseModel):
    username: str
    password: str


class ReviewRequest(BaseModel):
    status: str  # "approved" or "rejected"
    comment: str = ""


class RegionRecommendationResponse(BaseModel):
    mode: str
    mode_label: str
    recommended_region: dict
    rationale: str
    metric: str
    metric_label: str
    all_regions_ranked: list


# --- Auth Endpoints ---

@app.post("/auth/login", tags=["Authentication"])
async def login(request: LoginRequest):
    """
    Authenticate a user and return a JWT-like token.

    In production, this would use Firebase Authentication:
    - Frontend uses Firebase SDK to sign in
    - Backend verifies the Firebase ID token
    - User roles are stored as Firebase custom claims

    For demo purposes, simplified token-based auth is used.
    """
    try:
        result = authenticate(request.username, request.password)
        logger.info(f"User '{request.username}' logged in with role: {result['role']}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/auth/demo-users", tags=["Authentication"])
async def get_demo_users():
    """Return demo user credentials for testing purposes."""
    return {
        "users": [
            {"username": "manager_user", "password": "manager123", "role": "manager", "name": "Document Manager"},
            {"username": "admin_user", "password": "admin123", "role": "admin", "name": "Document Administrator"},
        ]
    }


# --- Region Endpoints ---

@app.get("/regions", tags=["Cloud Regions"])
async def list_regions():
    """
    List all available cloud regions with their cost and carbon metrics.
    This data powers the cost-aware and carbon-aware region selection feature.
    """
    return {"regions": get_all_regions()}


@app.get("/regions/recommend", tags=["Cloud Regions"])
async def recommend_region(mode: str = "cost"):
    """
    Recommend the best cloud region based on the selected mode.

    - mode=cost: Selects the region with the lowest storage cost
    - mode=carbon: Selects the region with the best sustainability score

    This is the key extension to the original research paper, adding
    cost optimization and environmental sustainability to document storage.
    """
    if mode not in ("cost", "carbon"):
        raise HTTPException(status_code=400, detail="Mode must be 'cost' or 'carbon'")
    return recommend_regions(mode)


# --- Document Endpoints ---

@app.get("/documents", tags=["Documents"])
async def list_documents(
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    List all documents. Optionally filter by status.
    Both managers and admins can view documents.
    """
    docs = get_all_documents(status_filter=status)
    return {"documents": docs, "count": len(docs)}


@app.post("/documents/upload", tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    region_mode: str = Form("cost"),  # "cost" or "carbon"
    region: str = Form(""),  # specific region or auto-select
    user: dict = Depends(require_role("manager"))
):
    """
    Upload an engineering document to cloud storage.

    The document is stored in the selected cloud region:
    - If region_mode=cost, the system recommends the cheapest region
    - If region_mode=carbon, the system recommends the greenest region
    - The user can override with a specific region

    Only document managers can upload documents.
    """
    # ================================================================
    # COST-AWARE vs CARBON-AWARE REGION ROUTING
    # ================================================================
    # This is the key feature extending the original research paper.
    # The region_mode parameter ('cost' or 'carbon') determines which
    # cloud region the document is stored in:
    #
    # - region_mode='cost'   -> regions.py sorts by cost_per_gb_month
    #                           and returns the CHEAPEST region
    # - region_mode='carbon' -> regions.py sorts by sustainability_score
    #                           (low carbon + high renewable) and returns
    #                           the GREENEST region
    #
    # The user can also manually override with a specific region ID.
    # ================================================================
    if not region:
        # Auto-select: ask the regions module for the best region
        recommendation = recommend_regions(region_mode)
        selected_region = recommendation["recommended_region"]["region_id"]
        logger.info(f"Region auto-selected ({region_mode} mode): {selected_region}")
    else:
        # Manual override: user specified a specific region
        selected_region = region
        logger.info(f"Region manually selected: {selected_region}")

    # Read file data
    file_data = await file.read()
    file_size = len(file_data)

    # Upload to storage (local or GCS)
    storage = get_storage()
    storage_info = storage.upload(file_data, file.filename, selected_region)

    # Save document metadata to database
    doc_data = {
        "title": title,
        "description": description,
        "file_name": file.filename,
        "file_path": storage_info["file_path"],
        "file_size": file_size,
        "file_type": file.content_type or "application/octet-stream",
        "storage_region": selected_region,
        "region_mode": region_mode,
        "uploaded_by": user["name"],
        "uploaded_by_role": user["role"],
        "gcs_bucket": storage_info.get("bucket"),
        "gcs_blob_name": storage_info.get("blob_name"),
    }

    document = create_document(doc_data)
    logger.info(f"Document '{title}' uploaded by {user['name']} to region: {selected_region}")

    return {
        "message": "Document uploaded successfully",
        "document": document,
        "storage_region": selected_region,
        "region_mode": region_mode,
    }


@app.get("/documents/{doc_id}/download", tags=["Documents"])
async def download_document(
    doc_id: int,
    user: dict = Depends(get_current_user)
):
    """
    Download a document from cloud storage.
    Both managers and admins can download documents.
    """
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    storage = get_storage()
    # Use gcs_blob_name for GCS storage, file_path for local storage
    if doc.get("gcs_blob_name"):
        file_data = storage.download(doc["gcs_blob_name"])
    else:
        file_data = storage.download(doc["file_path"])

    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=doc["file_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{doc["file_name"]}"'
        }
    )


@app.get("/documents/{doc_id}", tags=["Documents"])
async def get_document_details(
    doc_id: int,
    user: dict = Depends(get_current_user)
):
    """Get details of a specific document."""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.post("/documents/{doc_id}/review", tags=["Documents"])
async def review_document(
    doc_id: int,
    review: ReviewRequest,
    user: dict = Depends(require_role("admin"))
):
    """
    Review a document - approve or reject it.
    Only document administrators can review documents.

    This implements the workflow described in the research paper where
    the document administrator reviews documents submitted by document managers.
    """
    if review.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    updated = update_document_status(
        doc_id, review.status, user["name"], review.comment
    )

    logger.info(f"Document {doc_id} {review.status} by {user['name']}")
    return {"message": f"Document {review.status}", "document": updated}


@app.delete("/documents/{doc_id}", tags=["Documents"])
async def remove_document(
    doc_id: int,
    user: dict = Depends(require_role("admin"))
):
    """
    Delete a document from storage and database.
    Only document administrators can delete documents.
    """
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from storage
    storage = get_storage()
    storage.delete(doc["file_path"])

    # Delete from database
    delete_document(doc_id)

    logger.info(f"Document {doc_id} deleted by {user['name']}")
    return {"message": "Document deleted successfully"}


# --- Health Check ---

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "Cloud Document Management System",
        "storage_backend": os.environ.get("STORAGE_BACKEND", "local"),
    }


# --- Startup ---

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"Storage backend: {os.environ.get('STORAGE_BACKEND', 'local')}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
