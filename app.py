import os
import sqlite3
import datetime
import secrets
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Crea la cartella uploads se non esiste
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Percorso del database
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'handtinder.db')

# Estensioni consentite per le immagini
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Funzione per ottenere una connessione al database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Inizializza il database
def init_db():
    conn = get_db_connection()

    # Tabella utenti
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabella foto mani
    conn.execute('''
        CREATE TABLE IF NOT EXISTS hand_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Tabella swipes (like/dislike)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS swipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            swiper_id INTEGER NOT NULL,
            photo_id INTEGER NOT NULL,
            direction TEXT NOT NULL,
            body_part_preference TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (swiper_id) REFERENCES users (id),
            FOREIGN KEY (photo_id) REFERENCES hand_photos (id),
            UNIQUE(swiper_id, photo_id)
        )
    ''')

    # Tabella matches
    conn.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            user1_body_part TEXT,
            user2_body_part TEXT,
            user1_photo_path TEXT,
            user2_photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES users (id),
            FOREIGN KEY (user2_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

# Inizializza il database all'avvio
init_db()

# Route principale - Reindirizza al login se non autenticato
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('swipe'))

# Route per la registrazione
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('register.html', error='Username e password sono richiesti')

        conn = get_db_connection()

        # Verifica se l'utente esiste già
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if existing_user:
            conn.close()
            return render_template('register.html', error='Username già esistente')

        # Crea il nuovo utente
        password_hash = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()

        # Ottieni l'ID dell'utente appena creato
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        # Login automatico dopo la registrazione
        session['user_id'] = user['id']
        session['username'] = user['username']

        return redirect(url_for('upload_hand'))

    return render_template('register.html')

# Route per il login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('swipe'))

        return render_template('login.html', error='Username o password non validi')

    return render_template('login.html')

# Route per il logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Route per caricare una foto della mano
@app.route('/upload', methods=['GET', 'POST'])
def upload_hand():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'hand_photo' not in request.files:
            return render_template('upload.html', error='Nessun file selezionato')

        file = request.files['hand_photo']
        description = request.form.get('description', '')

        if file.filename == '':
            return render_template('upload.html', error='Nessun file selezionato')

        if file and allowed_file(file.filename):
            filename = secure_filename(f"{session['user_id']}_{datetime.datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Salva nel database
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO hand_photos (user_id, photo_path, description) VALUES (?, ?, ?)',
                (session['user_id'], filename, description)
            )
            conn.commit()
            conn.close()

            return redirect(url_for('swipe'))

        return render_template('upload.html', error='Formato file non valido')

    return render_template('upload.html')

# Route per lo swipe
@app.route('/swipe')
def swipe():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('swipe.html', username=session['username'])

# API per ottenere la prossima mano da valutare
@app.route('/api/next_hand', methods=['GET'])
def next_hand():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401

    conn = get_db_connection()

    # Ottieni una foto che l'utente non ha ancora swipato e che non è sua
    hand = conn.execute('''
        SELECT hp.* FROM hand_photos hp
        LEFT JOIN swipes s ON hp.id = s.photo_id AND s.swiper_id = ?
        WHERE hp.user_id != ? AND s.id IS NULL
        ORDER BY RANDOM()
        LIMIT 1
    ''', (session['user_id'], session['user_id'])).fetchone()

    conn.close()

    if hand:
        return jsonify({
            'id': hand['id'],
            'photo_path': f"/static/uploads/{hand['photo_path']}",
            'description': hand['description']
        })

    return jsonify({'message': 'Nessuna nuova mano da valutare'}), 404

