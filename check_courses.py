
from courses import courses

print("\n===== COURSE CONTENT QUALITY CHECK =====\n")

for language, course in courses.items():
    chapters = course.get("chapters", [])
    short_content = 0
    duplicate_content = 0
    seen_content = set()
    repeated_questions = 0

    for chapter in chapters:
        content = chapter.get("content", "").strip()
        words = content.split()

        if len(words) < 150:
            short_content += 1

        normalized = " ".join(content.lower().split())
        if normalized:
            if normalized in seen_content:
                duplicate_content += 1
            seen_content.add(normalized)

        questions = [
            q.get("question", "").strip().lower()
            for q in chapter.get("quiz", [])
        ]
        repeated_questions += len(questions) - len(set(questions))

    print(f"Language: {language}")
    print(f"  Total chapters: {len(chapters)}")
    print(f"  Chapters under 150 words: {short_content}")
    print(f"  Duplicate chapter content: {duplicate_content}")
    print(f"  Repeated quiz questions: {repeated_questions}")
    print()

print("===== CHECK COMPLETE =====")
