# 👋 HandTinder

Un'applicazione web tipo Tinder per valutare e matchare le mani più belle!

## 🎯 Descrizione

HandTinder è un'applicazione web interattiva che permette agli utenti di:
- Caricare foto delle proprie mani
- Fare swipe (scorri a destra o sinistra) sulle foto delle mani di altri utenti
- Esprimere preferenze su quali parti del corpo vorrebbero ricevere in cambio
- Ottenere match quando due persone si piacciono reciprocamente

## ✨ Funzionalità

### 🔐 Autenticazione
- Registrazione utente
- Login/Logout sicuro
- Sessioni utente con Flask

### 📸 Upload Foto
- Caricamento di foto delle mani
- Supporto per immagini PNG, JPG, JPEG, GIF
- Aggiunta di descrizioni opzionali

### 💕 Sistema Swipe
- Interfaccia stile Tinder con carte scorrevoli
- Swipe a destra (like) o a sinistra (dislike)
- Drag and drop delle carte
- Animazioni fluide

### 🎁 Preferenze Corpo
- Quando fai like, scegli quale parte del corpo vorresti vedere:
  - Piedi
  - Gambe
  - Braccia
  - Viso
  - Capelli
  - Occhi
  - Sorriso
  - Altro

### 🎉 Sistema Match
- Match automatico quando due persone si piacciono reciprocamente
- Notifica immediata del match
- Visualizzazione delle preferenze reciproche
- Lista di tutti i match ottenuti

### 👤 Profilo Utente
- Visualizzazione delle proprie foto caricate
- Statistiche personali:
  - Swipe totali
  - Like dati
  - Match ottenuti

## 🛠️ Tecnologie Utilizzate

### Backend
- **Python 3.11**
- **Flask 2.3.3** - Framework web
- **SQLite** - Database
- **Werkzeug** - Gestione password e sicurezza

### Frontend
- **HTML5**
- **CSS3** - Animazioni e gradients
- **JavaScript ES6+** - Logica interattiva
- **Bootstrap 5.3** - Framework CSS

### Database
- **SQLite** con 4 tabelle:
  - `users` - Utenti registrati
  - `hand_photos` - Foto delle mani
  - `swipes` - Cronologia degli swipe
  - `matches` - Match tra utenti

## 📦 Installazione

1. **Clona il repository**
```bash
git clone <repository-url>
cd 6
```

2. **Installa le dipendenze**
```bash
pip install -r requirements.txt
```

3. **Avvia l'applicazione**
```bash
python app.py
```

4. **Apri il browser**
```
http://localhost:5000
```

## 🚀 Utilizzo

### 1. Registrazione
- Vai su `/register`
- Crea un account con username e password

### 2. Carica una foto
- Dopo la registrazione, carica la prima foto della tua mano
- Aggiungi una descrizione (opzionale)

### 3. Swipe!
- Scorri le foto delle mani di altri utenti
- Swipe a destra (♥) se ti piace
- Swipe a sinistra (✕) se non ti interessa
- Quando fai like, scegli quale parte del corpo vorresti vedere

### 4. Match
- Quando due persone si fanno like reciprocamente, si crea un match!
- Ricevi una notifica immediata
- Puoi vedere le preferenze reciproche

### 5. Profilo
- Controlla le tue statistiche
- Vedi tutte le tue foto caricate
- Carica nuove foto

## 📁 Struttura del Progetto

```
6/
├── app.py                  # Applicazione Flask principale
├── requirements.txt        # Dipendenze Python
├── README.md              # Documentazione
├── data/
│   └── handtinder.db      # Database SQLite (creato automaticamente)
├── static/
│   ├── css/
│   │   └── style.css      # Stili CSS (non utilizzato, stili inline)
│   ├── js/
│   │   └── script.js      # Logica JavaScript per swipe
│   └── uploads/           # Cartella per le foto caricate
└── templates/
    ├── login.html         # Pagina di login
    ├── register.html      # Pagina di registrazione
    ├── upload.html        # Pagina upload foto
    ├── swipe.html         # Interfaccia principale swipe
    ├── matches.html       # Lista dei match
    └── profile.html       # Profilo utente
```

## 🔒 Sicurezza

- Password hashate con Werkzeug
- Sessioni sicure con Flask
- Validazione dei file upload
- Protezione contro SQL injection con parametri preparati
- Limite dimensione file (16MB)

## 🎨 Design

- Design moderno con gradienti viola
- Animazioni fluide per lo swipe
- Responsive design per mobile e desktop
- Interfaccia intuitiva stile Tinder

## 🚧 Funzionalità Future

- [ ] Chat tra match
- [ ] Upload multiplo di foto
- [ ] Filtri e preferenze avanzate
- [ ] Sistema di report utenti
- [ ] Verifica profili
- [ ] Geolocalizzazione
- [ ] Notifiche push
- [ ] Condivisione foto delle parti del corpo preferite dopo il match

## 📝 Note

- Questa è un'applicazione dimostrativa
- Non utilizzare in produzione senza ulteriori misure di sicurezza
- Il database viene creato automaticamente all'avvio

## 👨‍💻 Sviluppo

L'applicazione è stata sviluppata con Flask in modalità debug. Per la produzione:

1. Disabilita il debug mode in `app.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

2. Usa un server WSGI come Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📜 Licenza

Questo progetto è stato creato per scopi educativi e dimostrativi.

---

**Buon divertimento con HandTinder! 👋💕**