# API per salvare uno swipe
@app.route('/api/swipe', methods=['POST'])
def save_swipe():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401

    data = request.json
    photo_id = data.get('photo_id')
    direction = data.get('direction')  # 'left' o 'right'
    body_part = data.get('body_part')  # parte del corpo che piace all'utente

    if not photo_id or not direction:
        return jsonify({'error': 'Dati mancanti'}), 400

    conn = get_db_connection()

    # Salva lo swipe
    conn.execute(
        'INSERT INTO swipes (swiper_id, photo_id, direction, body_part_preference) VALUES (?, ?, ?, ?)',
        (session['user_id'], photo_id, direction, body_part)
    )
    conn.commit()

    # Se è un like (right swipe), controlla se c'è un match
    match_result = None
    if direction == 'right':
        # Ottieni l'owner della foto
        photo = conn.execute('SELECT user_id FROM hand_photos WHERE id = ?', (photo_id,)).fetchone()
        photo_owner_id = photo['user_id']

        # Controlla se il proprietario della foto ha già fatto like a una foto dell'utente corrente
        mutual_like = conn.execute('''
            SELECT s.*, hp.user_id, s.body_part_preference
            FROM swipes s
            JOIN hand_photos hp ON s.photo_id = hp.id
            WHERE s.swiper_id = ? AND hp.user_id = ? AND s.direction = 'right'
            LIMIT 1
        ''', (photo_owner_id, session['user_id'])).fetchone()

        if mutual_like:
            # È un match!
            conn.execute(
                '''INSERT INTO matches (user1_id, user2_id, user1_body_part, user2_body_part)
                   VALUES (?, ?, ?, ?)''',
                (session['user_id'], photo_owner_id, body_part, mutual_like['body_part_preference'])
            )
            conn.commit()

            # Ottieni il nome utente del match
            match_user = conn.execute('SELECT username FROM users WHERE id = ?', (photo_owner_id,)).fetchone()

            match_result = {
                'match': True,
                'username': match_user['username'],
                'your_preference': body_part,
                'their_preference': mutual_like['body_part_preference']
            }

    conn.close()

    if match_result:
        return jsonify(match_result)

    return jsonify({'success': True})

# Route per visualizzare i match
@app.route('/matches')
def matches():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Ottieni tutti i match dell'utente
    user_matches = conn.execute('''
        SELECT m.*,
               CASE
                   WHEN m.user1_id = ? THEN u2.username
                   ELSE u1.username
               END as match_username,
               CASE
                   WHEN m.user1_id = ? THEN m.user2_body_part
                   ELSE m.user1_body_part
               END as their_preference,
               CASE
                   WHEN m.user1_id = ? THEN m.user1_body_part
                   ELSE m.user2_body_part
               END as your_preference
        FROM matches m
        JOIN users u1 ON m.user1_id = u1.id
        JOIN users u2 ON m.user2_id = u2.id
        WHERE m.user1_id = ? OR m.user2_id = ?
        ORDER BY m.created_at DESC
    ''', (session['user_id'], session['user_id'], session['user_id'], session['user_id'], session['user_id'])).fetchall()

    conn.close()

    return render_template('matches.html', matches=user_matches, username=session['username'])

# Route per il profilo utente
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Ottieni le foto dell'utente
    user_photos = conn.execute(
        'SELECT * FROM hand_photos WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()

    # Ottieni statistiche
    total_likes_given = conn.execute(
        'SELECT COUNT(*) as count FROM swipes WHERE swiper_id = ? AND direction = "right"',
        (session['user_id'],)
    ).fetchone()['count']

    total_swipes = conn.execute(
        'SELECT COUNT(*) as count FROM swipes WHERE swiper_id = ?',
        (session['user_id'],)
    ).fetchone()['count']

    total_matches = conn.execute(
        'SELECT COUNT(*) as count FROM matches WHERE user1_id = ? OR user2_id = ?',
        (session['user_id'], session['user_id'])
    ).fetchone()['count']

    conn.close()

    return render_template('profile.html',
                         photos=user_photos,
                         stats={
                             'likes_given': total_likes_given,
                             'total_swipes': total_swipes,
                             'matches': total_matches
                         },
                         username=session['username'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
