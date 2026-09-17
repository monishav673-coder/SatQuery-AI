import sqlite3
import os
import json
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'satquery.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            preferred_language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Analyses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            user_email TEXT,
            mode TEXT NOT NULL,
            query TEXT NOT NULL,
            confidence_score INTEGER,
            confidence_level TEXT,
            buildings_count INTEGER DEFAULT 0,
            water_count INTEGER DEFAULT 0,
            water_pct REAL DEFAULT 0.0,
            agri_pct REAL DEFAULT 0.0,
            result_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_user(email, password, preferred_language='en'):
    email = email.strip().lower()
    if not email or '@' not in email:
        return False, "Invalid email address format."
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters."
    
    password_hash = generate_password_hash(password)
    user_id = str(uuid.uuid4())
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (id, email, password_hash, preferred_language) VALUES (?, ?, ?, ?)',
            (user_id, email, password_hash, preferred_language)
        )
        conn.commit()
        return True, {"id": user_id, "email": email, "preferred_language": preferred_language}
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    finally:
        conn.close()

def verify_user(email, password):
    email = email.strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        return True, {
            "id": user['id'],
            "email": user['email'],
            "preferred_language": user['preferred_language']
        }
    return False, "Invalid email or password."

def update_user_language(email, language):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET preferred_language = ? WHERE email = ?', (language, email.strip().lower()))
    conn.commit()
    conn.close()

def save_analysis(user_email, mode, query, result_dict):
    analysis_id = result_dict.get('analysis_id') or str(uuid.uuid4())
    conf = result_dict.get('result', {}).get('confidence', {})
    conf_score = conf.get('score', 0)
    conf_level = conf.get('level', 'Moderate')
    
    bldg_count = result_dict.get('result', {}).get('buildings', {}).get('count', 0)
    water_data = result_dict.get('result', {}).get('water_bodies', {})
    water_count = water_data.get('count', 0)
    water_pct = water_data.get('coverage_percentage', 0.0)
    agri_pct = result_dict.get('result', {}).get('land_cover', {}).get('agriculture', 0.0)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user_id if exists
    cursor.execute('SELECT id FROM users WHERE email = ?', (user_email.strip().lower() if user_email else '',))
    user_row = cursor.fetchone()
    user_id = user_row['id'] if user_row else None
    
    cursor.execute('''
        INSERT INTO analyses (
            id, user_id, user_email, mode, query, 
            confidence_score, confidence_level, buildings_count, 
            water_count, water_pct, agri_pct, result_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        analysis_id, user_id, user_email, mode, query,
        conf_score, conf_level, bldg_count,
        water_count, water_pct, agri_pct, json.dumps(result_dict)
    ))
    conn.commit()
    conn.close()
    return analysis_id

def get_analysis_by_id(analysis_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row['result_json'])
    return None

def get_user_history(user_email, limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, mode, query, confidence_score, confidence_level, 
               buildings_count, water_count, water_pct, agri_pct, created_at
        FROM analyses
        WHERE user_email = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_email.strip().lower(), limit))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        history.append({
            "id": r['id'],
            "mode": r['mode'],
            "query": r['query'],
            "confidence_score": r['confidence_score'],
            "confidence_level": r['confidence_level'],
            "buildings_count": r['buildings_count'],
            "water_count": r['water_count'],
            "water_pct": r['water_pct'],
            "agri_pct": r['agri_pct'],
            "created_at": r['created_at']
        })
    return history
