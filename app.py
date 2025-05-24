import os
import sqlite3
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import openai
import json
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Configurazione OpenAI
# Usa la API Key da una variabile di ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")
# Configurazione dell'applicazione
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24))

# Configurazione del modello AI
AI_MODEL = os.environ.get("AI_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.3"))
ENABLE_AI = os.environ.get("ENABLE_AI", "True").lower() in ("true", "1", "t")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Percorso del database
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'riza_database.db')

# Funzione per ottenere una connessione al database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Funzione per ottenere tutte le discipline/ambiti
def get_discipline():
    conn = get_db_connection()
    discipline = conn.execute('SELECT DISTINCT disciplina_ambito FROM rubriche').fetchall()
    conn.close()
    return [d['disciplina_ambito'] for d in discipline]

# Funzione per ottenere i suggerimenti basati sull'osservazione utilizzando OpenAI
def get_ai_suggestions(osservazione, disciplina, max_suggestions=5):
    if not ENABLE_AI:
        return get_tfidf_suggestions(osservazione, disciplina, max_suggestions)
        
    conn = get_db_connection()
    
    # Ottieni tutti i descrittori per la disciplina selezionata
    descrittori = conn.execute(
        'SELECT id, dimensione_riza, processo_specifico_verbo, livello, testo_descrittore FROM rubriche WHERE disciplina_ambito = ?',
        (disciplina,)
    ).fetchall()
    
    if not descrittori:
        conn.close()
        return []
    
    # Prepara il contesto per l'AI
    context = f"""
    Analizza la seguente osservazione di un docente su un allievo nell'ambito della disciplina '{disciplina}' 
    e suggerisci le classificazioni più appropriate secondo il modello RIZA (Risorse, Interpretazione, aZione, Autoregolazione).
    
    Osservazione del docente:
    "{osservazione}"
    
    Ecco alcuni descrittori di riferimento per questa disciplina:
    """
    
    # Aggiungi alcuni descrittori di esempio per ogni dimensione RIZA
    dimensioni = ["Interpretazione", "Azione", "Autoregolazione"]
    for dim in dimensioni:
        dim_descrittori = [d for d in descrittori if d['dimensione_riza'] == dim]
        if dim_descrittori:
            # Prendi fino a 2 esempi per ogni dimensione
            examples = dim_descrittori[:2]
            context += f"\n{dim}:\n"
            for ex in examples:
                context += f"- Processo: {ex['processo_specifico_verbo']}, Livello: {ex['livello']}, Descrittore: {ex['testo_descrittore']}\n"
    
    # Aggiungi le istruzioni per l'AI
    context += f"""
    Basandoti sull'osservazione del docente e sui descrittori di riferimento, identifica:
    1. La dimensione RIZA più pertinente (Interpretazione, Azione, Autoregolazione)
    2. Il processo specifico/verbo più appropriato
    3. Il livello di competenza (Iniziale, Base, Intermedio, Avanzato)
    4. Una breve spiegazione del perché questa classificazione è appropriata
    
    Fornisci i {max_suggestions} suggerimenti più pertinenti in formato JSON con i seguenti campi:
    - dimensione_riza
    - processo_specifico_verbo
    - livello
    - testo_descrittore (una descrizione appropriata basata sui descrittori di riferimento)
    - spiegazione
    - similarita (un valore numerico tra 0 e 1 che rappresenta la pertinenza del suggerimento)
    """
    
    try:
        # Chiamata all'API di OpenAI
        response = openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Sei un assistente esperto in valutazione formativa e nel modello RIZA."},
                {"role": "user", "content": context}
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"}
        )
        
        # Estrai la risposta JSON
        result = response.choices[0].message.content
        suggestions_data = json.loads(result)
        
        # Assicurati che la risposta contenga una lista di suggerimenti
        if "suggerimenti" in suggestions_data:
            suggestions = suggestions_data["suggerimenti"]
            
            # Aggiungi gli ID dei descrittori più simili dal database
            for suggestion in suggestions:
                # Trova il descrittore più simile nel database per questo suggerimento
                best_match = None
                best_similarity = -1
                
                for desc in descrittori:
                    if desc['dimensione_riza'] == suggestion['dimensione_riza']:
                        # Calcola una semplice similarità basata su TF-IDF
                        vectorizer = TfidfVectorizer()
                        tfidf_matrix = vectorizer.fit_transform([desc['testo_descrittore'], suggestion['testo_descrittore']])
                        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = desc
                
                if best_match:
                    suggestion['id'] = best_match['id']
                else:
                    # Se non troviamo un match, usa il primo descrittore della stessa dimensione
                    same_dim_desc = [d for d in descrittori if d['dimensione_riza'] == suggestion['dimensione_riza']]
                    if same_dim_desc:
                        suggestion['id'] = same_dim_desc[0]['id']
                    else:
                        suggestion['id'] = descrittori[0]['id']  # Fallback
            
            conn.close()
            return suggestions[:max_suggestions]
        else:
            conn.close()
            return []
            
    except Exception as e:
        print(f"Errore nella chiamata all'API OpenAI: {str(e)}")
        conn.close()
        
        # Fallback al metodo TF-IDF originale in caso di errore
        return get_tfidf_suggestions(osservazione, disciplina, max_suggestions)

