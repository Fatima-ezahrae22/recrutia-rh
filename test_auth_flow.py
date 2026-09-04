import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

print("--- 1. TEST DISPONIBILITE SERVEUR ---")
try:
    res = urllib.request.urlopen(f"{BASE_URL}/rh")
    print(f"[OK] GET /rh -> STATUS {res.status}")
except Exception as e:
    print(f"[ERR] GET /rh ERREUR: {e}")

print("\n--- 2. TEST AUTH LOGIN ---")
login_data = json.dumps({"username": "recruteur", "password": "RecrutIA2026!"}).encode("utf-8")
req = urllib.request.Request(
    f"{BASE_URL}/api/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"}
)

token = None
try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode("utf-8"))
    token = data.get("access_token")
    print(f"[OK] POST /api/auth/login -> STATUS {res.status}")
    print(f"TOKEN RECUPERE: {token[:30]}...")
except Exception as e:
    print(f"[ERR] POST /api/auth/login ERREUR: {e}")

print("\n--- 3. TEST GET /api/auth/me ---")
if token:
    req_me = urllib.request.Request(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        res = urllib.request.urlopen(req_me)
        user_data = json.loads(res.read().decode("utf-8"))
        print(f"[OK] GET /api/auth/me -> STATUS {res.status}")
        print(f"USER: {user_data.get('username')}")
    except Exception as e:
        print(f"[ERR] GET /api/auth/me ERREUR: {e}")

print("\n--- 4. TEST LISTER OFFRES (PROTEGE) ---")
if token:
    req_offres = urllib.request.Request(
        f"{BASE_URL}/api/offres",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        res = urllib.request.urlopen(req_offres)
        offres = json.loads(res.read().decode("utf-8"))
        print(f"[OK] GET /api/offres -> STATUS {res.status}")
        print(f"NOMBRE D OFFRES TROUVEES: {len(offres)}")
        for o in offres:
            print(f"  - Offre #{o.get('id')}: {o.get('titre')}")
    except Exception as e:
        print(f"[ERR] GET /api/offres ERREUR: {e}")

print("\n--- 5. TEST LISTER CANDIDATURES (PROTEGE) ---")
if token:
    req_cands = urllib.request.Request(
        f"{BASE_URL}/api/candidatures/toutes",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        res = urllib.request.urlopen(req_cands)
        cands = json.loads(res.read().decode("utf-8"))
        print(f"[OK] GET /api/candidatures/toutes -> STATUS {res.status}")
        print(f"NOMBRE DE CANDIDATURES: {len(cands)}")
    except Exception as e:
        print(f"[ERR] GET /api/candidatures/toutes ERREUR: {e}")

print("\n--- ALL BACKEND TESTS COMPLETE ---")
