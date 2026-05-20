"""
Benchmark suite for FinanceTrackerService.

Two user classes — run them separately or together:

  # Auth service only
  locust -f locustfile.py AuthServiceUser --host http://localhost:8081

  # Transactions service (requires auth service running too)
  locust -f locustfile.py TransactionsUser --host http://localhost:8080

  # Both together (headless, see run_benchmark.sh)
  locust -f locustfile.py --host http://localhost:8080
"""

import random
import string
from datetime import datetime, timezone

import requests as _requests
from locust import HttpUser, between, task

AUTH_SERVICE_URL = "http://localhost:8081"


def _random_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"bench_{suffix}@example.com"


class AuthServiceUser(HttpUser):
    """Simulates a user hitting auth-service endpoints directly."""

    host = AUTH_SERVICE_URL
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.email = _random_email()
        self.password = "BenchmarkPass1!"
        self.token = ""
        self.refresh_token = ""

        self.client.post("/users", json={"email": self.email, "password": self.password})
        resp = self.client.post(
            "/auth/login",
            data={"username": self.email, "password": self.password},
        )
        if resp.status_code == 200:
            body = resp.json()
            self.token = body.get("access_token", "")
            self.refresh_token = body.get("refresh_token", "")

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def get_me(self):
        self.client.get("/me", headers=self._auth_headers())

    @task(2)
    def login(self):
        resp = self.client.post(
            "/auth/login",
            data={"username": self.email, "password": self.password},
        )
        if resp.status_code == 200:
            body = resp.json()
            self.token = body.get("access_token", self.token)
            self.refresh_token = body.get("refresh_token", self.refresh_token)

    @task(1)
    def refresh(self):
        if not self.refresh_token:
            return
        resp = self.client.post(
            "/auth/refresh", json={"refresh_token": self.refresh_token}
        )
        if resp.status_code == 200:
            body = resp.json()
            self.token = body.get("access_token", self.token)
            self.refresh_token = body.get("refresh_token", self.refresh_token)


class TransactionsUser(HttpUser):
    """
    Simulates authenticated traffic against the Transactions service.

    This is the primary target for measuring:
      - Phase 1 improvement: JWT fix eliminates per-request HTTP call to auth-service
      - Phase 3 improvement: Redis cache reduces repeated DB lookups
    """

    host = "http://localhost:8080"
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.email = _random_email()
        self.password = "BenchmarkPass1!"
        self.token = ""

        # Register + login via auth-service (sync, runs once per simulated user)
        try:
            _requests.post(
                f"{AUTH_SERVICE_URL}/users",
                json={"email": self.email, "password": self.password},
                timeout=30,
            )
            resp = _requests.post(
                f"{AUTH_SERVICE_URL}/auth/login",
                data={"username": self.email, "password": self.password},
                timeout=30,
            )
            if resp.status_code == 200:
                self.token = resp.json().get("access_token", "")
        except _requests.exceptions.Timeout:
            pass

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}


    @task(5)
    def list_transactions(self):
        """
        Most representative endpoint: authenticated GET that currently triggers
        an HTTP call to auth-service on every request (pre-Phase-1-fix).
        This is where the biggest latency improvement will show up.
        """
        self.client.get("/transactions/user", headers=self._auth_headers(), name="/transactions/user")

    @task(2)
    def create_transaction(self):
        self.client.post(
            "/transactions",
            headers=self._auth_headers(),
            json={
                "amount": round(random.uniform(1.0, 9999.99), 2),
                "txn_type": random.choice(["income", "outcome"]),
                "desc": "benchmark load test",
                "transaction_date": datetime.now(timezone.utc).isoformat(),
            },
            name="/transactions [POST]",
        )

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")
