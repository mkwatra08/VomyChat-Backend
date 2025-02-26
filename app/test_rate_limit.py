import requests

url = "http://127.0.0.1:8000/api/register"
headers = {"Content-Type": "application/json"}
data = {
    "username": "test",
    "email": "test@example.com",
    "password": "password123"
}

for i in range(6):  # Send 6 requests quickly
    response = requests.post(url, json=data, headers=headers)
    print(f"Request {i+1}: {response.status_code}, {response.json()}")
