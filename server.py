from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn

# Simple token verification
def verify_token(token: str):
    # For now, just check if token is provided
    # You can add proper JWT verification later
    return token and len(token) > 10

# Your existing routes
@app.get("/api/movies")
async def get_movies():
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM movies').fetchall()
    conn.close()
    
    movies_list = [dict(movie) for movie in movies]
    return movies_list

@app.get("/health")
async def health_check():
    conn = get_db_connection()
    movie_count = conn.execute('SELECT COUNT(*) as count FROM movies').fetchone()['count']
    conn.close()
    
    return {"status": "healthy", "movie_count": movie_count}

# Admin routes


# Add movie endpoint - FIXED
@app.post("/api/admin/movies")
async def add_movie(request: dict):
    try:
        data = request
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO movies (title, year, genre, description, image, rating, telegram_video, telegram_group)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title'),
            data.get('year', 2024),
            data.get('genre', 'General'),
            data.get('description', ''),
            data.get('image', ''),
            data.get('rating', 7.0),
            data.get('telegram_video'),
            data.get('telegram_group')
        ))
        
        movie_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"success": True, "id": movie_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Delete movie endpoint - FIXED  
@app.delete("/api/admin/movies/{movie_id}")
async def delete_movie(movie_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
        conn.commit()
        conn.close()
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run(app, host='0.0.0.0', port=port)