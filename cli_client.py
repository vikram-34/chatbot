"""
CLI / SDK Consumer (Client Layer box)
----------------------------------------
A minimal terminal chat client against the running API Gateway.
Usage:
    python cli_client.py
"""
import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000"


def signup_or_login(client: httpx.Client, username: str, password: str) -> str:
    client.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
    # signup fails silently if user already exists; either way, try to log in
    resp = client.post(f"{BASE_URL}/auth/token", json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def main():
    print("=== Gemini Chatbot CLI ===")
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    session_id = str(uuid.uuid4())

    with httpx.Client(timeout=30) as client:
        token = signup_or_login(client, username, password)
        headers = {"Authorization": f"Bearer {token}"}
        print(f"\nLogged in. Session ID: {session_id}")
        print("Type 'exit' to quit, 'reset' to clear history.\n")

        while True:
            message = input("You: ").strip()
            if not message:
                continue
            if message.lower() == "exit":
                break
            if message.lower() == "reset":
                client.delete(f"{BASE_URL}/chat/{session_id}", headers=headers)
                print("(history cleared)\n")
                continue

            # resp = client.post(
            #     f"{BASE_URL}/chat",
            #     json={"session_id": session_id, "message": message},
            #     headers=headers,
            # )
            try:
                resp = client.post(
                f"{BASE_URL}/chat",
                json={"session_id": session_id, "message": message},
                headers=headers,
                timeout=60.0,
            )
            except httpx.ReadTimeout:
                print("Error: Gemini took too long to respond. Try again.")
                continue
            if resp.status_code != 200:
                print(f"Error: {resp.status_code} - {resp.text}")
                continue
            print(f"Bot: {resp.json()['reply']}\n")


if __name__ == "__main__":
    main()
