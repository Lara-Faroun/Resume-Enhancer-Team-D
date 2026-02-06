import json
import httpx

URL = "http://localhost:8000/api/v1/enhance?mode=incremental"

with open("sample_request.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

print("POST", URL)

with httpx.Client(timeout=None, trust_env=False) as client:
    with client.stream(
        "POST",
        URL,
        json=payload,
        headers={"Accept": "text/event-stream"},
    ) as r:
        print("Status:", r.status_code)
        print("Content-Type:", r.headers.get("content-type"))
        print("---- RAW BYTES (stream) ----")

        got_any = False
        for chunk in r.iter_raw():
            if not chunk:
                continue
            got_any = True
            print(chunk.decode("utf-8", errors="replace"), end="")

        print("\n---- END ----")
        print("got_any:", got_any)
