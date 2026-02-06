import fs from "fs";

const url = "http://localhost:8000/run-workflow?mode=incremental";
const body = fs.readFileSync("body.json", "utf8");

const res = await fetch(url, {
  method: "POST",
  headers: {
    "Accept": "text/event-stream",
    "Content-Type": "application/json",
  },
  body,
});

if (!res.ok) {
  console.error("HTTP", res.status, await res.text());
  process.exit(1);
}

const reader = res.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  process.stdout.write(decoder.decode(value));
}
