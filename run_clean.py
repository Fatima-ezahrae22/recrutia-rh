import os
import sys
import subprocess
import time
import uvicorn

def clean_port_8000():
    print("Nettoyage du port 8000...")
    try:
        # Trouver les processus écoutant sur 8000 sous Windows
        output = subprocess.check_output("netstat -ano | findstr :8000", shell=True).decode('utf-8', errors='ignore')
        pids = set()
        for line in output.strip().split('\n'):
            parts = [p for p in line.split() if p]
            if len(parts) >= 5:
                pid = parts[-1]
                pids.add(pid)
        
        for pid in pids:
            if pid != '0':
                print(f"Arret du processus PID {pid} utilisant le port 8000...")
                subprocess.call(f"taskkill /F /PID {pid}", shell=True)
        time.sleep(1)
    except Exception as e:
        print("Aucun processus bloquant ou erreur de nettoyage :", e)

if __name__ == "__main__":
    clean_port_8000()
    print("Démarrage de l'application RecrutIA sur http://127.0.0.1:8000...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
