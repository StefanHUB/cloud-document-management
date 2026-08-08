"""
SQLite database for document metadata.
Uses a lightweight SQLite database to store document records.
In production, this would use a managed cloud database (e.g., Cloud SQL).
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "documents.db"))


def get_connection():
    """Create and return a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_type TEXT NOT NULL,
            storage_region TEXT NOT NULL,
            region_mode TEXT NOT NULL DEFAULT 'cost',
            status TEXT NOT NULL DEFAULT 'pending',
            uploaded_by TEXT NOT NULL,
            uploaded_by_role TEXT NOT NULL,
            reviewed_by TEXT,
            review_comment TEXT,
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            gcs_bucket TEXT,
            gcs_blob_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('manager', 'admin')),
            created_at TEXT NOT NULL
        )
    """)

    # Insert default users if they don't exist
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        cursor.execute(
            "INSERT INTO users (username, email, role, created_at) VALUES (?, ?, ?, ?)",
            ("manager_user", "manager@example.com", "manager", datetime.now().isoformat())
        )
        cursor.execute(
            "INSERT INTO users (username, email, role, created_at) VALUES (?, ?, ?, ?)",
            ("admin_user", "admin@example.com", "admin", datetime.now().isoformat())
        )

    conn.commit()
    conn.close()


def create_document(doc_data: dict) -> dict:
    """Insert a new document record and return it."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO documents (
            title, description, file_name, file_path, file_size, file_type,
            storage_region, region_mode, status, uploaded_by, uploaded_by_role,
            created_at, gcs_bucket, gcs_blob_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_data["title"],
        doc_data.get("description", ""),
        doc_data["file_name"],
        doc_data["file_path"],
        doc_data["file_size"],
        doc_data["file_type"],
        doc_data["storage_region"],
        doc_data.get("region_mode", "cost"),
        "pending",
        doc_data["uploaded_by"],
        doc_data["uploaded_by_role"],
        datetime.now().isoformat(),
        doc_data.get("gcs_bucket"),
        doc_data.get("gcs_blob_name"),
    ))
    conn.commit()
    doc_id = cursor.lastrowid
    conn.close()
    return get_document(doc_id)


def get_document(doc_id: int) -> Optional[dict]:
    """Retrieve a single document by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_documents(status_filter: Optional[str] = None) -> list:
    """Retrieve all documents, optionally filtered by status."""
    conn = get_connection()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute(
            "SELECT * FROM documents WHERE status = ? ORDER BY created_at DESC",
            (status_filter,)
        )
    else:
        cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_document_status(doc_id: int, status: str, reviewed_by: str, comment: str = "") -> Optional[dict]:
    """Update a document's review status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE documents
        SET status = ?, reviewed_by = ?, review_comment = ?, reviewed_at = ?
        WHERE id = ?
    """, (status, reviewed_by, comment, datetime.now().isoformat(), doc_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return get_document(doc_id) if affected > 0 else None


def delete_document(doc_id: int) -> bool:
    """Delete a document record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def get_user_by_username(username: str) -> Optional[dict]:
    """Retrieve a user by username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
