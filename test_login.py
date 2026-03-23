import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("RELIF_JWT_TOKEN")
print(f"Token encontrado: {'Sí' if token else 'No'}")

print("Probando query...")
try:
    r = requests.post(
        "https://relif-saas-back-workload-816446680429.southamerica-west1.run.app/admin/db/execute",
        headers={"Authorization": f"Bearer {token}"},
        json={"userQuery": 'SELECT COUNT(*) FROM "BankOfferRequests"'},
        timeout=15,
    )
    print(f"Status: {r.status_code}")
    print(f"Respuesta: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
