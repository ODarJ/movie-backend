
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql://'):
        try:
            # PostgreSQL connection
            conn = psycopg2.connect(database_url, sslmode='require')
            return conn
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            print("Falling back to SQLite...")
    
    # SQLite fallback
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                year INTEGER,
                genre TEXT,
                description TEXT,
                image TEXT,
                telegram_video TEXT,
                telegram_group TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("✅ Database table created/checked")
    except Exception as e:
        print(f"Database init error: {e}")
    finally:
        conn.close()

# Initialize database on startup
init_database()

@app.post("/api/admin/login")
async def admin_login(request: dict):
    try:
        password = request.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not password:
            return {"success": False, "message": "Password is required"}
        
        if admin_password and password == admin_password:
            token = "fastapi_token_" + password
            return {
                "success": True, 
                "token": token,
                "message": "Login successful"
            }
        else:
            return {"success": False, "message": "Invalid password"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/movies")
async def get_movies():
    try:
        conn = get_db_connection()
        
        if isinstance(conn, psycopg2.extensions.connection):
            # PostgreSQL
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM movies ORDER BY created_at DESC')
            movies = cursor.fetchall()
            result = [dict(movie) for movie in movies]
        else:
            # SQLite
            movies = conn.execute('SELECT * FROM movies ORDER BY created_at DESC').fetchall()
            result = [dict(movie) for movie in movies]
        
        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/admin/movies")
async def add_movie(request: dict):
    try:
        data = request
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if isinstance(conn, psycopg2.extensions.connection):
            # PostgreSQL
            cursor.execute('''
                INSERT INTO movies (title, year, genre, description, image, telegram_video, telegram_group)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                data.get('title'),
                data.get('year', 2024),
                data.get('genre', 'General'),
                data.get('description', ''),
                data.get('image', ''),
                data.get('telegram_video'),
data.get('telegram_group')
            ))
            movie_id = cursor.fetchone()[0]
        else:
            # SQLite
            cursor.execute('''
                INSERT INTO movies (title, year, genre, description, image, telegram_video, telegram_group)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('title'),
                data.get('year', 2024),
                data.get('genre', 'General'),
                data.get('description', ''),
                data.get('image', ''),
                data.get('telegram_video'),
                data.get('telegram_group')
            ))
            movie_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return {"success": True, "id": movie_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/movies/{movie_id}")
async def delete_movie(movie_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if isinstance(conn, psycopg2.extensions.connection):
            cursor.execute('DELETE FROM movies WHERE id = %s', (movie_id,))
        else:
            cursor.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
        
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM movies')
        
        if isinstance(conn, psycopg2.extensions.connection):
            movie_count = cursor.fetchone()[0]
            db_type = "postgresql"
        else:
            movie_count = cursor.fetchone()[0]
            db_type = "sqlite"
        
        conn.close()
        return {
            "status": "healthy", 
            "database": db_type,
            "movie_count": movie_count
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run(app, host='0.0.0.0', port=port)