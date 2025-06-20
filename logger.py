import base64
import json
import requests

def push_to_github():
    try:
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPO")
        username = os.getenv("GITHUB_USERNAME")
        file_path = "data/log.csv"
        api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

        # Read CSV and base64 encode
        with open(file_path, "rb") as file:
            content = base64.b64encode(file.read()).decode("utf-8")

        # Check if file exists to get SHA
        res = requests.get(api_url, headers={"Authorization": f"Bearer {token}"})
        sha = res.json().get("sha") if res.status_code == 200 else None

        payload = {
            "message": "🔁 Automated log update",
            "content": content,
            "branch": "main",
            "committer": {
                "name": username,
                "email": f"{username}@users.noreply.github.com"
            }
        }

        if sha:
            payload["sha"] = sha

        push_res = requests.put(api_url, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }, data=json.dumps(payload))

        if push_res.status_code in [200, 201]:
            print("✅ GitHub push successful.")
        else:
            print(f"❌ GitHub push failed: {push_res.status_code}, {push_res.text}")

    except Exception as e:
        print(f"❌ Push error: {e}")
