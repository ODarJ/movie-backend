from flask import Blueprint, request, jsonify
from auth import token_required, generate_token, get_db_connection
import os

admin_bp = Blueprint('admin', name)

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'success': False, 'message': 'Password is required'})
        
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if admin_password and password == admin_password:
            token = generate_token('admin')
            return jsonify({
                'success': True, 
                'token': token,
                'message': 'Login successful'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid password'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/admin/movies', methods=['POST'])
@token_required
def add_movie(current_admin):
    data = request.get_json()
    
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
    
    return jsonify({'success': True, 'id': movie_id})

@admin_bp.route('/admin/movies/<int:movie_id>', methods=['DELETE'])
@token_required
def delete_movie(current_admin, movie_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})