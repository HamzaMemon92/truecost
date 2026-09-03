from __future__ import annotations

import os

from locust import HttpUser, between, task


class TrueCostReadUser(HttpUser):
    wait_time = between(0.2, 1.5)

    def on_start(self) -> None:
        email = os.getenv("TRUECOST_LOAD_EMAIL")
        password = os.getenv("TRUECOST_LOAD_PASSWORD")
        self.headers: dict[str, str] = {}
        if email and password:
            response = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
            if response.ok:
                self.headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    @task(4)
    def provider_catalog(self) -> None:
        self.client.get("/api/v1/providers", name="providers")

    @task(3)
    def dashboard(self) -> None:
        if self.headers:
            self.client.get("/api/v1/commerce/dashboard", headers=self.headers, name="dashboard")

    @task(1)
    def optimization(self) -> None:
        if self.headers:
            self.client.post("/api/v1/aggregator/optimize", headers=self.headers, json={"basket": []}, name="optimization")
