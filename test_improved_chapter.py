
import json
from pathlib import Path

path = Path("python_variables_preview.json")
chapter = json.loads(path.read_text(encoding="utf-8"))

print("Title:", chapter["title"])
print("Definition:", chapter["definition"])
print("Content words:", len(chapter["content"].split()))
print("Syntax available:", bool(chapter["syntax"]))
print("Example available:", bool(chapter["example"]))
print("Output available:", bool(chapter.get("output")))
print("Practice exercises:", len(chapter["practice"]))
print("Quiz questions:", len(chapter["quiz"]))

assert len(chapter["quiz"]) == 10
assert len(chapter["content"].split()) >= 150
assert all(q.get("question") for q in chapter["quiz"])

print("\nAll checks passed!")
