import sqlite3
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect
from rag import search, generate, add_document, get_document_count, reset_collection


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')


def init_db():
    conn = sqlite3.connect('messages.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS messages
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT NOT NULL,
         email TEXT NOT NULL,
         phone TEXT DEFAULT '',
         message TEXT NOT NULL,
         created_at TEXT NOT NULL)''')
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    message = data.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({'success': False, 'error': 'Tous les champs sont requis.'}), 400

    conn = sqlite3.connect('messages.db')
    conn.execute('INSERT INTO messages (name, email, phone, message, created_at) VALUES (?, ?, ?, ?, ?)',
                 (name, email, phone, message, datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        return render_template('admin.html', error='Mot de passe incorrect')

    if not session.get('admin'):
        return render_template('admin.html')

    conn = sqlite3.connect('messages.db')
    rows = conn.execute('SELECT * FROM messages ORDER BY id DESC').fetchall()
    conn.close()

    messages = [{'id': r[0], 'name': r[1], 'email': r[2], 'phone': r[3], 'message': r[4], 'date': r[5]} for r in rows]
    return render_template('admin.html', messages=messages)


@app.route('/admin/logout')
def logout():
    session.pop('admin', None)
    return redirect('/admin')


@app.route('/api/rag', methods=['POST'])
def api_rag():
    data = request.json
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'answer': 'Veuillez poser une question.'})

    docs = search(query)
    if not docs:
        return jsonify({'answer': 'Je ne trouve pas de réponse dans ma base de connaissances.'})

    context = '\n\n'.join(docs)
    answer = generate(query, context)
    return jsonify({'answer': answer})


@app.route('/api/rag/info')
def api_rag_info():
    return jsonify({'count': get_document_count()})


@app.route('/api/rag/add', methods=['POST'])
def api_rag_add():
    data = request.json
    text = data.get('text', '').strip()
    filename = data.get('filename', 'admin-upload.txt')
    if not text:
        return jsonify({'success': False, 'error': 'Texte vide'}), 400
    chunks = add_document(text, filename)
    return jsonify({'success': True, 'chunks': chunks})


@app.route('/api/rag/clear', methods=['POST'])
def api_rag_clear():
    import chromadb
    from chromadb.config import Settings
    client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), 'chroma_data'), settings=Settings(anonymized_telemetry=False))
    try:
        client.delete_collection('documents')
        reset_collection()
        return jsonify({'success': True})
    except Exception:
        reset_collection()
        return jsonify({'success': False, 'error': 'Aucune collection à supprimer'})


CARROUSEL_DIR = os.path.join(os.path.dirname(__file__), 'static', 'image carrousel')
os.makedirs(CARROUSEL_DIR, exist_ok=True)


@app.route('/api/carrousel/list')
def api_carrousel_list():
    files = []
    for f in sorted(os.listdir(CARROUSEL_DIR)):
        ext = os.path.splitext(f)[1].lower()
        if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            files.append({'filename': f})
    return jsonify(files)


@app.route('/api/carrousel/upload', methods=['POST'])
def api_carrousel_upload():
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier'}), 400
    files = request.files.getlist('files')
    uploaded = []
    for f in files:
        if f.filename:
            f.save(os.path.join(CARROUSEL_DIR, f.filename))
            uploaded.append(f.filename)
    return jsonify({'success': True, 'uploaded': uploaded})


@app.route('/api/carrousel/delete', methods=['POST'])
def api_carrousel_delete():
    data = request.json
    filename = data.get('filename', '')
    filepath = os.path.join(CARROUSEL_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Fichier introuvable'}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
