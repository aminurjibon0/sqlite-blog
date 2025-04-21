from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'blog.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('INSERT INTO posts (title, content, timestamp) VALUES (?, ?, ?)', (title, content, timestamp))
        conn.commit()
        return redirect('/')
    
    posts = cursor.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()

        cursor.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, post_id))
        conn.commit()
        conn.close()
        return redirect('/')

    post = cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    
    if post is None:
        return 'Post not found', 404
    
    return render_template('edit.html', post=post)

@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    if request.method == 'GET':
        return get_posts_api()
    else:
        return create_post_api()
    
def get_posts_api():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(post) for post in posts])

def create_post_api():
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()

    if not title or not content:
        return jsonify({'error': 'Title and content are required'})
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO posts (title, content, timestamp) VALUES (?, ?, ?)',
        (title, content, timestamp)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Post created successfully!'}), 201

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post_api(post_id):
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400
    
    conn = get_db_connection()
    post = conn.execute(
        'SELECT * FROM posts WHERE id = ?', (post_id,)
    ).fetchone()

    if post is None:
        conn.close()
        return jsonify({'error': 'Post not found'}), 404
    
    conn.execute(
        'UPDATE posts SET title = ?, content = ? WHERE id = ?',
        (title, content, post_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': f'Post {post_id} updated successfully'})

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post_api(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if post is None:
        conn.close()
        return jsonify({'error': 'Post not found'}), 404
    
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Post {post_id} deleted successfully'})

if __name__=='__main__':
    app.run(debug=True)