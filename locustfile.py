from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # Simulates user waiting time between requests

    @task(1)
    def register_user(self):
        """Simulates a new user registration."""
        self.client.post("/api/register", json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "securepassword123",
            "referral_code": ""
        })

    @task(2)
    def login_user(self):
        """Simulates user login."""
        response = self.client.post("/api/login", json={
            "email": "testuser@example.com",
            "password": "securepassword123"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(1)
    def check_referral_stats(self):
        """Simulates checking referral statistics."""
        self.client.get("/api/referral-stats")

