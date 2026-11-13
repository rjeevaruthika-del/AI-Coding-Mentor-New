
from courses import courses

chapter = courses["Python"]["chapters"][1]

print("CHAPTER TITLE:")
print(chapter.get("title", ""))

print("\nDEFINITION:")
print(chapter.get("definition", "No separate definition"))

print("\nCONTENT:")
print(chapter.get("content", ""))

print("\nSYNTAX:")
print(chapter.get("syntax", ""))

print("\nEXAMPLE:")
print(chapter.get("example", ""))

print("\nPRACTICE:")
for item in chapter.get("practice", []):
    print("-", item)

print("\nQUIZ QUESTIONS:")
for q in chapter.get("quiz", []):
    print("-", q.get("question", ""))
