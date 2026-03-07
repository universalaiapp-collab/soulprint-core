import requests

BASE_URL = "https://soulprint-core-production.up.railway.app"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("Health endpoint working")

if __name__ == "__main__":
    test_health()

