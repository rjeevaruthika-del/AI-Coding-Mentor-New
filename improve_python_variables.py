
import json
from pathlib import Path
from courses import courses

# Copy the existing Variables chapter into a separate preview file.
chapter = next(
    ch for ch in courses["Python"]["chapters"]
    if ch.get("title") == "Variables"
)

improved = dict(chapter)

improved["definition"] = (
    "A variable is a named reference used to access a value "
    "in a program. In Python, assignment creates or reassigns "
    "a variable name, and the value's type is determined at runtime."
)

improved["content"] = """
CHAPTER 2: VARIABLES IN PYTHON

1. Introduction
Variables are essential building blocks in programming.
They let a program keep track of information and use it
later. For example, a student application may store a
student's name, age, department and marks in variables.

2. Creating a Variable
In Python, use the assignment operator (=) to assign a value
to a name. You do not need to declare the type separately.

Example:
student_name = "Jeeva"
age = 19
percentage = 85.5
is_present = True

Python determines the types from the assigned values:
student_name is a string, age is an integer, percentage is
a floating-point number, and is_present is a Boolean.

3. Naming Rules
- A name can contain letters, digits and underscores.
- A name cannot begin with a digit.
- Spaces are not allowed in variable names.
- Names are case-sensitive: age and Age are different.
- Python keywords, such as if and for, cannot be used as names.

4. Reassigning Values
A variable can refer to a new value later in the program.

Example:
score = 50
score = 75
print(score)

Output:
75

The second assignment replaces the value accessed through
the name score.

5. Multiple Assignment
Python supports assigning values to multiple names in one
statement when the number of names and values matches.

Example:
x, y = 10, 20
print(x)
print(y)

Output:
10
20

6. Good Naming Practices
Choose meaningful names such as total_marks or student_name.
Avoid unclear names when a descriptive name makes the program
easier to understand. By convention, Python variables usually
use lowercase words separated by underscores.

7. Common Mistakes
- Writing a variable name that starts with a digit.
- Using a variable before assigning it a value.
- Confusing uppercase and lowercase letters.
- Putting spaces in a variable name.
- Using = for assignment and mistakenly confusing it with ==,
  which checks equality.

8. Summary
Variables let programs work with named values. Python uses
assignment to bind names to values, determines types at runtime,
and distinguishes variable names by letter case.
"""

improved["syntax"] = """variable_name = value

student_name = "Jeeva"
age = 19
"""

improved["example"] = """student_name = "Jeeva"
age = 19
score = 50
score = 75

print(student_name)
print(age)
print(score)"""

improved["output"] = """Jeeva
19
75"""

improved["practice"] = [
    "Create variables for your name, age and city, then print them.",
    "Store three subject marks and calculate their total.",
    "Assign a value to score, change it, and print the new value.",
    "Create two variables and swap their values.",
    "Identify which of these names are valid: student_name, 2marks, total marks, class1."
]

improved["quiz"] = [
    {
        "id": 1,
        "question": "Which operator assigns a value to a variable?",
        "options": ["=", "==", "!=", ">="],
        "answer": 0
    },
    {
        "id": 2,
        "question": "Which is a valid Python variable name?",
        "options": ["2marks", "total marks", "total_marks", "for"],
        "answer": 2
    },
    {
        "id": 3,
        "question": "What is the output of score = 10; score = 20; print(score)?",
        "options": ["10", "20", "30", "Error"],
        "answer": 1
    },
    {
        "id": 4,
        "question": "What type of value is 85.5?",
        "options": ["str", "int", "float", "bool"],
        "answer": 2
    },
    {
        "id": 5,
        "question": "Are age and Age the same variable name in Python?",
        "options": ["Yes, always", "No, names are case-sensitive", "Only in functions", "Only in loops"],
        "answer": 1
    },
    {
        "id": 6,
        "question": "Which value is a Boolean?",
        "options": ['"True"', "19", "True", "19.0"],
        "answer": 2
    },
    {
        "id": 7,
        "question": "What does student_name = 'Jeeva' do?",
        "options": ["Assigns a string to a name", "Declares a loop", "Defines a function", "Imports a module"],
        "answer": 0
    },
    {
        "id": 8,
        "question": "Which statement prints the value stored in age?",
        "options": ["print(age)", "print('age')", "show age", "display = age"],
        "answer": 0
    },
    {
        "id": 9,
        "question": "Which is a recommended variable naming style in Python?",
        "options": ["student name", "student-name", "student_name", "2student"],
        "answer": 2
    },
    {
        "id": 10,
        "question": "What does x, y = 10, 20 do?",
        "options": ["Assigns 10 to x and 20 to y", "Adds x and y", "Creates a function", "Causes an error"],
        "answer": 0
    }
]

Path("python_variables_preview.json").write_text(
    json.dumps(improved, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Preview saved: python_variables_preview.json")
print("Title:", improved["title"])
print("Content words:", len(improved["content"].split()))
print("Quiz questions:", len(improved["quiz"]))
print("Original courses.py was not modified.")
