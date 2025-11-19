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
@app.post("/api/admin/login")
async def admin_login(request: dict):
    try:
        password = request.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not password:
            return {"success": False, "message": "Password is required"}
        
        if admin_password and password == admin_password:
            # Simple token for now
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

@app.post("/api/admin/movies")
async def add_movie(request: dict, authorization: str = None):
    # Check authorization
    if not authorization or not verify_token(authorization.replace('Bearer ', '')):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = request
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO movies (title, year, genre, description, image, rating, telegram_video, telegram_group)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['title'], data['year'], data['genre'], 
        data['description'], data['image'], data['rating'],
        data['telegram_video'], data['telegram_group']
    ))
    
    movie_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"success": True, "id": movie_id}

@app.delete("/api/admin/movies/{movie_id}")
async def delete_movie(movie_id: int, authorization: str = None):
    # Check authorization
    if not authorization or not verify_token(authorization.replace('Bearer ', '')):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    conn = get_db_connection()
    conn.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
    conn.commit()
    conn.close()
    
    return {"success": True}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run(app, host='0.0.0.0', port=port)