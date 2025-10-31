#!/usr/bin/env python3
"""
Script per creare un URL pubblico per HandTinder
Prova diversi metodi di tunneling in ordine
"""

import subprocess
import sys
import time
import os

def print_banner():
    print("=" * 60)
    print("👋 HandTinder - Creazione URL Pubblico")
    print("=" * 60)
    print()

def check_server():
    """Controlla se Flask è in esecuzione sulla porta 5000"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    sock.close()
    return result == 0

def method_localtunnel():
    """Prova localtunnel"""
    print("🔄 Tentativo con LocalTunnel...")
    try:
        result = subprocess.run(
            ['npx', 'localtunnel', '--port', '5000'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ LocalTunnel avviato!")
            return True
    except Exception as e:
        print(f"❌ LocalTunnel fallito: {e}")
    return False

def method_serveo():
    """Prova serveo.net"""
    print("🔄 Tentativo con Serveo...")
    try:
        # serveo.net usa SSH redirect
        subprocess.Popen(
            ['ssh', '-R', '80:localhost:5000', 'serveo.net'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(5)
        print("✅ Serveo avviato!")
        print("⚠️  Controlla l'output SSH per l'URL")
        return True
    except Exception as e:
        print(f"❌ Serveo fallito: {e}")
    return False

def show_alternatives():
    """Mostra alternative manuali"""
    print("\n" + "=" * 60)
    print("📱 ALTERNATIVE PER ACCEDERE DA IPHONE")
    print("=" * 60)
    print()
    print("OPZIONE 1: Deploy su Render.com (CONSIGLIATO)")
    print("1. Vai su https://render.com")
    print("2. 'New +' → 'Web Service'")
    print("3. Connetti il repo GitHub: sidi-international/6")
    print("4. Branch: claude/tinder-hand-rating-app-011CUfPUDheLyadp9dUygtrX")
    print("5. Clicca 'Create Web Service'")
    print("   URL finale: https://handtinder.onrender.com")
    print()
    print("OPZIONE 2: Deploy su Replit (PIÙ SEMPLICE)")
    print("1. Vai su https://replit.com")
    print("2. 'Import from GitHub'")
    print("3. Repo: sidi-international/6")
    print("4. Branch: claude/tinder-hand-rating-app-011CUfPUDheLyadp9dUygtrX")
    print("5. Clicca 'Run' - URL pubblico automatico!")
    print()
    print("OPZIONE 3: Stessa rete WiFi")
    print(f"Se iPhone e computer sono sulla stessa rete WiFi:")
    print(f"URL: http://[TUO_IP]:5000")
    print()
    print("=" * 60)

def main():
    print_banner()

    # Controlla se Flask è in esecuzione
    if not check_server():
        print("⚠️  Flask non sembra essere in esecuzione sulla porta 5000")
        print("   Avvia prima l'applicazione con: python app.py")
        print()
        response = input("Continuare comunque? (s/n): ")
        if response.lower() != 's':
            sys.exit(0)
    else:
        print("✅ Flask in esecuzione sulla porta 5000")
        print()

    # Prova i vari metodi
    print("Provo diversi metodi di tunneling...")
    print()

    success = False

    # Metodo 1: LocalTunnel
    if method_localtunnel():
        success = True

    # Metodo 2: Serveo
    if not success and method_serveo():
        success = True

    if not success:
        print("\n❌ Nessun metodo di tunneling automatico ha funzionato")
        print("   Probabilmente ci sono restrizioni di rete nell'ambiente")
        print()

    # Mostra sempre le alternative
    show_alternatives()
    print()
    print("💡 SUGGERIMENTO: Render o Replit sono le opzioni più affidabili!")
    print()

if __name__ == "__main__":
    main()
