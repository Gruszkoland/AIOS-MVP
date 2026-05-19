#!/usr/bin/env python3
"""
UAP Local Database Initialization Script
Tworzy lokalną bazę SQLite z schematem MAPI v1.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path("./db/adrion_local.db")

def init_db():
    """Inicjalizuje lokalną bazę SQLite z tabelami MAPI."""
    
    # Tworzenie bazy jeśli nie istnieje
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    print(f"[INIT] Initializing SQLite database: {DB_PATH}")
    
    # Tabelan: tasks (rdzeniowe)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        agent TEXT,
        parameters JSON,
        result JSON,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """)
    print("  [OK] tasks table")
    
    # Table: genesis_records (raporty)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS genesis_records (
        id TEXT PRIMARY KEY,
        record_type TEXT,
        path TEXT,
        content TEXT,
        metadata JSON,
        created_at TIMESTAMP
    )
    """)
    print("  [OK] genesis_records table")
    
    # Table: trust_scores (TSPA [1])
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trust_scores (
        agent_name TEXT PRIMARY KEY,
        score REAL DEFAULT 0.75,
        updated_at TIMESTAMP,
        history JSON
    )
    """)
    print("  [OK] trust_scores table")
    
    # Table: ebdi_states (EBDI baseline)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ebdi_states (
        agent_name TEXT PRIMARY KEY,
        pleasure REAL,
        arousal REAL,
        dominance REAL,
        recorded_at TIMESTAMP
    )
    """)
    print("  [OK] ebdi_states table")
    
    # Insert default agents into trust_scores
    agents = [
        ("librarian", 0.80),
        ("sap", 0.85),
        ("auditor", 0.95),
        ("sentinel", 0.75),
        ("architect", 0.82),
        ("healer", 0.70),
    ]
    
    for agent_name, score in agents:
        cursor.execute("""
        INSERT OR REPLACE INTO trust_scores (agent_name, score, updated_at)
        VALUES (?, ?, ?)
        """, (agent_name, score, datetime.now().isoformat()))
    
    print("  [OK] Default agent scores inserted")
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Database initialized: {DB_PATH}")
    print(f"   Size: {DB_PATH.stat().st_size} bytes")

if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)
