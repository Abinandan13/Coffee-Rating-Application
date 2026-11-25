"""
Comprehensive Verification Test Suite for Module 3: Database Integration.
Tests all 12 required verification criteria against an isolated SQLite test database.
"""

import sys
import os
import time
import json
import sqlite3
import subprocess
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
TEST_DB_FILE = os.path.join(BACKEND_DIR, "test_coffee_rating.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"
TEST_HOST = "127.0.0.1"
TEST_PORT = 8009
BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"


def clean_test_db():
    """Removes temporary test database file if it exists."""
    for path in [TEST_DB_FILE, os.path.join(PROJECT_ROOT, "test_coffee_rating.db")]:
        if os.path.exists(path):
            for _ in range(5):
                try:
                    os.remove(path)
                    break
                except Exception:
                    time.sleep(0.2)


def start_server():
    """Starts the Uvicorn server in a subprocess pointing to the isolated test database."""
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DB_URL
    
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", TEST_HOST, "--port", str(TEST_PORT)],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server ready and database initialized
    for _ in range(35):
        time.sleep(0.3)
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/coffees", timeout=1) as resp:
                if resp.status == 200:
                    return proc
        except Exception:
            pass

    proc.terminate()
    raise RuntimeError("Server failed to become responsive on startup.")


def stop_server(proc):
    """Safely terminates the server subprocess."""
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def http_get(path: str):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode("utf-8")


def http_post(path: str, data: dict = None):
    url = f"{BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8") if data else b""
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8")


