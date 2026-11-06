import time, json, urllib.request
url = "https://ai-qa-lab-production.up.railway.app/health"
for i in range(40):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            body = json.loads(r.read().decode())
        print(i, body, flush=True)
        if body.get("ui_automation") is not None:
            print("DEPLOYED", flush=True)
            break
    except Exception as exc:
        print(i, "err", exc, flush=True)
    time.sleep(30)
