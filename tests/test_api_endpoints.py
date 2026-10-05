"""Integration test for miniBlue FastAPI endpoints and RBAC rules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

print("[STEP 0] Importing TestClient and app...", flush=True)
from fastapi.testclient import TestClient
from api.main import app

print("[STEP 1] Creating TestClient instance...", flush=True)
client = TestClient(app)

def test_all():
    print("[STEP 2] Testing /health...", flush=True)
    h = client.get("/health")
    assert h.status_code == 200, f"Health failed: {h.text}"
    print("✓ Health check passed:", h.json()["status"], flush=True)

    print("[STEP 3] Testing /auth/login for employee...", flush=True)
    l1 = client.post("/api/v1/auth/login", json={"email": "employee@miniblue.dev", "password": "MiniBlue2026!"})
    assert l1.status_code == 200, f"Employee login failed: {l1.text}"
    emp_token = l1.json()["access_token"]
    print("✓ Employee login passed:", l1.json()["full_name"], flush=True)

    print("[STEP 4] Testing /auth/login for manager...", flush=True)
    l2 = client.post("/api/v1/auth/login", json={"email": "manager@miniblue.dev", "password": "MiniBlue2026!"})
    assert l2.status_code == 200, f"Manager login failed: {l2.text}"
    mgr_token = l2.json()["access_token"]
    print("✓ Manager login passed:", l2.json()["full_name"], flush=True)

    print("[STEP 5] Testing /auth/login for admin...", flush=True)
    l3 = client.post("/api/v1/auth/login", json={"email": "admin@miniblue.dev", "password": "MiniBlue2026!"})
    assert l3.status_code == 200, f"Admin login failed: {l3.text}"
    adm_token = l3.json()["access_token"]
    print("✓ Admin login passed:", l3.json()["full_name"], flush=True)

    print("[STEP 6] Testing /telemetry (manager)...", flush=True)
    t = client.get("/api/v1/telemetry", headers={"Authorization": f"Bearer {mgr_token}"})
    assert t.status_code == 200, f"Telemetry failed: {t.text}"
    print("✓ Telemetry passed: total_actions =", t.json()["total_actions"], flush=True)

    print("[STEP 7] Testing RBAC: /audit/verify should be 403 for manager...", flush=True)
    a_forbidden = client.get("/api/v1/audit/verify", headers={"Authorization": f"Bearer {mgr_token}"})
    assert a_forbidden.status_code == 403, "RBAC failed: manager should not access audit verify"
    print("✓ RBAC enforced: manager got 403 Forbidden as expected.", flush=True)

    print("[STEP 8] Testing /audit/verify (admin)...", flush=True)
    a_admin = client.get("/api/v1/audit/verify", headers={"Authorization": f"Bearer {adm_token}"})
    assert a_admin.status_code == 200 and a_admin.json()["valid"] is True, f"Audit verify failed: {a_admin.text}"
    print(f"✓ Audit verify passed: chain valid = {a_admin.json()['valid']}, entries = {a_admin.json()['entries']}", flush=True)

    print("[STEP 9] Testing /reviews/pending (manager)...", flush=True)
    r = client.get("/api/v1/reviews/pending", headers={"Authorization": f"Bearer {mgr_token}"})
    assert r.status_code == 200, f"Pending reviews failed: {r.text}"
    print("✓ Pending reviews passed: count =", len(r.json()), flush=True)

    print("[STEP 10] Testing /policies (employee)...", flush=True)
    p = client.get("/api/v1/policies", headers={"Authorization": f"Bearer {emp_token}"})
    assert p.status_code == 200, f"Policies failed: {p.text}"
    print("✓ Policies list passed: count =", len(p.json()), flush=True)

    print("\n=======================================================", flush=True)
    print("🎉 ALL FASTAPI ENDPOINTS & RBAC RULES VERIFIED 100%!", flush=True)
    print("=======================================================", flush=True)

if __name__ == "__main__":
    test_all()