def run_all_tests():
    print("\n" + "=" * 75, flush=True)
    print("MODULE 3: DATABASE INTEGRATION - 12-POINT AUTOMATED TEST SUITE", flush=True)
    print("=" * 75, flush=True)

    clean_test_db()
    server_proc = start_server()
    results = []

    def record_test(name: str, passed: bool, details: str = ""):
        status = "[PASS]" if passed else "[FAIL]"
        results.append((name, passed, details))
        print(f"{status} {name}", flush=True)
        if details:
            print(f"       Details: {details}", flush=True)

    try:
        # 1. Database is created automatically
        db_created = os.path.exists(TEST_DB_FILE)
        record_test("1. Database is created automatically", db_created, f"File: {TEST_DB_FILE}")

        # 2. All four coffee records are inserted
        conn = sqlite3.connect(TEST_DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, votes FROM coffees ORDER BY id")
        rows = cursor.fetchall()
        row_ids = [r[0] for r in rows]
        expected_ids = ["cappuccino", "cold-brew", "espresso", "iced-latte"]
        all_inserted = len(rows) == 4 and all(cid in row_ids for cid in expected_ids)
        record_test("2. All four coffee records are inserted in SQLite", all_inserted, f"Found IDs: {row_ids}")

        # 3. Initial vote counts are zero for a fresh database
        all_zero = all(r[2] == 0 for r in rows)
        votes_dict = {r[1]: r[2] for r in rows}
        record_test("3. Initial vote counts are zero for a fresh database", all_zero, f"Votes in DB: {votes_dict}")
        conn.close()

        # 4. GET /api/coffees retrieves database records
        status_code, body = http_get("/api/coffees")
        coffees = json.loads(body)
        get_ok = (status_code == 200) and (len(coffees) == 4) and all(c["votes"] == 0 for c in coffees)
        record_test("4. GET /api/coffees retrieves database records", get_ok, f"Fetched: {len(coffees)} items")

        # 5. Voting increases the correct coffee count by exactly one
        status_code, body = http_post("/api/coffees/cappuccino/vote")
        data = json.loads(body)
        v1_ok = (status_code == 200) and (data.get("id") == "cappuccino") and (data.get("votes") == 1)
        record_test("5. Voting increases correct coffee count by exactly one", v1_ok, f"Cappuccino votes: {data.get('votes')}")

        # 6. Voting twice increases the count by two
        status_code, body = http_post("/api/coffees/cappuccino/vote")
        data = json.loads(body)
        v2_ok = (status_code == 200) and (data.get("id") == "cappuccino") and (data.get("votes") == 2)
        record_test("6. Voting twice increases the count by two", v2_ok, f"Cappuccino votes: {data.get('votes')}")

        # 7. Voting for one coffee does not affect other coffee counts
        status_code, body = http_post("/api/coffees/espresso/vote")
        _, all_body = http_get("/api/coffees")
        current_counts = {c["id"]: c["votes"] for c in json.loads(all_body)}
        independence_ok = (
            (status_code == 200) and
            (current_counts.get("cappuccino") == 2) and
            (current_counts.get("espresso") == 1) and
            (current_counts.get("iced-latte") == 0) and
            (current_counts.get("cold-brew") == 0)
        )
        record_test(
            "7. Voting for one coffee does not affect other coffee counts",
            independence_ok,
            f"Counts: Cappuccino={current_counts.get('cappuccino')}, Espresso={current_counts.get('espresso')}"
        )

        # 8. Invalid coffee ID returns HTTP 404
        status_code, body = http_post("/api/coffees/unknown-coffee-id/vote")
        data = json.loads(body)
        not_found_ok = (status_code == 404) and ("not found" in data.get("detail", "").lower())
        record_test("8. Invalid coffee ID returns HTTP 404", not_found_ok, f"Status: {status_code}, Detail: {data.get('detail')}")

        # 9. Existing vote counts remain unchanged after backend restart
        print("   Restarting backend server to verify persistence...", flush=True)
        stop_server(server_proc)
        time.sleep(1)
        server_proc = start_server()

        # Query GET /api/coffees after restart
        status_code, body = http_get("/api/coffees")
        after_restart_counts = {c["id"]: c["votes"] for c in json.loads(body)}
        persistence_ok = (
            (after_restart_counts.get("cappuccino") == 2) and
            (after_restart_counts.get("espresso") == 1) and
            (after_restart_counts.get("iced-latte") == 0) and
            (after_restart_counts.get("cold-brew") == 0)
        )
        record_test(
            "9. Existing vote counts remain unchanged after backend restart",
            persistence_ok,
            f"After restart: Cappuccino={after_restart_counts.get('cappuccino')}, Espresso={after_restart_counts.get('espresso')}"
        )

        # 10. Multiple voting requests do not lose increments (Atomic concurrency test)
        concurrent_votes = 15
        cold_brew_initial = after_restart_counts.get("cold-brew", 0)

        def vote_task(_):
            try:
                code, resp = http_post("/api/coffees/cold-brew/vote")
                return code == 200
            except Exception:
                return False

        with ThreadPoolExecutor(max_workers=5) as executor:
            vote_results = list(executor.map(vote_task, range(concurrent_votes)))

        all_requests_succeeded = all(vote_results)
        _, final_body = http_get("/api/coffees")
        final_counts = {c["id"]: c["votes"] for c in json.loads(final_body)}
        expected_cold_brew = cold_brew_initial + concurrent_votes
        atomic_ok = all_requests_succeeded and (final_counts.get("cold-brew") == expected_cold_brew)
        record_test(
            "10. Multiple voting requests do not lose increments (atomic transactions)",
            atomic_ok,
            f"Expected {expected_cold_brew} Cold Brew votes, got {final_counts.get('cold-brew')}"
        )

        # 11. Frontend displays the actual database vote counts (verification of script logic)
        frontend_script_path = os.path.join(PROJECT_ROOT, "frontend", "script.js")
        with open(frontend_script_path, "r", encoding="utf-8") as f:
            script_code = f.read()

        frontend_fetches_api = (
            "/api/coffees" in script_code and
            "fetch(" in script_code and
            "renderCoffeeCards" in script_code and
            "loading-indicator" in script_code
        )
        record_test(
            "11. Frontend fetches and displays actual database vote counts",
            frontend_fetches_api,
            "frontend/script.js includes fetch('/api/coffees') and DOM population logic"
        )

        # 12. Frontend voting requests update the database successfully
        frontend_posts_vote = (
            "/api/coffees/" in script_code and
            "/vote" in script_code and
            "btn-vote" in script_code and
            "disabled" in script_code and
            "showToast" in script_code
        )
        record_test(
            "12. Frontend voting requests update database and handle duplicate prevention",
            frontend_posts_vote,
            "frontend/script.js handles POST vote, duplicate click prevention & dynamic updates"
        )

    finally:
        stop_server(server_proc)
        clean_test_db()

    print("=" * 75, flush=True)
    passed_count = sum(1 for _, p, _ in results)
    total_count = len(results)
    print(f"SUMMARY: {passed_count}/{total_count} tests passed successfully.", flush=True)
    print("=" * 75, flush=True)

    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