# Funzione originale per ottenere suggerimenti basati su TF-IDF (come fallback)
def get_tfidf_suggestions(osservazione, disciplina, max_suggestions=5):
    conn = get_db_connection()
    
    # Ottieni tutti i descrittori per la disciplina selezionata
    descrittori = conn.execute(
        'SELECT id, dimensione_riza, processo_specifico_verbo, livello, testo_descrittore FROM rubriche WHERE disciplina_ambito = ?',
        (disciplina,)
    ).fetchall()
    
    if not descrittori:
        conn.close()
        return []
    
    # Converti i descrittori in liste per l'elaborazione
    ids = [d['id'] for d in descrittori]
    testi = [d['testo_descrittore'] for d in descrittori]
    
    # Aggiungi l'osservazione ai testi per il calcolo della similarità
    tutti_testi = testi + [osservazione]
    
    # Calcola la similarità TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(tutti_testi)
    
    # Calcola la similarità del coseno tra l'osservazione e tutti i descrittori
    cosine_similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1]).flatten()
    
    # Ottieni gli indici dei descrittori più simili
    top_indices = cosine_similarities.argsort()[-max_suggestions:][::-1]
    
    # Prepara i suggerimenti
    suggestions = []
    for idx in top_indices:
        if cosine_similarities[idx] > 0:  # Solo suggerimenti con similarità positiva
            suggestions.append({
                'id': ids[idx],
                'dimensione_riza': descrittori[idx]['dimensione_riza'],
                'processo_specifico_verbo': descrittori[idx]['processo_specifico_verbo'],
                'livello': descrittori[idx]['livello'],
                'testo_descrittore': descrittori[idx]['testo_descrittore'],
                'spiegazione': "Suggerimento basato sulla similarità testuale",
                'similarita': float(cosine_similarities[idx])
            })
    
    conn.close()
    return suggestions

# Funzione per salvare un'osservazione
def save_observation(classe, allievo, disciplina, situazione, osservazione, dimensione, processo, livello, id_descrittore):
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO osservazioni 
           (classe, allievo, disciplina_ambito, situazione_problema_attivita, 
            testo_osservazione, dimensione_riza_validata, processo_specifico_verbo_validato, 
            livello_validato, id_descrittore_suggerito)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (classe, allievo, disciplina, situazione, osservazione, dimensione, processo, livello, id_descrittore)
    )
    conn.commit()
    conn.close()

# Funzione per ottenere le osservazioni salvate per un allievo
def get_observations_for_student(allievo, disciplina=None):
    conn = get_db_connection()
    if disciplina:
        observations = conn.execute(
            '''SELECT * FROM osservazioni 
               WHERE allievo = ? AND disciplina_ambito = ?
               ORDER BY timestamp DESC''',
            (allievo, disciplina)
        ).fetchall()
    else:
        observations = conn.execute(
            '''SELECT * FROM osservazioni 
               WHERE allievo = ?
               ORDER BY timestamp DESC''',
            (allievo,)
        ).fetchall()
    conn.close()
    return observations

# Route principale
@app.route('/')
def index():
    discipline = get_discipline()
    return render_template('index.html', discipline=discipline)

# Route per ottenere suggerimenti
@app.route('/get_suggestions', methods=['POST'])
def suggest():
    data = request.json
    osservazione = data.get('osservazione', '')
    disciplina = data.get('disciplina', '')
    
    if not osservazione or not disciplina:
        return jsonify({'error': 'Osservazione e disciplina sono richiesti'}), 400
    
    # Usa il motore di suggerimento AI
    suggestions = get_ai_suggestions(osservazione, disciplina)
    return jsonify({'suggestions': suggestions})

# Route per salvare un'osservazione
@app.route('/save_observation', methods=['POST'])
def save():
    data = request.json
    classe = data.get('classe', '')
    allievo = data.get('allievo', '')
    disciplina = data.get('disciplina', '')
    situazione = data.get('situazione', '')
    osservazione = data.get('osservazione', '')
    dimensione = data.get('dimensione', '')
    processo = data.get('processo', '')
    livello = data.get('livello', '')
    id_descrittore = data.get('id_descrittore', None)
    
    if not all([classe, allievo, disciplina, osservazione, dimensione, processo, livello]):
        return jsonify({'error': 'Tutti i campi obbligatori devono essere compilati'}), 400
    
    save_observation(classe, allievo, disciplina, situazione, osservazione, dimensione, processo, livello, id_descrittore)
    return jsonify({'success': True})

# Route per visualizzare le osservazioni di un allievo
@app.route('/view_observations', methods=['GET', 'POST'])
def view_observations():
    discipline = get_discipline()
    
    if request.method == 'POST':
        allievo = request.form.get('allievo', '')
        disciplina = request.form.get('disciplina', '')
        
        if not allievo:
            return render_template('view_observations.html', error='Nome allievo richiesto', discipline=discipline)
        
        if disciplina:
            observations = get_observations_for_student(allievo, disciplina)
        else:
            observations = get_observations_for_student(allievo)
        
        return render_template('view_observations.html', 
                              observations=observations, 
                              allievo=allievo, 
                              disciplina=disciplina, 
                              discipline=discipline)
    
    return render_template('view_observations.html', discipline=discipline)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)
