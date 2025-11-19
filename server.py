
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ဒီလိုပြောင်းပါ
import sqlite3
import os
from datetime import datetime
from admin_routes import admin_bp

app = FastAPI(title="Movie API", version="1.0.0")

app.register_blueprint(admin_bp,url_prefix='/api')

# CORS middleware - Allow all origins for Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Database setup
def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            image TEXT,
            telegram_video TEXT NOT NULL,
            telegram_group TEXT NOT NULL,
            genre TEXT,
            year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data if table is empty
    cursor.execute('SELECT COUNT(*) FROM movies')
    if cursor.fetchone()[0] == 0:
        sample_movies = [
            ('The Matrix', 'A computer hacker learns about the true nature of reality', 
             'https://via.placeholder.com/300x450/000000/FFFFFF?text=The+Matrix',
             'https://t.me/movies/123', 'https://t.me/joinchat/ABC123', 'Sci-Fi', 1999),
            ('Inception', 'A thief who steals corporate secrets through dream-sharing',
             'https://via.placeholder.com/300x450/0000FF/FFFFFF?text=Inception',
             'https://t.me/movies/124', 'https://t.me/joinchat/DEF456', 'Action', 2010)
        ]
        
        cursor.executemany('''
            INSERT INTO movies (title, description, image, telegram_video, telegram_group, genre, year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_movies)
        print("✅ Sample movies added to database")
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# API Routes
@app.get("/")
async def root():
    return {
        "message": "🎬 Movie Backend API is running!", 
        "status": "healthy",
        "endpoints": {
            "movies": "/api/movies",
            "health": "/health"
        }
    }

@app.get("/api/movies")
async def get_movies():
    """Get all movies"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM movies ORDER BY created_at DESC')
        movies = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/movies")
async def create_movie(movie: dict):
    """Create new movie"""
    try:
        # Validation
        required_fields = ['title', 'telegram_video', 'telegram_group']
        for field in required_fields:
            if not movie.get(field):
                raise HTTPException(status_code=400, detail=f"{field} is required")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO movies (title, description, image, telegram_video, telegram_group, genre, year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            movie['title'],
            movie.get('description', ''),
            movie.get('image', 'https://via.placeholder.com/300x450/333333/FFFFFF?text=No+Image'),
            movie['telegram_video'],
            movie['telegram_group'],


movie.get('genre', 'General'),
            movie.get('year', datetime.now().year)
        ))
        
        movie_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True, 
            "message": "Movie added successfully", 
            "movie_id": movie_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/movies/{movie_id}")
async def delete_movie(movie_id: int):
    """Delete movie by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if deleted:
            return {"success": True, "message": "Movie deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Movie not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search_movies(q: str = ""):
    """Search movies by title or genre"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if q:
            cursor.execute('''
                SELECT * FROM movies 
                WHERE title LIKE ? OR genre LIKE ? OR description LIKE ?
                ORDER BY created_at DESC
            ''', (f'%{q}%', f'%{q}%', f'%{q}%'))
        else:
            cursor.execute('SELECT * FROM movies ORDER BY created_at DESC')
        
        movies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM movies')
        movie_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "movie_count": movie_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))  # 5000 ပြောင်းပါ
    print(f"🚀 Starting Movie Backend API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)