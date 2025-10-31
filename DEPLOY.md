# HandTinder - Deploy su Render

## 🚀 Deploy Automatico

Segui questi passaggi per avere HandTinder accessibile dal tuo iPhone:

### Opzione 1: Deploy su Render (CONSIGLIATO)

1. **Vai su [render.com](https://render.com)** e crea un account gratuito
2. **Clicca "New +"** → **"Web Service"**
3. **Connetti il repository GitHub:** `sidi-international/6`
4. **Seleziona il branch:** `claude/tinder-hand-rating-app-011CUfPUDheLyadp9dUygtrX`
5. **Configura:**
   - Name: `handtinder`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
6. **Clicca "Create Web Service"**

Dopo 2-3 minuti avrai un URL tipo: **https://handtinder.onrender.com**

### Opzione 2: Deploy su Railway

1. **Vai su [railway.app](https://railway.app)** e accedi con GitHub
2. **"New Project"** → **"Deploy from GitHub repo"**
3. **Seleziona:** `sidi-international/6`
4. Railway farà il deploy automaticamente

URL finale: **https://handtinder.up.railway.app**

### Opzione 3: Deploy su Fly.io

```bash
# Installa Fly CLI (se non hai restrizioni)
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

### Opzione 4: Replit (più semplice)

1. **Vai su [replit.com](https://replit.com)**
2. **Import from GitHub:** `sidi-international/6`
3. **Branch:** `claude/tinder-hand-rating-app-011CUfPUDheLyadp9dUygtrX`
4. **Run** - Replit fornirà un URL pubblico automaticamente

## 📱 URL Locale (se sei sulla stessa rete WiFi)

Se il tuo iPhone è sulla stessa rete WiFi del computer:

```
http://[IP_DEL_TUO_COMPUTER]:5000
```

Per trovare l'IP:
- Mac/Linux: `ifconfig` o `ip addr`
- Windows: `ipconfig`

---

**Consiglio:** Usa **Render** o **Replit** - sono i più veloci e non richiedono configurazione! 🚀
