import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn

SECRET_KEY = os.environ.get('JWT_SECRET', 'fallback-secret-key')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_admin = data['admin']
        except:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_admin, *args, **kwargs)
    
    return decorated

def generate_token(username):
    return jwt.encode({
        'admin': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm='HS256')