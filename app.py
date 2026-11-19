from flask import Flask, request, jsonify, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import re
import json
import subprocess
import sys
import tempfile
import shutil
import requests
import smtplib
import hashlib
from werkzeug.security import check_password_hash
from email.message import EmailMessage
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from openai import OpenAI

try:
    from courses import courses
except Exception:
    courses = {}

load_dotenv()

# Optional OpenAI support
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =========================================================
# APP SETUP
# =========================================================

app = Flask(__name__, static_folder="templates/static")
print("STATIC FOLDER:", app.static_folder)

js_path = os.path.join(app.static_folder, "js_actual.js")

print("JS FILE PATH:", js_path)
print("FILE EXISTS:", os.path.exists(js_path))

if os.path.exists(js_path):
    with open(js_path, "r", encoding="utf-8") as f:
        code = f.read()
    print("CHAPTER CARD CODE:", "chapter-card" in code)
app.secret_key = "ai_coding_mentor_secret_key_123"

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coding_mentor.db")

LANGUAGES = ['Python', 'C', 'C++', 'Java', 'JavaScript', 'R', 'C#', 'Go', 'PHP', 'Ruby', 'Kotlin', 'Swift', 'TypeScript', 'Rust', 'Dart']


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the current schema and repair older database schemas safely."""

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            email TEXT,
            password TEXT,
            language TEXT DEFAULT 'Python',
            progress INTEGER DEFAULT 0,
            quiz_score INTEGER DEFAULT 0
        )
    """)

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    }

    # Add missing columns safely
    if "username" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN username TEXT")
        columns.add("username")

    if "name" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN name TEXT")
        columns.add("name")

    if "email" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
        columns.add("email")

    if "password" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN password TEXT")
        columns.add("password")

    if "language" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'Python'"
        )
        columns.add("language")

    if "progress" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN progress INTEGER DEFAULT 0")
        columns.add("progress")

    if "quiz_score" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN quiz_score INTEGER DEFAULT 0")
        columns.add("quiz_score")

    # Copy an existing name into username when username is empty
    conn.execute("""
        UPDATE users
        SET username = name
        WHERE (username IS NULL OR TRIM(username) = '')
          AND name IS NOT NULL
          AND TRIM(name) != ''
    """)

    # Copy an existing username into name when name is empty
    conn.execute("""
        UPDATE users
        SET name = username
        WHERE (name IS NULL OR TRIM(name) = '')
          AND username IS NOT NULL
          AND TRIM(username) != ''
    """)

    # Keep existing records with no saved name from displaying email as name
    conn.execute("""
        UPDATE users
        SET name = 'Student'
        WHERE name IS NULL OR TRIM(name) = ''
    """)

    conn.execute("""
        UPDATE users
        SET username = name
        WHERE username IS NULL OR TRIM(username) = ''
    """)

    conn.execute("""
        UPDATE users
        SET language = 'Python'
        WHERE language IS NULL OR TRIM(language) = ''
    """)

    conn.execute("""
        UPDATE users SET progress = 0 WHERE progress IS NULL
    """)

    conn.execute("""
        UPDATE users SET quiz_score = 0 WHERE quiz_score IS NULL
    """)

    # Daily test history
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_test_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            test_date TEXT NOT NULL,
            language TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            UNIQUE(username, test_date, language)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# COURSE CONTENT - 70 TOPICS PER LANGUAGE
# =========================================================

COURSE_TOPICS = {'Python': ['Introduction to Python',
            'Features of Python',
            'Installation and Setup',
            'Python Interpreter',
            'Python Syntax',
            'Keywords',
            'Identifiers',
            'Variables',
            'Constants',
            'Comments',
            'Indentation',
            'Data Types',
            'Type Conversion',
            'Input and Output',
            'Arithmetic Operators',
            'Relational Operators',
            'Logical Operators',
            'Assignment Operators',
            'Bitwise Operators',
            'Membership Operators',
            'Identity Operators',
            'Operator Precedence',
            'if Statement',
            'if-else Statement',
            'if-elif-else',
            'Nested Conditions',
            'for Loop',
            'while Loop',
            'Nested Loops',
            'break Statement',
            'continue Statement',
            'pass Statement',
            'Strings',
            'String Methods',
            'String Formatting',
            'Lists',
            'List Methods',
            'Tuples',
            'Sets',
            'Dictionaries',
            'Dictionary Methods',
            'List Comprehension',
            'Dictionary Comprehension',
            'Functions',
            'Function Arguments',
            'Return Statement',
            'Lambda Functions',
            'Recursion',
            'Scope',
            'Modules',
            'Packages',
            'File Handling',
            'Exception Handling',
            'Regular Expressions',
            'Iterators',
            'Generators',
            'Decorators',
            'OOP Introduction',
            'Classes and Objects',
            'Constructors',
            'Inheritance',
            'Polymorphism',
            'Encapsulation',
            'Abstraction',
            'NumPy',
            'Pandas',
            'Matplotlib',
            'Data Cleaning',
            'Data Visualization',
            'Python for AI and ML'],
 'C': ['Introduction to C',
       'Features of C',
       'C Program Structure',
       'Compilation Process',
       'Tokens',
       'Keywords',
       'Identifiers',
       'Variables',
       'Constants',
       'Data Types',
       'Format Specifiers',
       'Input and Output',
       'Escape Sequences',
       'Arithmetic Operators',
       'Relational Operators',
       'Logical Operators',
       'Assignment Operators',
       'Bitwise Operators',
       'Conditional Operator',
       'Operator Precedence',
       'if Statement',
       'if-else Statement',
       'Nested if',
       'else-if Ladder',
       'switch Statement',
       'while Loop',
       'do-while Loop',
       'for Loop',
       'Nested Loops',
       'break Statement',
       'continue Statement',
       'goto Statement',
       'Arrays',
       'One-Dimensional Arrays',
       'Two-Dimensional Arrays',
       'Strings',
       'String Functions',
       'Functions',
       'Function Prototype',
       'Function Arguments',
       'Return Values',
       'Recursion',
       'Storage Classes',
       'Pointers',
       'Pointer Arithmetic',
       'Pointers and Arrays',
       'Pointers and Functions',
       'Double Pointers',
       'Dynamic Memory Allocation',
       'malloc Function',
       'calloc Function',
       'realloc Function',
       'free Function',
       'Structures',
       'Nested Structures',
       'Array of Structures',
       'Structure Pointers',
       'Unions',
       'Enumerations',
       'typedef',
       'Preprocessor',
       'Macros',
       'Header Files',
       'File Handling',
       'Text Files',
       'Binary Files',
       'Command Line Arguments',
       'Error Handling',
       'Debugging',
       'C Mini Project'],
 'C++': ['Introduction to C++',
         'Features of C++',
         'C++ Program Structure',
         'Compilation',
         'Namespaces',
         'Variables',
         'Data Types',
         'Constants',
         'Input and Output',
         'Operators',
         'Operator Precedence',
         'if Statement',
         'if-else Statement',
         'switch Statement',
         'for Loop',
         'while Loop',
         'do-while Loop',
         'break and continue',
         'Arrays',
         'Multidimensional Arrays',
         'Strings',
         'Functions',
         'Function Arguments',
         'Return Values',
         'Default Arguments',
         'Function Overloading',
         'Inline Functions',
         'Recursion',
         'Pointers',
         'References',
         'Dynamic Memory',
         'Structures',
         'Classes',
         'Objects',
         'Constructors',
         'Destructors',
         'this Pointer',
         'Static Members',
         'Friend Functions',
         'Encapsulation',
         'Inheritance',
         'Types of Inheritance',
         'Constructor in Inheritance',
         'Function Overriding',
         'Polymorphism',
         'Virtual Functions',
         'Abstract Classes',
         'Interfaces Concept',
         'Templates',
         'Function Templates',
         'Class Templates',
         'Exception Handling',
         'STL Introduction',
         'Vector',
         'List',
         'Deque',
         'Stack',
         'Queue',
         'Priority Queue',
         'Set',
         'Map',
         'Unordered Map',
         'Iterators',
         'Algorithms',
         'Lambda Expressions',
         'File Handling',
         'Smart Pointers',
         'Move Semantics',
         'RAII',
         'C++ Mini Project'],
 'Java': ['Introduction to Java',
          'Features of Java',
          'JDK',
          'JRE',
          'JVM',
          'First Java Program',
          'Java Syntax',
          'Keywords',
          'Identifiers',
          'Variables',
          'Data Types',
          'Type Casting',
          'Constants',
          'Input and Output',
          'Operators',
          'Operator Precedence',
          'if Statement',
          'if-else Statement',
          'Nested if',
          'else-if Ladder',
          'switch Statement',
          'for Loop',
          'while Loop',
          'do-while Loop',
          'break Statement',
          'continue Statement',
          'Arrays',
          'Multidimensional Arrays',
          'Strings',
          'String Methods',
          'StringBuilder',
          'Methods',
          'Method Arguments',
          'Method Overloading',
          'Return Values',
          'Recursion',
          'Classes',
          'Objects',
          'Constructors',
          'this Keyword',
          'static Keyword',
          'final Keyword',
          'Encapsulation',
          'Access Modifiers',
          'Packages',
          'Inheritance',
          'super Keyword',
          'Method Overriding',
          'Polymorphism',
          'Abstract Classes',
          'Interfaces',
          'Inner Classes',
          'Object Class',
          'Exception Handling',
          'Custom Exceptions',
          'Collections Framework',
          'ArrayList',
          'LinkedList',
          'HashSet',
          'HashMap',
          'Queue',
          'Generics',
          'Wrapper Classes',
          'Autoboxing',
          'File Handling',
          'Streams',
          'Lambda Expressions',
          'Multithreading',
          'JDBC',
          'Java Mini Project'],
 'JavaScript': ['Introduction to JavaScript',
                'Features of JavaScript',
                'JavaScript in HTML',
                'JavaScript Syntax',
                'Variables',
                'let',
                'const',
                'var',
                'Data Types',
                'Type Conversion',
                'Operators',
                'Arithmetic Operators',
                'Comparison Operators',
                'Logical Operators',
                'Assignment Operators',
                'Conditional Operator',
                'if Statement',
                'if-else Statement',
                'switch Statement',
                'for Loop',
                'while Loop',
                'do-while Loop',
                'break and continue',
                'Functions',
                'Function Parameters',
                'Return Values',
                'Arrow Functions',
                'Anonymous Functions',
                'Scope',
                'Hoisting',
                'Strings',
                'String Methods',
                'Arrays',
                'Array Methods',
                'Objects',
                'Object Methods',
                'Destructuring',
                'Spread Operator',
                'Rest Operator',
                'Template Literals',
                'Date and Time',
                'Math Object',
                'JSON',
                'DOM Introduction',
                'DOM Selectors',
                'DOM Manipulation',
                'Events',
                'Event Listeners',
                'Forms',
                'Form Validation',
                'Local Storage',
                'Session Storage',
                'Error Handling',
                'try-catch',
                'Callbacks',
                'Promises',
                'async-await',
                'Fetch API',
                'ES6 Features',
                'Modules',
                'Classes',
                'Constructors',
                'Inheritance',
                'Encapsulation',
                'Regular Expressions',
                'APIs',
                'AJAX',
                'Node.js Introduction',
                'JavaScript Projects',
                'JavaScript Mini Project'],
 'R': ['Introduction to R',
       'Features of R',
       'Installing R',
       'RStudio',
       'R Syntax',
       'Variables',
       'Constants',
       'Data Types',
       'Numeric Data',
       'Character Data',
       'Logical Data',
       'Complex Data',
       'Operators',
       'Arithmetic Operators',
       'Relational Operators',
       'Logical Operators',
       'Assignment Operators',
       'Input and Output',
       'Conditional Statements',
       'if Statement',
       'if-else Statement',
       'Nested Conditions',
       'for Loop',
       'while Loop',
       'repeat Loop',
       'break and next',
       'Vectors',
       'Vector Operations',
       'Matrices',
       'Matrix Operations',
       'Arrays',
       'Lists',
       'Factors',
       'Data Frames',
       'Data Frame Operations',
       'Strings',
       'String Functions',
       'Functions',
       'Function Arguments',
       'Return Values',
       'Recursion',
       'Packages',
       'Installing Packages',
       'Importing Data',
       'CSV Files',
       'Excel Data',
       'Data Cleaning',
       'Missing Values',
       'Data Filtering',
       'Data Sorting',
       'Data Transformation',
       'Data Aggregation',
       'Statistics Introduction',
       'Mean',
       'Median',
       'Mode',
       'Variance',
       'Standard Deviation',
       'Correlation',
       'Regression',
       'Data Visualization',
       'Base R Graphics',
       'ggplot2',
       'Bar Charts',
       'Line Charts',
       'Scatter Plots',
       'Histograms',
       'Statistical Analysis',
       'Machine Learning with R',
       'R Mini Project'],
 'C#': ['Introduction to C#',
        'Features of C#',
        '.NET Platform',
        'CLR',
        'C# Program Structure',
        'Compilation',
        'Namespaces',
        'Variables',
        'Constants',
        'Data Types',
        'Type Conversion',
        'Input and Output',
        'Operators',
        'Arithmetic Operators',
        'Comparison Operators',
        'Logical Operators',
        'Assignment Operators',
        'Bitwise Operators',
        'if Statement',
        'if-else Statement',
        'switch Statement',
        'for Loop',
        'while Loop',
        'do-while Loop',
        'break and continue',
        'Arrays',
        'Multidimensional Arrays',
        'Strings',
        'String Methods',
        'Methods',
        'Method Parameters',
        'Return Values',
        'Method Overloading',
        'Optional Parameters',
        'Classes',
        'Objects',
        'Constructors',
        'this Keyword',
        'static Keyword',
        'Properties',
        'Encapsulation',
        'Inheritance',
        'Method Overriding',
        'Polymorphism',
        'Abstract Classes',
        'Interfaces',
        'Generics',
        'Collections',
        'List',
        'Dictionary',
        'HashSet',
        'LINQ',
        'Delegates',
        'Events',
        'Lambda Expressions',
        'Exception Handling',
        'File Handling',
        'Async and Await',
        'Tasks',
        'Threads',
        'Nullable Types',
        'Records',
        'Pattern Matching',
        'Extension Methods',
        'Dependency Injection Basics',
        'Unit Testing Basics',
        'Database Access',
        'API Basics',
        'Debugging',
        'C# Mini Project'],
 'Go': ['Introduction to Go',
        'Features of Go',
        'Installation',
        'Go Workspace',
        'Program Structure',
        'Packages',
        'Variables',
        'Constants',
        'Data Types',
        'Type Inference',
        'Input and Output',
        'Operators',
        'if Statement',
        'switch Statement',
        'for Loop',
        'Nested Loops',
        'break and continue',
        'Arrays',
        'Slices',
        'Slice Methods',
        'Strings',
        'String Functions',
        'Maps',
        'Map Operations',
        'Functions',
        'Function Parameters',
        'Multiple Return Values',
        'Variadic Functions',
        'Anonymous Functions',
        'Closures',
        'Pointers',
        'Structs',
        'Methods',
        'Interfaces',
        'Embedding',
        'Error Handling',
        'Custom Errors',
        'Defer',
        'Panic and Recover',
        'Goroutines',
        'Channels',
        'Buffered Channels',
        'Select',
        'Synchronization',
        'WaitGroups',
        'Mutex',
        'Packages and Modules',
        'File Handling',
        'JSON',
        'HTTP Client',
        'HTTP Server',
        'REST APIs',
        'Testing',
        'Benchmarking',
        'Generics',
        'Type Parameters',
        'Reflection',
        'Context Package',
        'Database Access',
        'Command Line Tools',
        'Environment Variables',
        'Logging',
        'Time Package',
        'Regular Expressions',
        'Sorting',
        'Algorithms',
        'Data Structures',
        'Concurrency Patterns',
        'Go Project Structure',
        'Go Mini Project'],
 'PHP': ['Introduction to PHP',
         'Features of PHP',
         'Installation',
         'PHP Syntax',
         'Variables',
         'Constants',
         'Data Types',
         'Type Casting',
         'Strings',
         'String Functions',
         'Arrays',
         'Indexed Arrays',
         'Associative Arrays',
         'Array Functions',
         'Operators',
         'Arithmetic Operators',
         'Comparison Operators',
         'Logical Operators',
         'Assignment Operators',
         'if Statement',
         'if-else Statement',
         'switch Statement',
         'for Loop',
         'while Loop',
         'foreach Loop',
         'break and continue',
         'Functions',
         'Function Arguments',
         'Return Values',
         'Variable Scope',
         'Include and Require',
         'Forms',
         'Form Handling',
         'GET and POST',
         'Sessions',
         'Cookies',
         'File Handling',
         'Exception Handling',
         'Regular Expressions',
         'Classes',
         'Objects',
         'Constructors',
         'Inheritance',
         'Polymorphism',
         'Encapsulation',
         'Interfaces',
         'Traits',
         'Namespaces',
         'Composer',
         'JSON',
         'Date and Time',
         'MySQL Basics',
         'PDO',
         'CRUD Operations',
         'Authentication Basics',
         'Password Hashing',
         'REST APIs',
         'HTTP Requests',
         'cURL',
         'Error Logging',
         'Security Basics',
         'OOP Project',
         'MVC Concept',
         'Laravel Introduction',
         'PHP Web Project',
         'Testing Basics',
         'Deployment Basics',
         'Performance Basics',
         'PHP Mini Project',
         'PHP Topic 70'],
 'Ruby': ['Introduction to Ruby',
          'Features of Ruby',
          'Installation',
          'Ruby Syntax',
          'Variables',
          'Constants',
          'Data Types',
          'Numbers',
          'Strings',
          'String Methods',
          'Arrays',
          'Array Methods',
          'Hashes',
          'Hash Methods',
          'Symbols',
          'Ranges',
          'Operators',
          'if Statement',
          'unless Statement',
          'case Statement',
          'while Loop',
          'until Loop',
          'for Loop',
          'each Iterator',
          'break and next',
          'Methods',
          'Method Arguments',
          'Return Values',
          'Blocks',
          'Procs',
          'Lambdas',
          'Scope',
          'Classes',
          'Objects',
          'Constructors',
          'Instance Variables',
          'Class Variables',
          'Inheritance',
          'Modules',
          'Mixins',
          'Encapsulation',
          'Polymorphism',
          'Exception Handling',
          'File Handling',
          'Regular Expressions',
          'Enumerables',
          'Iterators',
          'Gems',
          'Bundler',
          'JSON',
          'Dates and Time',
          'Testing',
          'RSpec Basics',
          'Debugging',
          'Metaprogramming',
          'Reflection',
          'Threads',
          'Concurrency Basics',
          'Networking Basics',
          'HTTP Requests',
          'Web Development Basics',
          'Rails Introduction',
          'Database Basics',
          'APIs',
          'Security Basics',
          'Ruby Project',
          'Ruby Mini Project',
          'Ruby Topic 68',
          'Ruby Topic 69',
          'Ruby Topic 70'],
 'Kotlin': ['Introduction to Kotlin',
            'Features of Kotlin',
            'Installation',
            'Kotlin Syntax',
            'Variables',
            'val and var',
            'Data Types',
            'Type Inference',
            'Type Conversion',
            'Input and Output',
            'Operators',
            'if Expression',
            'when Expression',
            'for Loop',
            'while Loop',
            'do-while Loop',
            'break and continue',
            'Ranges',
            'Arrays',
            'Lists',
            'Mutable Lists',
            'Sets',
            'Maps',
            'Strings',
            'String Templates',
            'Functions',
            'Function Parameters',
            'Default Arguments',
            'Named Arguments',
            'Return Values',
            'Lambdas',
            'Higher-Order Functions',
            'Extension Functions',
            'Scope Functions',
            'Null Safety',
            'Nullable Types',
            'Elvis Operator',
            'Classes',
            'Objects',
            'Constructors',
            'Data Classes',
            'Sealed Classes',
            'Enum Classes',
            'Inheritance',
            'Interfaces',
            'Abstract Classes',
            'Overriding',
            'Generics',
            'Collections',
            'Exception Handling',
            'File Handling',
            'Packages',
            'Modules',
            'Coroutines',
            'Coroutine Builders',
            'Suspending Functions',
            'Flows',
            'Channels',
            'Java Interoperability',
            'Android Basics',
            'Serialization',
            'JSON',
            'Testing',
            'Unit Testing',
            'Database Basics',
            'REST APIs',
            'Build Tools',
            'Debugging',
            'Kotlin Project',
            'Kotlin Mini Project'],
 'Swift': ['Introduction to Swift',
           'Features of Swift',
           'Installation',
           'Swift Syntax',
           'Variables',
           'Constants',
           'Data Types',
           'Type Inference',
           'Type Conversion',
           'Input and Output',
           'Operators',
           'if Statement',
           'switch Statement',
           'for-in Loop',
           'while Loop',
           'repeat-while Loop',
           'break and continue',
           'Arrays',
           'Array Methods',
           'Sets',
           'Dictionaries',
           'Strings',
           'String Methods',
           'Functions',
           'Function Parameters',
           'Return Values',
           'Default Parameters',
           'Closures',
           'Optionals',
           'Optional Binding',
           'Guard Statement',
           'Tuples',
           'Enumerations',
           'Structures',
           'Classes',
           'Properties',
           'Methods',
           'Initializers',
           'Inheritance',
           'Protocols',
           'Extensions',
           'Generics',
           'Error Handling',
           'File Handling',
           'Modules',
           'Access Control',
           'Memory Management',
           'ARC',
           'Higher-Order Functions',
           'Map Filter Reduce',
           'Pattern Matching',
           'Concurrency',
           'Async Await',
           'Actors',
           'Networking',
           'JSON',
           'URLSession',
           'SwiftUI Introduction',
           'Views',
           'State Management',
           'Navigation',
           'Forms',
           'Data Persistence',
           'Core Data Basics',
           'Testing',
           'Debugging',
           'Packages',
           'APIs',
           'iOS App Structure',
           'Swift Project'],
 'TypeScript': ['Introduction to TypeScript',
                'Features of TypeScript',
                'Installation',
                'Compiler',
                'TypeScript Syntax',
                'Variables',
                'Type Annotations',
                'Primitive Types',
                'Arrays',
                'Tuples',
                'Enums',
                'Any Type',
                'Unknown Type',
                'Never Type',
                'Union Types',
                'Intersection Types',
                'Type Aliases',
                'Interfaces',
                'Optional Properties',
                'Readonly Properties',
                'Functions',
                'Function Types',
                'Optional Parameters',
                'Default Parameters',
                'Generics',
                'Generic Functions',
                'Generic Interfaces',
                'Classes',
                'Constructors',
                'Access Modifiers',
                'Inheritance',
                'Abstract Classes',
                'Polymorphism',
                'Modules',
                'Namespaces',
                'Type Assertions',
                'Narrowing',
                'Type Guards',
                'Literal Types',
                'Utility Types',
                'Mapped Types',
                'Conditional Types',
                'Template Literal Types',
                'Decorators',
                'Object Types',
                'Arrays and Tuples',
                'Enums in Practice',
                'Error Handling',
                'Promises',
                'Async Await',
                'DOM Types',
                'Events',
                'Fetch API',
                'JSON Types',
                'Node.js with TypeScript',
                'Express Basics',
                'REST APIs',
                'Database Basics',
                'Testing',
                'tsconfig',
                'Build Tools',
                'ES Modules',
                'Package Management',
                'Debugging',
                'Linting',
                'React with TypeScript',
                'API Project',
                'TypeScript Project',
                'TypeScript Mini Project',
                'TypeScript Topic 70'],
 'Rust': ['Introduction to Rust',
          'Features of Rust',
          'Installation',
          'Cargo',
          'Rust Syntax',
          'Variables',
          'Mutability',
          'Data Types',
          'Type Conversion',
          'Input and Output',
          'Operators',
          'if Expression',
          'match Expression',
          'Loops',
          'while Loop',
          'for Loop',
          'loop Expression',
          'break and continue',
          'Arrays',
          'Slices',
          'Vectors',
          'Strings',
          'String Slices',
          'Tuples',
          'Structs',
          'Methods',
          'Enums',
          'Pattern Matching',
          'Option',
          'Result',
          'Functions',
          'Function Parameters',
          'Return Values',
          'Ownership',
          'Borrowing',
          'References',
          'Mutable References',
          'Lifetimes',
          'Generics',
          'Traits',
          'Trait Bounds',
          'Modules',
          'Packages and Crates',
          'Error Handling',
          'File Handling',
          'Iterators',
          'Closures',
          'Smart Pointers',
          'Box',
          'Rc and Arc',
          'Concurrency',
          'Threads',
          'Channels',
          'Async Basics',
          'Futures',
          'Networking',
          'JSON',
          'Testing',
          'Unit Testing',
          'Macros',
          'Unsafe Rust',
          'FFI Basics',
          'WebAssembly Basics',
          'Database Access',
          'REST APIs',
          'CLI Applications',
          'Performance',
          'Debugging',
          'Rust Project',
          'Rust Mini Project'],
 'Dart': ['Introduction to Dart',
          'Features of Dart',
          'Installation',
          'Dart SDK',
          'Dart Syntax',
          'Variables',
          'final and const',
          'Data Types',
          'Type Inference',
          'Type Conversion',
          'Input and Output',
          'Operators',
          'if Statement',
          'switch Statement',
          'for Loop',
          'while Loop',
          'do-while Loop',
          'break and continue',
          'Lists',
          'List Methods',
          'Sets',
          'Maps',
          'Strings',
          'String Methods',
          'Functions',
          'Function Parameters',
          'Optional Parameters',
          'Named Parameters',
          'Return Values',
          'Anonymous Functions',
          'Arrow Functions',
          'Closures',
          'Classes',
          'Objects',
          'Constructors',
          'Named Constructors',
          'Inheritance',
          'Abstract Classes',
          'Interfaces',
          'Mixins',
          'Extensions',
          'Generics',
          'Null Safety',
          'Nullable Types',
          'Exception Handling',
          'File Handling',
          'Async Programming',
          'Future',
          'async and await',
          'Streams',
          'Isolates',
          'Packages',
          'JSON',
          'HTTP Requests',
          'REST APIs',
          'Testing',
          'Debugging',
          'Flutter Introduction',
          'Widgets',
          'Stateless Widgets',
          'Stateful Widgets',
          'Layouts',
          'Navigation',
          'Forms',
          'State Management',
          'Local Storage',
          'Database Basics',
          'Animations',
          'Flutter APIs',
          'Dart Project']}

# =========================================================
# HTML
# =========================================================

PAGE = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>AI Coding Mentor</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}

body {
    min-height: 100vh !important;
    color: #172554 !important;
    background:
        radial-gradient(circle at 10% 10%, rgba(96,165,250,0.15), transparent 25%),
        radial-gradient(circle at 90% 20%, rgba(167,139,250,0.12), transparent 25%),
        linear-gradient(135deg, #f8fbff 0%, #eef5ff 50%, #f7f9ff 100%) !important;
}

/* =====================================================
   COMMON
===================================================== */

.page {

    min-height: 100vh;

    padding: 40px;

}

.hidden {

    display: none !important;

}

.container {

    max-width: 1200px;

    margin: auto;

}


/* =====================================================
   WELCOME
===================================================== */

#welcomePage {
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 45px;
    position: relative;
    overflow: hidden;
}

#welcomePage::before {
    content: '';
    position: absolute;
    width: 520px;
    height: 520px;
    border-radius: 50%;
    background: rgba(37,99,235,0.08);
    top: -220px;
    left: -180px;
}

#welcomePage::after {
    content: '';
    position: absolute;
    width: 420px;
    height: 420px;
    border-radius: 50%;
    background: rgba(59,130,246,0.07);
    bottom: -210px;
    right: -130px;
}

.welcome-grid {
    max-width: 1180px;
    width: 100%;
    display: grid;
    grid-template-columns: 0.95fr 1.05fr;
    gap: 70px;
    align-items: center;
    position: relative;
    z-index: 1;
}

.welcome-left {
    padding: 25px 10px;
}

.brand-line {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 28px;
}

.brand-robot {
    width: 48px;
    height: 48px;
    border-radius: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 27px;
    background: linear-gradient(135deg, #dbeafe, #eff6ff);
    border: 1px solid #c7dcf8;
    box-shadow: 0 10px 25px rgba(37,99,235,0.10);
}

.brand-name {
    font-size: 23px;
    font-weight: 800;
    color: #102a56;
}

.brand-name span {
    color: #1769e0;
}

.welcome-left h1 {
    font-size: 58px;
    line-height: 1.08;
    margin-bottom: 22px;
    color: #102a56;
    letter-spacing: -1.5px;
}

.gradient {
    color: #1769e0;
}

.welcome-left p {
    color: #58708f;
    font-size: 18px;
    line-height: 1.75;
    margin-bottom: 30px;
    max-width: 570px;
}

.btn {
    border: none;
    padding: 14px 25px;
    border-radius: 12px;
    color: white;
    background: linear-gradient(135deg, #1769e0, #3b82f6);
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
    box-shadow: 0 10px 25px rgba(23,105,224,0.20);
    transition: 0.2s ease;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 30px rgba(23,105,224,0.26);
}

.glass {
    box-sizing: border-box;
    width: 100%;
    background: rgba(255,255,255,0.92);
    border: 1px solid #d8e6f7;
    border-radius: 24px;
    padding: 34px;
    box-shadow: 0 22px 60px rgba(31,72,125,0.12);
    backdrop-filter: blur(12px);
}

.welcome-left .glass {
    color: #102a56;
}

.welcome-features-title {
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 22px;
    color: #102a56;
}

.feature {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    padding: 16px 0;
    color: #4e6787;
    border-bottom: 1px solid #edf2f8;
    line-height: 1.5;
}

.feature:last-child {
    border-bottom: none;
}

.feature b {
    color: #17345f;
}

.feature-icon {
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    border-radius: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    background: #eaf3ff;
    border: 1px solid #d7e7fb;
}

/* =====================================================
   AUTH
===================================================== */

#authPage {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 35px;
}

.auth-box {
    width: 100%;
    max-width: 455px;
    padding: 40px;
    background: rgba(255,255,255,0.97);
    border: 1px solid #d7e5f5;
    border-radius: 24px;
    box-shadow: 0 25px 65px rgba(31,72,125,0.14);
}

.auth-brand {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 22px;
}

.auth-brand .brand-robot {
    width: 42px;
    height: 42px;
    font-size: 23px;
}

.auth-box h2 {
    text-align: center;
    margin-bottom: 10px;
    color: #102a56;
    font-size: 30px;
}

.auth-box p {
    text-align: center;
    color: #6b7f99;
    margin-bottom: 28px;
}

.input {
    width: 100%;
    padding: 14px 15px;
    margin-bottom: 15px;
    border-radius: 11px;
    border: 1px solid #d3e0ef;
    background: #fbfdff;
    color: #17345f;
    outline: none;
}

.input:focus {
    border-color: #4b8ff5;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.10);
}

.switch {
    color: #70839b !important;
}

.switch span:last-child {
    color: #1769e0;
    font-weight: 700;
    cursor: pointer;
}

    .lesson-layout { grid-template-columns:1fr; }
    .lesson-side-quiz { position:relative; top:auto; max-height:none; }
}
@media (max-width: 700px) {

    .chapter-number {
        font-size: 18px !important;
        font-weight: 700 !important;
    }

    .chapter-card {
        flex-direction: column !important;
        align-items: stretch !important;
        gap: 16px !important;
    }

    .chapter-card h3 {
        font-size: 26px !important;
    }

    .chapter-card p {
        font-size: 17px !important;
        line-height: 1.6 !important;
    }

    .chapter-quiz-box {
        width: 100% !important;
        box-sizing: border-box !important;
    }

    .chapter-quiz-box h3 {
        font-size: 24px !important;
    }

    .chapter-quiz-box p {
        font-size: 17px !important;
    }

    .chapter-card .btn,
    .chapter-quiz-box .btn {
        font-size: 17px !important;
    }

}
/* =====================================================
   FINAL PROFESSIONAL DASHBOARD THEME
===================================================== */
#dashboard {
    min-height: 100vh;
    background: #f5f9ff;
    color: #102a56;
}PS C:\Users\ELCOT\OneDrive\Desktop\AI coding mentor> Select-String -Path .\app.py -Pattern "\.hero-actions|\.btn" -Context 2,4

  app.py:1325:}
  app.py:1326:
> app.py:1327:.btn {
  app.py:1328:    border: none;
  app.py:1329:    padding: 14px 25px;
  app.py:1330:    border-radius: 12px;
  app.py:1331:    color: white;
  app.py:1338:}
  app.py:1339:
> app.py:1340:.btn:hover {
  app.py:1341:    transform: translateY(-2px);
  app.py:1342:    box-shadow: 0 14px 30px rgba(23,105,224,0.26);
  app.py:1343:}
  app.py:1344:
  app.py:1496:}
  app.py:1497:
> app.py:1498:.chapter-card .btn,
> app.py:1499:.chapter-quiz-box .btn {
  app.py:1500:    font-size: 17px !important;
  app.py:1501:}
  app.py:1502:}
  app.py:1503:
  app.py:1699:}
  app.py:1700:
> app.py:1701:.hero-actions {
  app.py:1702:    display: flex;
  app.py:1703:    gap: 12px;
  app.py:1704:    flex-wrap: wrap;
  app.py:1705:}
  app.py:1706:
> app.py:1707:.hero-actions .btn {
  app.py:1708:    margin: 0;
  app.py:1709:}
  app.py:1710:
> app.py:1711:.btn-secondary {
  app.py:1712:    border: 1px solid #2477ed !important;
  app.py:1713:    color: #1769e0 !important;
  app.py:1714:    background: #fff !important;
  app.py:1715:    box-shadow: none !important;
  app.py:2049:}
  app.py:2050:
> app.py:2051:.lesson-side-quiz .btn {
  app.py:2052:    width: 100%;
  app.py:2053:    margin-top: 8px;
  app.py:2054:}
  app.py:2055:
  app.py:2267:/* Buttons - keep same style, slightly stronger */
  app.py:2268:button,
> app.py:2269:.btn,
  app.py:2270:.start-btn,
  app.py:2271:.primary-btn {
  app.py:2272:    filter: brightness(0.92);
  app.py:2273:}


PS C:\Users\ELCOT\OneDrive\Desktop\AI coding mentor> 

.dashboard-shell {
    min-height: 100vh;
    display: flex;
}

.dashboard-shell {
    display: flex !important;
    flex-direction: row !important;
}

.dashboard-sidebar {
    width: 245px;
    flex: 0 0 245px;
    min-height: 100vh;
    background: linear-gradient(180deg, #0b285c 0%, #09204a 100%);
    color: #fff;
    padding: 24px 16px;
    display: flex;
    flex-direction: column;
    position: relative;
}
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 8px 10px 26px;
    font-size: 19px;
    font-weight: 800;
    white-space: nowrap;
}

.sidebar-robot {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: #fff;
    font-size: 24px;
    box-shadow: 0 8px 20px rgba(0,0,0,.15);
}

.sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.sidebar-nav button {
    width: 100%;
    border: 0;
    background: transparent;
    color: #dce9ff;
    padding: 13px 14px;
    border-radius: 12px;
    text-align: left;
    font-size: 15px;
    cursor: pointer;
    transition: .2s ease;
}

.sidebar-nav button:hover,
.sidebar-nav button.active {
    background: linear-gradient(135deg, #2477ed, #3d8bf4);
    color: #fff;
    box-shadow: 0 8px 20px rgba(37,99,235,.25);
}

.sidebar-bottom {
    margin-top: auto;
    padding: 18px 12px 6px;
}

.sidebar-tip {
    border: 1px solid rgba(255,255,255,.13);
    border-radius: 14px;
    padding: 17px 14px;
    background: rgba(255,255,255,.05);
    color: #dce9ff;
    line-height: 1.55;
    font-size: 13px;
}

.dashboard-main {
    min-width: 0;
    flex: 1;
    min-height: 100vh;
    background: #f7faff;
    position: relative;
}

.dashboard-topbar {
    height: 72px;
    width: 100%;
    box-sizing: border-box;

    background: rgba(255, 255, 255, 0.96);
    border-bottom: 1px solid #e3ecf8;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 0 28px;

    position: sticky;
    top: 0;
    z-index: 100;
}

.topbar-title {
    font-size: 19px;
    font-weight: 800;
    color: #102a56;
}

.topbar-user {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #193862;
    font-weight: 700;
}

.user-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    color: #fff;
    background: #2879e8;
    font-weight: 800;
}

.dashboard-content {
    flex: 1;
    width: 100%;
    max-width: none;
    margin: 0;
    padding: 26px 30px 34px;
    box-sizing: border-box;
}

.dashboard-hero {
    min-height: 245px;
    border-radius: 18px;
    padding: 34px 38px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
    background: linear-gradient(110deg, #dcecff 0%, #eaf4ff 52%, #d5e9ff 100%);
    border: 1px solid #d2e5fa;
}

.dashboard-hero::after {
    content: '';
    position: absolute;
    width: 430px;
    height: 430px;
    border-radius: 50%;
    right: -120px;
    top: -220px;
    background: rgba(255,255,255,.45);
}

.hero-copy {
    position: relative;
    z-index: 2;
    max-width: 610px;
}

.hero-kicker {
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 13px;
    font-weight: 800;
    color: #2869b8;
    margin-bottom: 10px;
}

.hero-copy h1 {
    font-size: 38px;
    line-height: 1.15;
    margin-bottom: 12px;
    color: #102f63;
}

.hero-copy p {
    font-size: 16px;
    line-height: 1.65;
    color: #42648c;
    max-width: 560px;
    margin-bottom: 22px;
}

.hero-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.hero-actions .btn {
    margin: 0;
}

.btn-secondary {
    border: 1px solid #2477ed !important;
    color: #1769e0 !important;
    background: #fff !important;
    box-shadow: none !important;
}

.hero-visual {
    width: 340px;
    height: 210px;
    display: grid;
    place-items: center;
    position: relative;
    z-index: 2;
    font-size: 118px;
    filter: drop-shadow(0 15px 20px rgba(30,83,145,.16));
}

.section-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 25px 2px 13px;
}

.section-title-row h2 {
    font-size: 21px;
    color: #102a56;
}

.section-link {
    border: 0;
    background: transparent;
    color: #1769e0;
    font-weight: 700;
    cursor: pointer;
}

.quick-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}

.quick-card {
    min-height: 166px;
    border-radius: 16px;
    padding: 20px;
    border: 1px solid #dbe8f6;
    background: #fff;
    box-shadow: 0 7px 22px rgba(35,76,125,.06);
    transition: .2s ease;
    position: relative;
}

.quick-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 28px rgba(35,76,125,.10);
}

.quick-icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    font-size: 22px;
    background: #e8f2ff;
    margin-bottom: 12px;
}

.quick-card h3 {
    font-size: 17px;
    color: #102f63;
    margin-bottom: 7px;
}

.quick-card p {
    color: #6a82a0;
    font-size: 13px;
    line-height: 1.45;
}

.quick-arrow {
    position: absolute;
    bottom: 15px;
    right: 17px;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    color: #1769e0;
    background: #eaf3ff;
}

.progress-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}

.stat-card {
    background: #fff;
    border: 1px solid #dbe8f6;
    border-radius: 15px;
    padding: 18px 20px;
    box-shadow: 0 7px 22px rgba(35,76,125,.05);
}

.stat-label {
    color: #7890ad;
    font-size: 13px;
    margin-bottom: 7px;
}

.stat-number {
    font-size: 27px;
    font-weight: 800;
    color: #102f63;
}

.stat-line {
    height: 7px;
    border-radius: 20px;
    background: #e8f1fb;
    margin-top: 13px;
    overflow: hidden;
}

.stat-line span {
    display: block;
    width: 0%;
    height: 100%;
    border-radius: inherit;
    background: #4b96f5;
}

.growth-banner {
    margin-top: 18px;
    border: 1px solid #d2e5fa;
    border-radius: 15px;
    padding: 19px 23px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(105deg, #e5f1ff, #f1f7ff);
    color: #173a6b;
}

.growth-banner strong {
    font-size: 17px;
}

.growth-banner small {
    color: #6681a4;
}

@media (max-width: 1000px) {
    .dashboard-sidebar { width: 210px; flex-basis: 210px; }
    .quick-grid, .progress-grid { grid-template-columns: repeat(2, 1fr); }
    .hero-visual { width: 240px; font-size: 90px; }
}

@media (max-width: 720px) {
    .dashboard-shell { display: block; }
    .dashboard-sidebar { width: 100%; min-height: auto; position: relative; }
    .sidebar-nav { display: grid; grid-template-columns: repeat(2, 1fr); }
    .sidebar-bottom { display: none; }
    .dashboard-topbar { padding: 0 18px; }
    .dashboard-content { padding: 18px; }
    .dashboard-hero { padding: 25px; }
    .hero-visual { display: none; }
    .quick-grid, .progress-grid { grid-template-columns: 1fr; }
}


.language-page{min-height:100vh;padding:42px 5%;background:#f4f7fb}
.language-header{text-align:center;margin-bottom:34px}
.language-header h1{margin:0 0 10px;color:#111827;font-size:38px;font-weight:800}
.language-header p{margin:0;color:#64748b;font-size:16px}
.language-grid{max-width:1180px;margin:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.language-card{background:#fff;border:1px solid #e2e8f0;border-radius:18px;padding:26px;min-height:185px;box-shadow:0 8px 24px rgba(15,23,42,.07);transition:.22s;display:flex;flex-direction:column;justify-content:space-between}
.language-card:hover{transform:translateY(-5px);border-color:#60a5fa;box-shadow:0 14px 32px rgba(15,23,42,.12)}
.language-card-top{display:flex;align-items:center;gap:15px}
.language-icon-box{width:52px;height:52px;border-radius:14px;background:#eff6ff;display:flex;align-items:center;justify-content:center;font-size:27px}
.language-card h2{margin:0;color:#111827;font-size:22px;font-weight:800}
.chapter-count{margin-top:5px;color:#64748b;font-size:14px}
.language-card .start-btn{width:100%;margin-top:22px;padding:12px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-size:14px;font-weight:700;cursor:pointer}
.language-card .start-btn:hover{background:#1d4ed8}
@media(max-width:950px){.language-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:620px){.language-page{padding:30px 18px}.language-header h1{font-size:29px}.language-grid{grid-template-columns:1fr}}


/* =========================================================
   PROFESSIONAL LESSON + SIDE QUIZ
   ========================================================= */

#lessonPage {
    min-height: 100vh;
    background: #f4f7fb;
    color: #111827;
}

#lessonPage .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 34px 4%;
}

.lesson-layout {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) !important;
    gap: 28px !important;
    width: 100% !important;
    max-width: none !important;
    align-items: start;
}

.lesson-book {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 20px !important;
    padding: 34px !important;
    box-shadow: 0 10px 30px rgba(15, 23, 42, .08) !important;
    min-width: 0;
}

.lesson-book h1 {
    color: #102a56 !important;
    font-size: 34px !important;
    margin: 0 0 18px !important;
    font-weight: 800 !important;
}

.lesson-book h2 {
    color: #172554 !important;
    font-size: 23px !important;
    margin-top: 28px !important;
    margin-bottom: 12px !important;
}

.lesson-book p,
.lesson-book li {
    color: #374151 !important;
    font-size: 16px !important;
    line-height: 1.85 !important;
}

.lesson-definition-box {
    background: #eff6ff;
    border-left: 5px solid #2563eb;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 20px 0 28px;
}

.lesson-definition-box h2 {
    color: #1d4ed8 !important;
    margin: 0 0 8px !important;
    font-size: 20px !important;
}

.lesson-definition-box p {
    color: #1f2937 !important;
    margin: 0 !important;
}

.lesson-code {
    background: #111827 !important;
    color: #f8fafc !important;
    border-radius: 12px;
    padding: 18px;
    overflow-x: auto;
    line-height: 1.6;
    font-size: 14px;
}

.lesson-side-quiz {
    position: sticky !important;
    top: 22px;
    max-height: calc(100vh - 44px);
    overflow-y: auto;
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #dbe3ee !important;
    border-radius: 20px !important;
    padding: 24px !important;
    box-shadow: 0 12px 34px rgba(15, 23, 42, .10) !important;
}

.lesson-side-quiz h2 {
    color: #102a56 !important;
    margin: 0 0 7px !important;
    font-size: 24px !important;
}

.lesson-quiz-subtitle {
    color: #64748b !important;
    font-size: 14px;
    margin-bottom: 18px;
}

.side-q {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 14px;
}

.side-q b {
    display: block;
    color: #111827 !important;
    line-height: 1.55;
    margin-bottom: 10px;
}

.side-q label {
    display: block;
    color: #374151 !important;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 9px;
    padding: 9px 10px;
    margin: 7px 0;
    cursor: pointer;
    line-height: 1.4;
}

.side-q label:hover {
    border-color: #60a5fa;
    background: #eff6ff;
}

.side-q input {
    margin-right: 7px;
}

.lesson-side-quiz .btn {
    width: 100%;
    margin-top: 8px;
}

.lesson-result {
    margin-top: 14px;
}

@media (max-width: 1000px) {
    .lesson-layout {
        grid-template-columns: 1fr !important;
    }

    .lesson-side-quiz {
        position: relative !important;
        top: auto;
        max-height: none;
        order: 2;
    }
}

@media (max-width: 600px) {
    #lessonPage .container {
        padding: 22px 14px;
    }

    .lesson-book {
        padding: 22px !important;
    }

    .lesson-book h1 {
        font-size: 27px !important;
    }
}


/* =====================================================
   DAILY CODING TEST
===================================================== */
.daily-test-banner {
    margin-top: 18px;
    background: linear-gradient(110deg, #e9f3ff, #f4f8ff);
    border: 1px solid #cfe1f7;
    border-radius: 18px;
    padding: 22px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    box-shadow: 0 8px 24px rgba(35,76,125,.06);
}
.daily-test-banner h3 { color:#102f63; font-size:20px; margin-bottom:6px; }
.daily-test-banner p { color:#6681a4; line-height:1.5; font-size:14px; }
.daily-test-badge {
    display:inline-flex; align-items:center; gap:7px;
    background:#fff; border:1px solid #d6e5f6;
    color:#1769e0; padding:7px 11px; border-radius:999px;
    font-size:12px; font-weight:800; margin-bottom:10px;
}
.daily-test-page {
    min-height:100vh;
    background:#f4f7fb;
}
.daily-test-page .container { max-width:1100px; }
.daily-test-header {
    display:flex; justify-content:space-between; align-items:flex-start;
    gap:20px; margin-bottom:20px;
}
.daily-test-title h1 { color:#102a56; margin-bottom:8px; }
.daily-test-title p { color:#64748b; }
.daily-timer {
    min-width:120px; text-align:center; padding:13px 16px;
    background:#fff; border:1px solid #dbe8f6; border-radius:14px;
    box-shadow:0 7px 22px rgba(35,76,125,.06);
}
.daily-timer span { display:block; color:#7890ad; font-size:12px; margin-bottom:4px; }
.daily-timer strong { color:#1769e0; font-size:24px; }
.daily-question-card {
    background:#fff; border:1px solid #e2e8f0; border-radius:16px;
    padding:22px; margin-bottom:16px;
    box-shadow:0 7px 22px rgba(35,76,125,.05);
}
.daily-q-number {
    color:#1769e0; font-size:12px; font-weight:800;
    text-transform:uppercase; letter-spacing:.8px; margin-bottom:8px;
}
.daily-question-card h3 {
    color:#102f63; font-size:17px; line-height:1.55; margin-bottom:14px;
}
.daily-option {
    display:block; padding:12px 14px; margin:8px 0;
    border:1px solid #dbe5f1; border-radius:11px;
    color:#294e78; background:#fbfdff; cursor:pointer;
    transition:.18s;
}
.daily-option:hover { border-color:#75aaf1; background:#f2f7ff; }
.daily-option input { margin-right:10px; }
.daily-submit-row {
    position:sticky; bottom:0; padding:16px 0 4px;
    background:linear-gradient(180deg,rgba(244,247,251,0),#f4f7fb 35%);
}
.daily-result {
    margin-top:18px; padding:22px; border-radius:16px;
    background:#fff; border:1px solid #dbe8f6;
    box-shadow:0 7px 22px rgba(35,76,125,.05);
}
.daily-score {
    font-size:32px; font-weight:900; color:#102f63; margin:8px 0;
}
.daily-history {
    margin-top:20px; background:#fff; border:1px solid #e2e8f0;
    border-radius:16px; padding:20px;
}
.daily-history-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:12px 0; border-bottom:1px solid #edf2f8;
    color:#294e78;
}
.daily-history-row:last-child { border-bottom:0; }
.daily-history-row strong { color:#102f63; }
@media(max-width:700px){
    .daily-test-banner,.daily-test-header { flex-direction:column; align-items:stretch; }
    .daily-timer { width:100%; }
}


/* =====================================================
   CHATGPT STYLE AI CHATBOT
===================================================== */
#chatPage{padding:0!important;margin:0!important;height:100vh;overflow:hidden;}
.chatgpt-page{height:100vh;display:flex;flex-direction:column;background:#f7f9fc;}
.chatgpt-topbar{height:70px;display:flex;align-items:center;padding:0 28px;background:#fff;border-bottom:1px solid #e5e7eb;box-shadow:0 2px 8px rgba(0,0,0,.04);}
.chat-back-btn{width:42px;height:42px;border:none;border-radius:12px;background:#eef4ff;color:#1d4ed8;font-size:22px;cursor:pointer;margin-right:15px;}
.chat-back-btn:hover{background:#dbeafe;}
.chat-title{display:flex;align-items:center;gap:12px;}
.chat-logo{width:42px;height:42px;border-radius:12px;background:#2563eb;display:flex;align-items:center;justify-content:center;font-size:23px;}
.chat-title strong{display:block;font-size:17px;color:#172554;}
.chat-title span{display:block;font-size:12px;color:#16a34a;margin-top:3px;}
.chatgpt-messages{flex:1;overflow-y:auto;padding:35px 12%;scroll-behavior:smooth;}
.chat-row{display:flex;gap:14px;margin-bottom:28px;width:100%;}
.bot-row{justify-content:flex-start;}
.user-row{justify-content:flex-end;}
.chat-avatar{width:38px;height:38px;min-width:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;}
.bot-avatar{background:#2563eb;}
.user-avatar-chat{background:#e5e7eb;}
.chat-bubble{max-width:75%;padding:15px 18px;border-radius:18px;font-size:15px;line-height:1.65;white-space:pre-wrap;word-break:break-word;}
.bot-bubble{background:#fff;color:#1f2937;border:1px solid #e5e7eb;border-top-left-radius:5px;}
.user-bubble{background:#2563eb;color:#fff;border-top-right-radius:5px;}
.bot-name{font-size:12px;font-weight:700;color:#2563eb;margin-bottom:7px;}
.chatgpt-input-area{padding:15px 12% 20px;background:linear-gradient(to top,#f7f9fc 75%,rgba(247,249,252,0));}
.chatgpt-input-box{max-width:900px;margin:auto;background:#fff;border:1px solid #d1d5db;border-radius:18px;min-height:58px;display:flex;align-items:center;padding:8px 10px 8px 18px;box-shadow:0 5px 20px rgba(15,23,42,.08);}
.chatgpt-input-box textarea{flex:1;border:none;outline:none;resize:none;font-size:15px;line-height:1.5;color:#111827;background:transparent;max-height:130px;padding:8px 0;font-family:inherit;}
.chatgpt-input-box textarea::placeholder{color:#9ca3af;}
.chat-send-btn{width:42px;height:42px;border:none;border-radius:12px;background:#2563eb;color:#fff;font-size:19px;cursor:pointer;margin-left:10px;}
.chat-send-btn:hover{background:#1d4ed8;transform:scale(1.03);}
.chat-disclaimer{text-align:center;color:#9ca3af;font-size:11px;margin-top:8px;}
@media(max-width:700px){.chatgpt-topbar{padding:0 15px}.chatgpt-messages{padding:25px 15px}.chatgpt-input-area{padding:12px 15px 16px}.chat-bubble{max-width:85%;}}
/* ===== DARKER VERSION - DESIGN UNCHANGED ===== */

body {
    color: #172554 !important;
    background:
        radial-gradient(circle at 8% 12%, rgba(37, 99, 235, 0.16), transparent 28%),
        radial-gradient(circle at 92% 88%, rgba(30, 64, 175, 0.20), transparent 30%),
        linear-gradient(135deg, #e8f0fb 0%, #dce8f7 48%, #d7e4f5 100%) !important;
}

/* Main content */
.dashboard-content {
    background: transparent !important;
}

/* Existing cards - same design, slightly darker */
.card,
.course-card,
.chapter-card,
.lesson-card,
.progress-card,
.content-card,
.quiz-card,
.feature-card {
    background: #f8fbff !important;
    border-color: #cbd8e8 !important;
    box-shadow: 0 5px 18px rgba(30, 55, 90, 0.12) !important;
}

/* Headings */
h1 {
    color: #102a56 !important;
}

h2 {
    color: #153b70 !important;
}

h3 {
    color: #1b477d !important;
}

/* Normal text */
p,
label,
span {
    color: #334b6b;
}

/* Inputs */
input,
select,
textarea {
    background: #f7faff !important;
    border-color: #b9c9dd !important;
    color: #172554 !important;
}

/* Buttons - keep same style, slightly stronger */
button,
.btn,
.start-btn,
.primary-btn {
    filter: brightness(0.92);
}

/* Progress background */
.progress-bar {
    background: #cbd8e8 !important;
}

/* Divider */
hr {
    border-color: #c3d1e2 !important;
}
.card,
.course-card,
.chapter-card,
.lesson-card,
.progress-card,
.content-card,
.quiz-card,
.feature-card,
.lesson-main,
.lesson-content {
    background: #e8eef7 !important;
}
/* Fix course chapter display */
#coursePage:not(.hidden) #courseTopics {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 20px;
    width: 100%;
    margin-top: 25px;
}

#coursePage #courseTopics .chapter-card {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    min-width: 0;
    padding: 22px;
    border-radius: 16px;
    background: #202b3d;
    border: 1px solid #3b4960;
    color: #ffffff;
}

#coursePage #courseTopics .chapter-card h3,
#coursePage #courseTopics .chapter-card p {
    display: block;
    color: #ffffff;
}

@media (max-width: 900px) {
    #coursePage:not(.hidden) #courseTopics {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 600px) {
    #coursePage:not(.hidden) #courseTopics {
        grid-template-columns: 1fr;
    }
}
</style>

</head>


<body>


<!-- =====================================================
     WELCOME
===================================================== -->

<section id="welcomePage">

    <div class="welcome-grid">

        <div class="welcome-left">

            <div class="brand-line">
                <div class="brand-robot">🤖</div>
                <div class="brand-name">AI Coding <span>Mentor</span></div>
            </div>

            <h1>

                Learn Coding

                <br>

                With Your

                <span class="gradient">
                    AI Mentor
                </span>

            </h1>

            <p>

                Learn programming languages,
                practice coding, take quizzes,
                analyze your code and chat with
                your AI coding mentor.

            </p>


<button
    type="button"
    class="btn"
    onclick="showPage('authPage')"
>
    Start Learning
</button>

        </div>


        <div class="glass">

            <div class="welcome-features-title">Your Personal Coding Mentor</div>

            <div class="feature">

                <div class="feature-icon">
                    🤖
                </div>

                <div>
                    <b>AI Code Analysis</b>
                    <br>
                    Find coding errors and get explanations.
                </div>

            </div>


            <div class="feature">

                <div class="feature-icon">
                    📚
                </div>

                <div>
                    <b>Multiple Languages</b>
                    <br>
                    Python, C, C++, Java and more.
                </div>

            </div>


            <div class="feature">

                <div class="feature-icon">
                    🧠
                </div>

                <div>
                    <b>Practice Quiz</b>
                    <br>
                    Test your programming knowledge.
                </div>

            </div>


            <div class="feature">

                <div class="feature-icon">
                    📊
                </div>

                <div>
                    <b>Progress Tracking</b>
                    <br>
                    Track your learning progress.
                </div>

            </div>

        </div>

    </div>

</section>


<!-- =====================================================
     AUTH
===================================================== -->


<!-- AUTH PAGE -->
<section id="authPage" class="hidden">

    <div class="glass auth-box">

        <!-- BRAND -->
        <div class="auth-brand">
            <div class="brand-robot">🤖</div>
            <div class="brand-name">
                AI Coding <span>Mentor</span>
            </div>
        </div>

        <!-- TITLE -->
        <h2 id="authTitle">Welcome Back 👋</h2>

        <p id="authDescription">
            Login to continue learning.
        </p>

        <!-- NAME - SIGN UP ONLY -->
       <!-- NAME INPUT -->



<!-- NAME - SIGN UP ONLY -->
<div id="authNameWrapper" style="display:none; width:100%;">
    <input
        id="authName"
        name="name"
        type="text"
        class="input"
        placeholder="Enter your full name"
        autocomplete="name"
        style="width:100%;"
    >
</div>

        <!-- EMAIL -->
        <input
            id="authEmail"
            type="email"
            class="input"
            placeholder="Enter your email ID"
            autocomplete="email"
        >

        <!-- PASSWORD -->
        <div style="position:relative;width:100%;">

            <input
                id="authPassword"
                type="password"
                class="input"
                placeholder="Enter your password"
                autocomplete="current-password"
                style="padding-right:50px;"
            >

            <button
                type="button"
                onclick="
                    const p = document.getElementById('authPassword');
                    p.type = p.type === 'password' ? 'text' : 'password';
                    this.innerText = p.type === 'password' ? '👁️' : '🙈';
                "
                style="
                    position:absolute;
                    right:12px;
                    top:50%;
                    transform:translateY(-50%);
                    border:none;
                    background:transparent;
                    color:#94a3b8;
                    cursor:pointer;
                    font-size:18px;
                    padding:4px;
                "
            >👁️</button>

        </div>

        <!-- CONFIRM PASSWORD - SIGN UP ONLY -->
        <div
            id="confirmPasswordWrapper"
            class="hidden"
            style="position:relative;width:100%;"
        >

            <input
                id="authConfirmPassword"
                type="password"
                class="input"
                placeholder="Confirm your password"
                autocomplete="new-password"
                style="padding-right:50px;"
            >

            <button
                type="button"
                onclick="
                    const p = document.getElementById('authConfirmPassword');
                    p.type = p.type === 'password' ? 'text' : 'password';
                    this.innerText = p.type === 'password' ? '👁️' : '🙈';
                "
                style="
                    position:absolute;
                    right:12px;
                    top:50%;
                    transform:translateY(-50%);
                    border:none;
                    background:transparent;
                    color:#94a3b8;
                    cursor:pointer;
                    font-size:18px;
                    padding:4px;
                "
            >👁️</button>

        </div>

      

<!-- LOGIN / CREATE ACCOUNT BUTTON -->
<button
    type="button"
    class="btn"
    id="authButton"
    style="width:100%;"
    onclick="loginUser()"
>
    Login
</button>


        <!-- SWITCH LOGIN / SIGN UP -->
        <div class="switch" style="margin-top:18px;">

            <span id="switchText">
                Don't have an account?
            </span>

            &nbsp;

            <span
                id="authSwitch"
                onclick="toggleAuth()"
                style="
                    cursor:pointer;
                    font-weight:600;
                    color:#2563eb;
                "
            >Sign Up</span>

        </div>

    </div>

</section>


<!-- =====================================================
     DASHBOARD
===================================================== -->

<section id="dashboard" class="hidden">

    <div class="dashboard-shell">

        <aside class="dashboard-sidebar">

            <div class="sidebar-brand">
                <div class="sidebar-robot">🤖</div>
                <span>AI Coding Mentor</span>
            </div>

            <nav class="sidebar-nav">

                <button class="active" onclick="showPage('dashboard')">
                    🏠 &nbsp; Home
                </button>

                <button onclick="showLanguages()">
                    📚 &nbsp; Courses
                </button>

                <button onclick="openEditor()">
                    ✦ &nbsp; AI Analysis
                </button>

                <button onclick="openProgress()">
                    ❔ &nbsp; Quiz
                </button>

                <button onclick="openDailyTest()">
                    📝 &nbsp; Daily Test
                </button>

                <button onclick="openChat()">
                    🤖 &nbsp; AI Chatbot
                </button>

                <button onclick="openProgress()">
                    📊 &nbsp; Progress
                </button>

                <button onclick="showPage('profilePage')">
                    👤 &nbsp; Profile
                </button>

                <button onclick="logout()">
                    ↪ &nbsp; Logout
                </button>

            </nav>

            <div class="sidebar-bottom">
                <div class="sidebar-tip">
                    💡<br>
                    <strong>
                        Small steps every day lead to big progress.
                    </strong>
                </div>
            </div>

        </aside>

        <main class="dashboard-main">

            <header class="dashboard-topbar">

                <div class="topbar-title">
                    AI Coding Mentor
                </div>

                <div class="topbar-user">

                    <span>🔔</span>

                    <div class="user-avatar" id="dashboardAvatar">
                        {{ session.get('user_name', 'S')[:1].upper() }}
                    </div>

                    <div
                        class="user-menu"
                        onclick="showPage('profilePage')"
                        style="cursor:pointer;"
                    >
                        <span id="dashboardUserName">
                            {{ session.get('user_name', 'Student') }}
                        </span>
                        <span>⌄</span>
                    </div>

                </div>

            </header>

            <div class="dashboard-content">

                <section class="dashboard-hero">

                    <div class="hero-copy">

                        <div class="hero-kicker">
                            Welcome back,
                        </div>

                        <h1>
                            <span id="userDisplay" class="gradient">
                                {{ session.get('user_name', 'Student') }}
                            </span>! 👋
                        </h1>

                        <p>
                            Your personal AI coding mentor is here to help you
                            learn, practice and grow your coding skills.
                        </p>

                        <div class="hero-actions">

                            <button
                                type="button"
                                class="btn"
                                onclick="showPage('authPage')"
                            >
                                Start Learning →
                            </button>

                            <button
                                type="button"
                                class="btn btn-secondary"
                                onclick="showLanguages()"
                            >
                                Explore Courses
                            </button>

                        </div>

                    </div>

                    <div class="hero-visual">
                        🤖
                    </div>

                </section>

                <div class="section-title-row">

                    <h2>Quick Access</h2>

                    <button
                        class="section-link"
                        onclick="showLanguages()"
                    >
                        View All →
                    </button>

                </div>

                <div class="quick-grid">

                    <div
                        class="quick-card"
                        onclick="showLanguages()"
                    >
                        <div class="quick-icon">📖</div>
                        <h3>Courses</h3>
                        <p>
                            Learn from structured lessons and book-style notes.
                        </p>
                        <div class="quick-arrow">→</div>
                    </div>

                    <div
                        class="quick-card"
                        onclick="openEditor()"
                    >
                        <div class="quick-icon">✦</div>
                        <h3>AI Analysis</h3>
                        <p>
                            Get AI-powered code review and suggestions.
                        </p>
                        <div class="quick-arrow">→</div>
                    </div>

                    <div
                        class="quick-card"
                        onclick="openProgress()"
                    >
                        <div class="quick-icon">❔</div>
                        <h3>Quiz</h3>
                        <p>
                            Test your knowledge and track your progress.
                        </p>
                        <div class="quick-arrow">→</div>
                    </div>

                    <div
                        class="quick-card"
                        onclick="openChat()"
                    >
                        <div class="quick-icon">🤖</div>
                        <h3>AI Chatbot</h3>
                        <p>
                            Ask coding questions and learn with your AI mentor.
                        </p>
                        <div class="quick-arrow">→</div>
                    </div>

                </div>

                <div class="daily-test-banner">

                    <div>

                        <div class="daily-test-badge">
                            📝 DAILY CHALLENGE
                        </div>

                        <h3>
                            Daily Coding Test
                        </h3>

                        <p>
                            10 fresh questions every day based on your selected
                            programming language. Complete today's test and
                            track your score.
                        </p>

                    </div>

                    <button
                        class="btn"
                        onclick="openDailyTest()"
                    >
                        Start Today's Test →
                    </button>

                </div>

                <div class="section-title-row">
                    <h2>Your Progress</h2>
                </div>

                <div class="progress-grid">

                    <div class="stat-card">
                        <div class="stat-label">
                            📖 Completed Courses
                        </div>
                        <div class="stat-number">0</div>
                        <div class="stat-line">
                            <span></span>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-label">
                            ▶️ Problems Solved
                        </div>
                        <div class="stat-number">0</div>
                        <div class="stat-line">
                            <span></span>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-label">
                            ❔ Quizzes Taken
                        </div>
                        <div class="stat-number">0</div>
                        <div class="stat-line">
                            <span></span>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-label">
                            📊 Overall Progress
                        </div>
                        <div class="stat-number">0%</div>
                        <div class="stat-line">
                            <span></span>
                        </div>
                    </div>

                </div>

                <div class="growth-banner">

                    <div>
                        <strong>
                            🎯 Keep Going, Keep Growing
                        </strong>
                        <br>
                        <small>
                            Every expert was once a beginner.
                        </small>
                    </div>

                    <span style="font-size:24px">
                        →
                    </span>

                </div>

            </div>

        </main>

    </div>

</section>


<!-- =====================================================
     LANGUAGE PAGE
===================================================== -->

<section id="languagePage" class="hidden page">

    <div class="container">

        <h1>📚 Choose a Programming Language</h1>

        <p style="color:#536b8f; margin-top:8px;">
            Each language has 70 structured learning topics.
        </p>

        <div class="language-grid">

            <div class="language-card" onclick="openCourse('Python')">
                <div class="language-icon">🐍</div>
                <h3>Python</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('C')">
                <div class="language-icon">💻</div>
                <h3>C</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('C++')">
                <div class="language-icon">⚙️</div>
                <h3>C++</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('Java')">
                <div class="language-icon">☕</div>
                <h3>Java</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('JavaScript')">
                <div class="language-icon">🌐</div>
                <h3>JavaScript</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('R')">
                <div class="language-icon">📊</div>
                <h3>R</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('C#')">
                <div class="language-icon">🔷</div>
                <h3>C#</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('Go')">
                <div class="language-icon">🐹</div>
                <h3>Go</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('PHP')">
                <div class="language-icon">🐘</div>
                <h3>PHP</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('Ruby')">
                <div class="language-icon">💎</div>
                <h3>Ruby</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('Kotlin')">
                <div class="language-icon">🟣</div>
                <h3>Kotlin</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('Swift')">
                <div class="language-icon">🍎</div>
                <h3>Swift</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('TypeScript')">
                <div class="language-icon">🔷</div>
                <h3>TypeScript</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('Rust')">
                <div class="language-icon">🦀</div>
                <h3>Rust</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

            <div class="language-card" onclick="openCourse('Dart')">
                <div class="language-icon">🎯</div>
                <h3>Dart</h3>
                <p style="color:#536b8f; margin-top:8px;">75+ Chapters</p>
            </div>

        </div>

        <br>

   <button
    type="button"
    class="logout"
    onclick="showPage('dashboard')"
    style="
        background:#1e293b;
        color:#e2e8f0;
        border:1px solid #334155;
    "
>
    ← Dashboard
</button>

    </div>

</section>


<!-- =====================================================
     COURSE PAGE
===================================================== -->



<section id="coursePage" class="hidden page">
    <div class="container">
        <button class="logout" onclick="showPage('dashboard')">
            ← Dashboard
        </button>

        <h1 style="margin-top:25px">
            📚 <span id="courseTitle">Python</span> Course
        </h1>

        <p style="color:#aaa;margin-top:10px">
            Learn every chapter with detailed definitions, explanations,
            syntax, examples, output, practice and chapter quizzes.
        </p>

        <div
            id="courseTopics"
            class="cards"
            style="grid-template-columns:repeat(3,minmax(0,1fr));margin-top:25px">
        </div>
    </div>
</section>

<section id="lessonPage" class="hidden page">
    <div class="container book-container">

        <button class="logout"
                onclick="openCourse(window.selectedLanguage || 'Python')">
            ← Back to Chapters
        </button>

        <div class="book-heading">
            <div>
                <p class="book-label">AI CODING MENTOR · TEXTBOOK</p>
                <h1 id="bookLessonTitle">Chapter Lesson</h1>
                <p id="bookLessonSubtitle">
                    Learn step by step with examples and practice.
                </p>
            </div>

            <div class="chapter-count" id="bookChapterNumber">
                CHAPTER
            </div>
        </div>

        <div class="book-layout">

            <!-- LEFT SIDE: BOOK CONTENT -->
            <article class="lesson-book glass">

                <div class="reading-progress">
                    <span id="lessonProgressText">Your learning journey</span>
                </div>

                <section class="book-section">
                    <h2>1. Definition</h2>
                    <div id="bookDefinition" class="book-paragraph"></div>
                </section>

                <section class="book-section">
                    <h2>2. Detailed Explanation</h2>
                    <div id="bookExplanation" class="book-paragraph"></div>
                </section>

                <section class="book-section">
                    <h2>3. Important Points</h2>
                    <ul id="bookKeyPoints" class="book-list"></ul>
                </section>

                <section class="book-section">
                    <h2>4. Syntax</h2>
                    <pre class="book-code"><code id="bookSyntax"></code></pre>
                </section>

                <section class="book-section">
                    <h2>5. Example Program</h2>
                    <pre class="book-code"><code id="bookExample"></code></pre>
                </section>

                <section class="book-section">
                    <h2>6. Expected Output</h2>
                    <pre class="book-output" id="bookOutput"></pre>
                </section>

                <section class="book-section">
                    <h2>7. Practice Exercises</h2>
                    <ol id="bookPractice" class="book-list"></ol>
                </section>

                <div class="book-navigation">
                    <button
                        id="previousChapterBtn"
                        class="book-nav-btn"
                        onclick="moveBookChapter(-1)">
                        ← Previous
                    </button>

                    <button
                        id="nextChapterBtn"
                        class="book-nav-btn"
                        onclick="moveBookChapter(1)">
                        Next Chapter →
                    </button>
                </div>

            </article>

            <!-- RIGHT SIDE: CHAPTER QUIZ -->
            <aside class="chapter-quiz-panel glass">
                <div class="quiz-panel-icon">📝</div>

                <p class="book-label">TEST YOUR KNOWLEDGE</p>
                <h2>Chapter Quiz</h2>

                <p class="quiz-panel-description">
                    Test your understanding of this chapter using
                    multiple-choice questions.
                </p>

                <div class="quiz-info-row">
                    <span>Questions</span>
                    <strong>10</strong>
                </div>

                <div class="quiz-info-row">
                    <span>Question type</span>
                    <strong>MCQ</strong>
                </div>

                <div class="quiz-info-row">
                    <span>Chapter</span>
                    <strong id="sideQuizChapter">Chapter 1</strong>
                </div>

                <button
                    class="book-start-quiz"
                    id="sideStartQuizBtn"
                    onclick="startSideChapterQuiz()">
                    Start Chapter Quiz →
                </button>

                <div class="quiz-study-tip">
                    <strong>💡 Study Tip</strong>
                    <p>
                        Read the definition, understand the example,
                        and then attempt the quiz.
                    </p>
                </div>
            </aside>

        </div>
    </div>
</section>


<!-- PROFILE PAGE -->
<section id="profilePage" class="hidden page">

    <div class="dashboard-shell">

        <!-- SIDEBAR -->
        <aside class="dashboard-sidebar">

            <div class="sidebar-brand">
                <div class="sidebar-robot">🤖</div>
                <span>AI Coding Mentor</span>
            </div>

            <nav class="sidebar-nav">

                <button onclick="showPage('dashboard')">
                    🏠 &nbsp; Home
                </button>

                <button onclick="showLanguages()">
                    📚 &nbsp; Courses
                </button>

                <button onclick="openEditor()">
                    ✦ &nbsp; AI Analysis
                </button>

                <button onclick="openQuiz()">
                    ❔ &nbsp; Quiz
                </button>

                <button onclick="openDailyTest()">
                    📝 &nbsp; Daily Test
                </button>

                <button onclick="openChat()">
                    🤖 &nbsp; AI Chatbot
                </button>

                <button onclick="openProgress()">
                    📊 &nbsp; Progress
                </button>

                <button class="active" onclick="showPage('profilePage')">
                    👤 &nbsp; Profile
                </button>

                <button onclick="logout()">
                    ↪ &nbsp; Logout
                </button>

            </nav>

            <div class="sidebar-bottom">
                <div class="sidebar-tip">
                    💡<br>
                    <strong>
                        Small steps every day lead to big progress.
                    </strong>
                </div>
            </div>

        </aside>

        <!-- MAIN CONTENT -->
        <main class="dashboard-main">

            <header class="dashboard-topbar">

                <div class="topbar-title">
                    AI Coding Mentor
                </div>

                <div class="topbar-user">

                    <span>🔔</span>

                    <div class="user-avatar">
                        {{ session.get('user_name', 'S')[:1].upper() }}
                    </div>

                    <span id="profileTopName">
                        {{ session.get('user_name', 'Student') }}
                    </span>

                    <span>⌄</span>

                </div>

            </header>

            <!-- PROFILE DETAILS -->
            <div class="dashboard-content">

                <div class="dashboard-hero">

                    <div class="hero-copy">

                        <h1>
                            Welcome,
                            <span class="gradient" id="profileUserName">
                                {{ session.get('user_name', 'Student') }}
                            </span>! 👋
                        </h1>

                        <p>
                            View your account information and learning profile.
                        </p>

                    </div>

                    <div class="hero-visual">
                        👤
                    </div>

                </div>

                <!-- PROFILE INFORMATION -->
                <div class="quick-grid">

                    <div class="quick-card">
                        <div class="quick-icon">👤</div>
                        <h3>Name</h3>
                        <p id="profileName">
                            {{ session.get('user_name', 'Student') }}
                        </p>
                    </div>

                    <div class="quick-card">
                        <div class="quick-icon">📧</div>
                        <h3>Email</h3>
                        <p id="profileEmail">
                            {{ session.get('user_email', 'Email not available') }}
                        </p>
                    </div>

                    <div class="quick-card">
                        <div class="quick-icon">💻</div>
                        <h3>Learning</h3>
                        <p>AI &amp; Machine Learning</p>
                    </div>

                    <div class="quick-card">
                        <div class="quick-icon">📚</div>
                        <h3>Programming</h3>
                        <p>Python, C, C++, Java and more</p>
                    </div>

                </div>

                <!-- GROWTH BANNER -->
                <div class="growth-banner">
                    <div>
                        <strong>🚀 Keep Learning, Keep Growing</strong>
                        <br>
                        <small>
                            Continue your coding journey with AI Coding Mentor.
                        </small>
                    </div>
                </div>

            </div>

        </main>

    </div>

</section>


<!-- =====================================================
     EDITOR
===================================================== -->

<section id="editorPage" class="hidden page">

    <div class="container">

        <h1>
            💻 AI Code Analysis
        </h1>

        <p style="color:#aaa;margin-top:10px">

            Language:
            <b id="selectedLanguage">
                Python
            </b>

        </p>

        <div style="margin:15px 0 20px 0;">
            <label for="editorLanguage" style="display:block;color:white;font-weight:600;margin-bottom:8px;">
                Select Programming Language
            </label>
            <select id="editorLanguage" onchange="changeEditorLanguage(this.value)"
                    style="width:100%;max-width:360px;padding:12px 14px;border-radius:10px;background:#111827;color:white;border:1px solid #6d28d9;font-size:16px;outline:none;">
                <option value="Python">Python</option>
                <option value="C">C</option>
                <option value="C++">C++</option>
                <option value="Java">Java</option>
                <option value="JavaScript">JavaScript</option>
                <option value="R">R</option>
                <option value="C#">C#</option>
                <option value="Go">Go</option>
                <option value="PHP">PHP</option>
                <option value="Ruby">Ruby</option>
                <option value="Kotlin">Kotlin</option>
                <option value="Swift">Swift</option>
                <option value="TypeScript">TypeScript</option>
                <option value="Rust">Rust</option>
                <option value="Dart">Dart</option>
            </select>
        </div>

        <div class="editor-layout">


            <div class="glass">

                <h3 style="margin-bottom:15px">
                    Write Your Code
                </h3>

                <textarea
    id="codeEditor"
    placeholder="Write your code here..."
    style="width:100%; min-height:450px; resize:vertical;"
></textarea>


                <div class="editor-buttons">

                    <button
                        class="btn"
                        onclick="runCode()"
                    >
                        ▶ Run Code
                    </button>

                    <button
                        class="btn"
                        onclick="analyzeCode()"
                    >
                        🤖 AI Code Analysis
                    </button>

                    <button
                        class="btn"
                        style="background:#374151"
                        onclick="clearEditor()"
                    >
                        Clear
                    </button>

                </div>

            </div>


            <div class="glass">

                <h3>
                    🤖 AI Mentor Feedback
                </h3>


               <div
    id="analysisResult"
    class="result"
    style="min-height:350px; max-height:600px; overflow-y:auto; width:100%;"
>

                    <div class="message hint">

                        Write your code and click
                        Analyze My Code.

                    </div>

                </div>

            </div>

        </div>


        <br>

        <button
            class="btn"
            onclick="backDashboard()"
        >

            ← Dashboard

        </button>

    </div>

</section>


<!-- =====================================================
     DAILY CODING TEST
===================================================== -->
<section id="dailyTestPage" class="hidden page daily-test-page">
    <div class="container">
        <div style="padding-top:28px;">
            <button class="btn" style="background:#475569" onclick="backDashboard()">← Dashboard</button>
        </div>

        <div id="dailyTestContent" style="margin-top:22px;">
            <div class="glass">Loading today's test...</div>
        </div>
    </div>
</section>

<!-- =====================================================
     QUIZ
===================================================== -->

<section id="quizPage" class="hidden page">

    <div class="container">

        <h1>
            🧠 Programming Quiz
        </h1>

        <p style="color:#aaa;margin-top:10px">

            Language:
            <b id="quizLanguage">
                Python
            </b>

        </p>


        <div
            id="quizContainer"
            class="glass quiz-question"
        >

        </div>


        <br>

        <button
            class="btn"
            onclick="backDashboard()"
        >
            ← Dashboard
        </button>

    </div>

</section>


<!-- =====================================================
     CHATBOT
===================================================== -->

<section id="chatPage" class="hidden page">

    <div class="chatgpt-page">

        <div class="chatgpt-topbar">
            <button class="chat-back-btn" onclick="backDashboard()">←</button>
            <div class="chat-title">
                <div class="chat-logo">🤖</div>
                <div>
                    <strong>AI Coding Mentor</strong>
                    <span>● Online</span>
                </div>
            </div>
        </div>

        <div id="chatMessages" class="chatgpt-messages">
            <div class="chat-row bot-row">
                <div class="chat-avatar bot-avatar">🤖</div>
                <div class="chat-bubble bot-bubble">
                    <div class="bot-name">AI Coding Mentor</div>
                    <div>👋 Hello! I'm your AI Coding Mentor.<br><br>Ask me anything about programming, coding errors, concepts or examples.</div>
                </div>
            </div>
        </div>

        <div class="chatgpt-input-area">
            <div class="chatgpt-input-box">
                <textarea id="chatInput" rows="1" placeholder="Message AI Coding Mentor..." onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault();sendMessage();}"></textarea>
                <button class="chat-send-btn" onclick="sendMessage()" title="Send">➤</button>
            </div>
            <div class="chat-disclaimer">AI Coding Mentor can make mistakes. Check important code before using it.</div>
        </div>

    </div>

</section>


<!-- =====================================================
     PROGRESS
===================================================== -->

<section id="progressPage" class="hidden page"> 
 
    <div class="container"> 
 
        <h1> 
            📊 My Learning Progress 
        </h1> 
 
        <div class="glass progress-box"> 
 
            <h3> 
                Overall Progress 
            </h3> 
 
            <br> 
 
            <div class="progress-bar"> 
 
                <div 
                    id="progressFill" 
                    class="progress-fill" 
                ></div> 
 
            </div> 
 
            <br> 
 
            <h2 id="progressText"> 
                0% 
            </h2> 
 
            <br> 
 
            <p> 
                Quiz Score: 
                <b id="quizScore"> 
                    0 
                </b> 
            </p> 
 
            <br> 
 
            <p> 
                Selected Language: 
                <b id="progressLanguage"> 
                    Python 
                </b> 
            </p> 
 
        </div> 
 
        <br> 
 
        <button 
            class="btn" 
            type="button"
            onclick="backDashboard()" 
        > 
            ← Dashboard 
        </button> 
 
    </div> 
 
</section> 


<script>


window.loginMode = true;
window.selectedLanguage = "Python";

window.hideAll = function() {

    const pages = [
        "welcomePage",
        "authPage",
        "dashboard",
        "languagePage",
        "editorPage",
        "quizPage",
        "dailyTestPage",
        "chatPage",
        "progressPage",
        "coursePage",
        "lessonPage",
        "profilePage"
    ];

    pages.forEach(function(id) {

        const page = document.getElementById(id);

        if (page) {
            page.classList.add("hidden");
        }

    });
};


window.showPage = function(id) {

    window.hideAll();

    const page = document.getElementById(id);

    if (page) {
        page.classList.remove("hidden");
    }

    // Profile page open pannumbothu name and email load aagum
    if (id === "profilePage") {

        fetch("/profile-data")
            .then(function(response) {
                if (!response.ok) {
                    throw new Error("Profile data load aagala");
                }
                return response.json();
            })
            .then(function(data) {

                if (data.success) {

                    const name = data.name || "Student";
                    const email = data.email || "Email not available";

                    const profileName =
                        document.getElementById("profileName");

                    const profileEmail =
                        document.getElementById("profileEmail");

                    const profileTopName =
                        document.getElementById("profileTopName");

                    const profileUserName =
                        document.getElementById("profileUserName");

                    // Name card
                    if (profileName) {
                        profileName.textContent = name;
                    }

                    // Email card
                    if (profileEmail) {
                        profileEmail.textContent = email;
                    }

                    // Topbar user name
                    if (profileTopName) {
                        profileTopName.textContent = name;
                    }

                    // Welcome heading
                    if (profileUserName) {
                        profileUserName.textContent = name;
                    }

                } else {
                    console.log("Please login to view your profile.");
                }

            })
            .catch(function(error) {
                console.error("Profile loading error:", error);
            });
    }

};
</script>
<script>

// ========================================================
// AUTH
// ========================================================


function toggleAuth() {
    window.loginMode = (window.loginMode !== false) ? false : true;
    const isSignup = window.loginMode === false;

    const nameWrapper = document.getElementById("authNameWrapper");
    const nameInput = document.getElementById("authName");

    const confirmInput = document.getElementById("authConfirmPassword");
    const confirmWrapper = document.getElementById("confirmPasswordWrapper");

    const title = document.getElementById("authTitle");
    const description = document.getElementById("authDescription");
    const button = document.getElementById("authButton");
    const switchText = document.getElementById("switchText");
    const switchButton = document.getElementById("authSwitch");

    // NAME FIELD
    if (nameWrapper) {
        nameWrapper.style.display = isSignup ? "block" : "none";
    }

    if (nameInput) {
        nameInput.required = isSignup;
        if (!isSignup) {
            nameInput.value = "";
        }
    }

    // CONFIRM PASSWORD
    if (confirmWrapper) {
        confirmWrapper.style.display = isSignup ? "block" : "none";
    }

    if (confirmInput) {
        confirmInput.required = isSignup;
        if (!isSignup) {
            confirmInput.value = "";
        }
    }

    // PAGE TEXT
    if (isSignup) {
        title.innerText = "Create Account 🚀";
        description.innerText = "Create your student account.";
        button.innerText = "Create Account";
        switchText.innerText = "Already have an account?";
        switchButton.innerText = "Login";
    } else {
        title.innerText = "Welcome Back 👋";
        description.innerText = "Login to continue learning.";
        button.innerText = "Login";
        switchText.innerText = "Don't have an account?";
        switchButton.innerText = "Sign Up";
    }

    console.log("SIGNUP MODE:", isSignup);
    console.log("NAME WRAPPER FOUND:", !!nameWrapper);
}


 // ========================================================
 // LOGIN + SIGN UP
 // ========================================================

async function loginUser() {
    console.log("LOGIN FUNCTION CALLED");

    const emailInput = document.getElementById("authEmail");
    const passwordInput = document.getElementById("authPassword");
    const nameInput = document.getElementById("authName");
    const confirmInput = document.getElementById("authConfirmPassword");

    const email = emailInput ? emailInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value : "";
    const name = nameInput ? nameInput.value.trim() : "";
    const confirmPassword = confirmInput ? confirmInput.value : "";

    console.log("LOGIN MODE:", window.loginMode);
    console.log("NAME:", name || "EMPTY");
    console.log("EMAIL:", email || "EMPTY");
    console.log("PASSWORD EMPTY:", password.length === 0);
    console.log("CONFIRM EMPTY:", confirmPassword.length === 0);

    try {


        // SIGN UP
        if (window.loginMode === false) {

            console.log("SIGNUP MODE:", window.loginMode);
            console.log("NAME:", name);
            console.log("EMAIL:", email);
            console.log("PASSWORD FILLED:", password.length > 0);
            console.log("CONFIRM FILLED:", confirmPassword.length > 0);

            if (!nameInput || !emailInput ||
                !passwordInput || !confirmInput) {
                alert("Signup input field ID missing. Check your HTML.");
                return;
            }

            if (!name || !email || !password || !confirmPassword) {
                if (!name) {
                    alert("Please enter your name.");
                } else if (!email) {
                    alert("Please enter your email.");
                } else if (!password) {
                    alert("Please enter your password.");
                } else {
                    alert("Please confirm your password.");
                }
                return;
            }

            if (password !== confirmPassword) {
                alert("Passwords do not match.");
                return;
            }

            // SEND SIGNUP REQUEST
            const response = await fetch("/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password,
                    confirm_password: confirmPassword
                })
            });

            const data = await response.json();

            console.log("SIGNUP RESPONSE:", data);

            if (!response.ok || !data.success) {
                alert(data.message || "Signup failed.");
                return;
            }

            alert("Account created successfully! Please login.");

            // SWITCH TO LOGIN MODE
            window.loginMode = true;

            if (emailInput) emailInput.value = email;
            if (passwordInput) passwordInput.value = "";

            if (nameInput) {
                nameInput.value = "";
                nameInput.classList.add("hidden");
            }

            if (confirmInput) {
                confirmInput.value = "";
                confirmInput.classList.add("hidden");
            }

            const title = document.getElementById("authTitle");
            if (title) title.textContent = "Welcome Back 👋";

            const description = document.getElementById("authDescription");
            if (description) {
                description.textContent = "Login to continue learning.";
            }

            const button = document.getElementById("authButton");
            if (button) button.textContent = "Login";

            const switchText = document.getElementById("switchText");
            if (switchText) {
                switchText.textContent = "Don't have an account?";
            }

            const authSwitch = document.getElementById("authSwitch");
            if (authSwitch) authSwitch.textContent = "Sign Up";

            return;
        }

        // LOGIN VALIDATION
        if (!email || !password) {
            alert("Please enter your email and password.");
            return;
        }

        // LOGIN REQUEST
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        console.log("LOGIN STATUS:", response.status);
        console.log("LOGIN RESPONSE:", data);

        if (!response.ok || !data.success) {
            alert(data.message || "Invalid email or password.");
            return;
        }

        // SAVE USER DETAILS
        const loginName = String(data.name || "Student").trim();
        const loginEmail = String(data.email || email).trim();

        sessionStorage.setItem("userName", loginName);
        sessionStorage.setItem("userEmail", loginEmail);

        // UPDATE DASHBOARD AND PROFILE
        const fields = {
            userDisplay: loginName,
            dashboardName: loginName,
            profileName: loginName,
            profileEmail: loginEmail,
            profileTopName: loginName,
            profileUserName: loginName
        };

        for (const id in fields) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = fields[id];
            }
        }

        // OPEN DASHBOARD
        if (typeof showPage === "function") {
            showPage("dashboard");
        } else {
            alert("showPage() function not found. Check your script.");
        }

    } catch (error) {
        console.error("LOGIN/SIGNUP ERROR:", error);
        alert("Error occurred. Check the browser Console (F12).");
    }
}

// ========================================================
// LANGUAGE
// ========================================================

function showLanguages() {
    const languagePage = document.getElementById("languagePage");

        document.getElementById("dashboard").classList.add("hidden");
    languagePage.classList.remove("hidden");
}



console.log("AI Coding Mentor JavaScript loaded");

window.openCourse = async function(language) {
    alert("Clicked language: " + language);
    console.log("Opening course:", language);

    const coursePage = document.getElementById("coursePage");
    const languagePage = document.getElementById("languagePage");

    if (!coursePage || !languagePage) {
        alert("Course page or language page not found!");
        return;
    }

    languagePage.classList.add("hidden");
    coursePage.classList.remove("hidden");

    document.getElementById("courseTitle").innerText = language;

    const box = document.getElementById("courseTopics");
    box.innerHTML = "<p>Loading chapters...</p>";

    try {
        const response = await fetch(
            "/course-data?language=" + encodeURIComponent(language)
        );
        const data = await response.json();

        window.currentTopics = data.topics || [];

        if (!response.ok) {
            throw new Error(data.message || "Failed to load chapters");
        }

        if (window.currentTopics.length === 0) {
            box.innerHTML = "<p>No chapters found.</p>";
            return;
        }

        box.innerHTML = window.currentTopics.map((topic, index) => `
            <div class="chapter-card">
                <h3>📘 Chapter ${index + 1}: ${topic.title}</h3>
                <p>Learn ${topic.title} step by step.</p>
                <button class="btn" onclick="openLesson(${Number(topic.id)})">
                    📖 Open Chapter
                </button>
            </div>
        `).join("");

    } catch (error) {
        console.error(error);
        box.innerHTML = `<p>Unable to load chapters: ${error.message}</p>`;
    }
};

// ========================================================
// CHAPTER SIDE QUIZ
// ========================================================
async function openChapterQuiz(id) {
    showPage("quizPage");

    const container = document.getElementById("quizContainer");
    const title = document.querySelector("#quizPage h1");
    const languageLabel = document.getElementById("quizLanguage");

    if (title) title.innerText = "📝 Chapter Quiz";
    if (languageLabel) languageLabel.innerText = selectedLanguage;

    container.innerHTML = '<div class="message hint">Loading chapter quiz...</div>';

    try {
        const response = await fetch("/course-data?language=" + encodeURIComponent(selectedLanguage));
        const data = await response.json();

        if (!data.success) {
            container.innerHTML = '<div class="message error">Unable to load chapter quiz.</div>';
            return;
        }

        const chapter = data.topics.find(t => t.id === id);
        if (!chapter) {
            container.innerHTML = '<div class="message error">Chapter not found.</div>';
            return;
        }

        const quiz = (chapter.quiz || []).slice(0, 10).map((q) => {
            const options = q.options.map((label, index) => ({
                label: label,
                correct: index === q.answer
            }));

            for (let i = options.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [options[i], options[j]] = [options[j], options[i]];
            }

            return { question: q.question, options: options };
        });

        window.currentChapterQuiz = quiz;
        window.currentChapterQuizId = id;
        window.currentChapterTitle = chapter.title;

        let html = `
            <div class="glass" style="padding:20px;margin-bottom:20px;">
                <h2>${chapter.id}. ${chapter.title}</h2>
                <p style="color:#aaa;margin-top:8px;">Answer all 10 questions to complete this chapter quiz.</p>
            </div>
        `;

        quiz.forEach((q, qi) => {
            html += `
                <div class="glass quiz-question" style="margin-bottom:18px;">
                    <h3>Question ${qi + 1} of ${quiz.length}</h3>
                    <p style="font-size:18px;line-height:1.6;margin:12px 0 16px;">${q.question}</p>
                    <div>
                        ${q.options.map((option, oi) => `
                            <label style="display:block;padding:12px 14px;margin:8px 0;border:1px solid rgba(255,255,255,0.12);border-radius:12px;cursor:pointer;">
                                <input type="radio" name="chapter_q_${qi}" value="${oi}" style="margin-right:10px;">
                                ${option.label}
                            </label>
                        `).join("")}
                    </div>
                </div>
            `;
        });

        html += `
            <button class="btn" onclick="submitChapterQuiz()">✅ Submit Quiz</button>
            <div id="chapterQuizResult" style="margin-top:20px;"></div>
            <br>
            <button class="btn" style="background:#374151" onclick="openCourse(selectedLanguage)">← Back to Chapters</button>
        `;

        container.innerHTML = html;
    } catch (error) {
        console.error(error);
        container.innerHTML = '<div class="message error">Chapter quiz loading error.</div>';
    }
}

function submitChapterQuiz() {
    const quiz = window.currentChapterQuiz || [];
    let score = 0;
    let answered = 0;

    quiz.forEach((q, qi) => {
        const selected = document.querySelector(`input[name="chapter_q_${qi}"]:checked`);
        if (selected) {
            answered++;
            if (q.options[Number(selected.value)].correct) score++;
        }
    });

    const result = document.getElementById("chapterQuizResult");
    if (!result) return;

    if (answered < quiz.length) {
        result.innerHTML = `<div class="message hint">Please answer all ${quiz.length} questions before submitting.</div>`;
        return;
    }

    const percent = Math.round((score / quiz.length) * 100);
    const message = percent >= 80
        ? "Excellent! You understood this chapter well."
        : percent >= 60
            ? "Good job! Review the chapter once more and try again."
            : "Keep practicing. Read the chapter again and retake the quiz.";

    result.innerHTML = `<div class="message ${percent >= 60 ? "hint" : "error"}"><strong>Score: ${score}/${quiz.length} (${percent}%)</strong><br>${message}</div>`;
}

async function openLesson(id) {
    showPage("lessonPage");

    const box = document.getElementById("lessonContent");
    box.innerHTML = '<div class="glass">Loading lesson...</div>';

    try {
        const response = await fetch(
            "/course-data?language=" +
            encodeURIComponent(selectedLanguage),
            {
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            box.innerHTML = `
                <div class="glass">
                    <h2>Unable to load lesson</h2>
                    <p>${data.message || "Course data could not be loaded."}</p>
                </div>
            `;
            return;
        }

        currentTopics = data.topics || [];

        const t = currentTopics.find(function(item) {
            return Number(item.id) === Number(id);
        });

        if (!t) {
            box.innerHTML = `
                <div class="glass">
                    <h2>Lesson not found</h2>
                    <p>Please go back and select the chapter again.</p>
                </div>
            `;
            return;
        }

        const definition =
            t.definition ||
            (t.content || "").split(/\n\s*\n/)[0] ||
            "Definition not available.";

        box.innerHTML = `
            <div class="lesson-layout">

                <article class="lesson-book">

                    <h1>${t.id}. ${t.title}</h1>

                    <div class="lesson-definition-box">
                        <h2>Definition</h2>
                        <p>${definition}</p>
                    </div>

                    <h2>Book Content</h2>
                    <p style="white-space:pre-line;">
                        ${t.content || ""}
                    </p>

                    <h2>Syntax</h2>
                    <pre class="lesson-code">${t.syntax || "Syntax not available."}</pre>

                    <h2>Example</h2>
                    <pre class="lesson-code">${t.example || "Example not available."}</pre>

                    <h2>Practice</h2>
                    <ol>
                        ${(t.practice || []).map(function(x) {
                            return `<li>${x}</li>`;
                        }).join("")}
                    </ol>

                    <div style="
                        margin-top:30px;
                        display:flex;
                        gap:12px;
                        flex-wrap:wrap;
                    ">

                        ${
                            id > 1
                            ? `
                                <button
                                    class="btn"
                                    onclick="openLesson(${id - 1})">
                                    ← Previous Chapter
                                </button>
                            `
                            : ""
                        }

                        ${
                            id < currentTopics.length
                            ? `
                                <button
                                    class="btn"
                                    onclick="openLesson(${id + 1})">
                                    Next Chapter →
                                </button>
                            `
                            : ""
                        }

                        <button
                            class="btn"
                            style="background:#475569"
                            onclick="openCourse(selectedLanguage)">
                            ← All Chapters
                        </button>

                    </div>

                </article>

            </div>
        `;

    } catch (error) {

        console.error("openLesson error:", error);

        box.innerHTML = `
            <div class="glass">
                <h2>Unable to load lesson</h2>
                <p>${error.message || "Something went wrong."}</p>
            </div>
        `;
    }
}
        

    

function submitLessonQuiz() {
    const quiz = window.currentLessonQuiz || [];
    let score = 0;
    let answered = 0;
    quiz.forEach((q, qi) => {
        const selected = document.querySelector(`input[name="lesson_q_${qi}"]:checked`);
        if (selected) {
            answered++;
            if (q.options[Number(selected.value)].correct) score++;
        }
    });
    const result = document.getElementById("lessonQuizResult");
    if (!result) return;
    if (answered < quiz.length) {
        result.innerHTML = `<div class="message hint">Please answer all ${quiz.length} questions before submitting.</div>`;
        return;
    }
    const percent = Math.round((score / quiz.length) * 100);
    let message = percent >= 80 ? "Excellent! You understood this lesson well." : percent >= 60 ? "Good job! Review the lesson once more and try again." : "Keep practicing. Read the lesson again and retake the quiz.";
    result.innerHTML = `<div class="message ${percent >= 60 ? "hint" : "error"}"><strong>Score: ${score}/${quiz.length} (${percent}%)</strong><br>${message}</div>`;
}


async function selectLanguage(language) {

    selectedLanguage = language;

    document
        .getElementById("selectedLanguage")
        .innerText =
        language;

    document
        .getElementById("quizLanguage")
        .innerText =
        language;

    document
        .getElementById("progressLanguage")
        .innerText =
        language;


    try {

        const response =
            await fetch("/select-language", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    language: language
                })

            });


        const data =
            await response.json();


        if (!data.success) {

            alert(data.message);

            return;

        }


        alert(
            language +
            " selected successfully!"
        );


        showPage("dashboard");

    }

    catch(error) {

        alert(
            "Could not save language."
        );

    }

}


// ========================================================
// EDITOR
// ========================================================

function openEditor() {

    const select = document.getElementById("editorLanguage");
    const label = document.getElementById("selectedLanguage");

    if (select) {
        select.value = selectedLanguage || "Python";
    }

    if (label) {
        label.innerText = selectedLanguage || "Python";
    }

    showPage("editorPage");

}

async function changeEditorLanguage(language) {

    selectedLanguage = language;

    const label = document.getElementById("selectedLanguage");
    if (label) {
        label.innerText = language;
    }

    const select = document.getElementById("editorLanguage");
    if (select) {
        select.value = language;
    }

    try {
        const response = await fetch("/select-language", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ language: language })
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
            console.log(data.message || "Could not save selected language.");
        }
    } catch (error) {
        console.log("Language selection error:", error);
    }
}


function clearEditor() {

    document
        .getElementById("codeEditor")
        .value = "";

    document
        .getElementById("analysisResult")
        .innerHTML = `
            <div class="message hint">
                Write your code and click Run Code or AI Code Analysis.
            </div>
        `;
}


async function runCode() {

    const code =
        document
            .getElementById("codeEditor")
            .value;

    const result =
        document
            .getElementById("analysisResult");

    if (!code.trim()) {
        result.innerHTML = `
            <div class="message error">
                ❌ Please write some code first.
            </div>
        `;
        return;
    }

    result.innerHTML = `
        <div class="message hint">
            ▶ Running your code...
        </div>
    `;

    try {
        const response = await fetch("/run-code", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                code: code,
                language: selectedLanguage || "Python"
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            let html = `
                <div class="message error">
                    <strong>❌ Runtime Error</strong>
                    <br><br>
                    ${escapeHtml(data.error || data.message || "Code execution failed.")}
                </div>
            `;

            if (data.corrected_code) {
                html += `
                    <div class="message success">
                        <strong>🔧 Corrected Code</strong>
                        <br><br>
                        <pre style="white-space:pre-wrap;background:#070711;padding:15px;border-radius:10px;overflow-x:auto;color:#e5e7eb;">${escapeHtml(data.corrected_code)}</pre>
                    </div>
                `;
            }

            result.innerHTML = html;
            return;
        }

        result.innerHTML = `
            <div class="message success">
                <strong>✅ Code executed successfully</strong>
                <br><br>
                <pre style="white-space:pre-wrap;background:#070711;padding:15px;border-radius:10px;overflow-x:auto;color:#e5e7eb;">${escapeHtml(data.output || "No output")}</pre>
            </div>
        `;

    } catch (error) {
        console.error("Code execution error:", error);
        result.innerHTML = `
            <div class="message error">
                <strong>❌ Server connection error</strong>
                <br><br>
                Make sure Flask is running and try again.
            </div>
        `;
    }
}


async function analyzeCode() {

    const code =
        document
            .getElementById("codeEditor")
            .value;

    const result =
        document
            .getElementById("analysisResult");

    if (!code.trim()) {
        result.innerHTML = `
            <div class="message error">
                ❌ Please write some code first.
            </div>
        `;
        return;
    }

    result.innerHTML = `
        <div class="message hint">
            🤖 AI Mentor is analyzing your code...
        </div>
    `;

    try {

        const response =
            await fetch("/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    code: code,
                    language: selectedLanguage || "Python"
                })
            });

        const data = await response.json();

        if (!response.ok || !data.success) {
            result.innerHTML = `
                <div class="message error">
                    ❌ ${escapeHtml(data.message || "Code analysis failed.")}
                </div>
            `;
            return;
        }

        let html = "";

        if (Array.isArray(data.errors) && data.errors.length > 0) {
            data.errors.forEach(function(error) {
                html += `
                    <div class="message error">
                        <strong>❌ Error</strong>
                        <br><br>
                        ${escapeHtml(error)}
                    </div>
                `;
            });
        }

        if (Array.isArray(data.hints) && data.hints.length > 0) {
            data.hints.forEach(function(hint) {
                html += `
                    <div class="message hint">
                        <strong>💡 Hint</strong>
                        <br><br>
                        ${escapeHtml(hint)}
                    </div>
                `;
            });
        }

        if (
            data.corrected_code &&
            String(data.corrected_code).trim() &&
            Array.isArray(data.errors) &&
            data.errors.length > 0
        ) {
            html += `
                <div class="message success">
                    <strong>🔧 Corrected Code</strong>
                    <br><br>
                    <pre style="white-space:pre-wrap;background:#070711;padding:15px;border-radius:10px;overflow-x:auto;color:#e5e7eb;">${escapeHtml(data.corrected_code)}</pre>
                </div>
            `;
        }

        if (Array.isArray(data.suggestions) && data.suggestions.length > 0) {
            data.suggestions.forEach(function(item) {
                html += `
                    <div class="message warning">
                        <strong>⭐ AI Mentor</strong>
                        <br><br>
                        ${escapeHtml(item)}
                    </div>
                `;
            });
        }

        if (Array.isArray(data.errors) && data.errors.length === 0) {
            html = `
                <div class="message success">
                    <strong>✅ No errors found</strong>
                    <br><br>
                    Your code is correct.
                </div>
            ` + html;
        }

        if (!html) {
            html = `
                <div class="message success">
                    <strong>✅ Analysis Complete</strong>
                    <br><br>
                    No problems were detected in the submitted code.
                </div>
            `;
        }

        result.innerHTML = html;

    } catch (error) {

        console.error("Code analysis error:", error);

        result.innerHTML = `
            <div class="message error">
                <strong>❌ Server connection error</strong>
                <br><br>
                Make sure Flask is running and try again.
            </div>
        `;
    }
}


function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ========================================================
// QUIZ
// ========================================================

function openQuiz() {

    showPage("quizPage");

    loadQuiz();

}


async function loadQuiz() {

    const container =
        document
            .getElementById("quizContainer");


    container.innerHTML =

        "Loading quiz...";


    try {

        const response =
            await fetch(
                "/quiz?language=" +
                encodeURIComponent(
                    selectedLanguage
                )
            );


        const data =
            await response.json();


        if (!data.success) {

            container.innerHTML =
                data.message;

            return;

        }


        let html = "";

        data.questions.forEach(
            function(q, index) {

                html += `

                    <div>

                        <h3>
                            ${index + 1}.
                            ${q.question}
                        </h3>

                        <br>

                `;


                q.options.forEach(
                    function(option) {

                        html += `

                            <button
                                class="option"
                                onclick="answerQuiz(
                                    ${q.id},
                                    '${option}'
                                )"
                            >

                                ${option}

                            </button>

                        `;

                    }
                );


                html += `

                    </div>

                    <hr
                        style="
                        margin:25px 0;
                        border-color:#3b2b50;
                        "
                    >

                `;

            }
        );


        container.innerHTML = html;

    }

    catch(error) {

        container.innerHTML =
            "Quiz loading error.";

    }

}


async function answerQuiz(id, answer) {

    try {

        const response =
            await fetch("/quiz-answer", {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body: JSON.stringify({

                    id: id,

                    answer: answer

                })

            });


        const data =
            await response.json();


        alert(data.message);

    }

    catch(error) {

        alert(
            "Could not submit answer."
        );

    }

}



// ========================================================
// DAILY CODING TEST
// ========================================================

window.dailyTimerInterval = null;

window.dailyTestSubmitted = false;
function openDailyTest() {
    showPage("dailyTestPage");
    loadDailyTest();
}

function stopDailyTimer() {
    if (dailyTimerInterval) {
        clearInterval(dailyTimerInterval);
        dailyTimerInterval = null;
    }
}

function startDailyTimer(seconds) {
    stopDailyTimer();

    let remaining = seconds;
    const timer = document.getElementById("dailyTimer");

    function paint() {
        if (!timer) return;

        const minutes = Math.floor(remaining / 60);
        const secs = remaining % 60;
        timer.innerText =
            String(minutes).padStart(2, "0") +
            ":" +
            String(secs).padStart(2, "0");

        if (remaining <= 0) {
            stopDailyTimer();
            if (!dailyTestSubmitted) {
                submitDailyTest(true);
            }
            return;
        }

        remaining--;
    }

    paint();
    dailyTimerInterval = setInterval(paint, 1000);
}

async function loadDailyTest() {
    dailyTestSubmitted = false;
    stopDailyTimer();

    const box = document.getElementById("dailyTestContent");
    if (!box) return;

    box.innerHTML = '<div class="glass">Loading today\'s fresh questions...</div>';

    try {
        const response = await fetch("/daily-test?ts=" + Date.now(), {
            cache: "no-store"
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
            box.innerHTML = `
                <div class="glass">
                    <h2>Unable to load Daily Test</h2>
                    <p>${escapeHtml(data.message || "Please login and try again.")}</p>
                </div>`;
            return;
        }

        if (data.completed) {
            box.innerHTML = `
                <div class="daily-test-header">
                    <div class="daily-test-title">
                        <h1>📝 Daily Coding Test</h1>
                        <p>${escapeHtml(data.language)} • ${escapeHtml(data.date)}</p>
                    </div>
                </div>

                <div class="daily-result">
                    <div class="daily-test-badge">✓ COMPLETED TODAY</div>
                    <div class="daily-score">${data.score}/${data.total}</div>
                    <p style="color:#64748b;">
                        Today's test is already completed. Come back tomorrow for a completely fresh test.
                    </p>
                    <br>
                    <button class="btn" onclick="backDashboard()">← Back to Dashboard</button>
                </div>

                <div class="daily-history">
                    <h2 style="color:#102f63;margin-bottom:10px;">Recent Daily Test History</h2>
                    <div id="dailyHistoryList">Loading history...</div>
                </div>
            `;
            loadDailyHistory();
            return;
        }

        let html = `
            <div class="daily-test-header">
                <div class="daily-test-title">
                    <div class="daily-test-badge">📝 TODAY'S CHALLENGE</div>
                    <h1>Daily Coding Test</h1>
                    <p>${escapeHtml(data.language)} • ${escapeHtml(data.date)} • 10 fresh questions</p>
                </div>

                <div class="daily-timer">
                    <span>Time Left</span>
                    <strong id="dailyTimer">15:00</strong>
                </div>
            </div>
        `;

        data.questions.forEach(function(q, index) {
            html += `
                <div class="daily-question-card">
                    <div class="daily-q-number">Question ${index + 1} of ${data.questions.length}</div>
                    <h3>${escapeHtml(q.question)}</h3>

                    ${q.options.map(function(option, oi) {
                        return `
                            <label class="daily-option">
                                <input
                                    type="radio"
                                    name="daily_${escapeHtml(q.id)}"
                                    value="${oi}"
                                >
                                ${escapeHtml(option)}
                            </label>
                        `;
                    }).join("")}
                </div>
            `;
        });

        html += `
            <div class="daily-submit-row">
                <button class="btn" onclick="submitDailyTest(false)">
                    ✅ Submit Today's Test
                </button>
            </div>
            <div id="dailyTestResult"></div>
        `;

        box.innerHTML = html;

        window.currentDailyQuestions = data.questions;
        startDailyTimer(15 * 60);

    } catch (error) {
        console.error("DAILY TEST ERROR:", error);
        box.innerHTML = `
            <div class="glass">
                <h2>Daily Test connection error</h2>
                <p>Please make sure Flask is running and try again.</p>
            </div>`;
    }
}

async function submitDailyTest(autoSubmit) {
    if (dailyTestSubmitted) return;

    const questions = window.currentDailyQuestions || [];
    if (!questions.length) return;

    const answers = {};
    let answered = 0;

    questions.forEach(function(q) {
        const selected = document.querySelector(
            `input[name="daily_${q.id}"]:checked`
        );

        if (selected) {
            answers[q.id] = q.options[Number(selected.value)];
            answered++;
        }
    });

    if (!autoSubmit && answered < questions.length) {
        const result = document.getElementById("dailyTestResult");
        if (result) {
            result.innerHTML = `
                <div class="message hint">
                    Please answer all ${questions.length} questions before submitting.
                </div>`;
        }
        return;
    }

    dailyTestSubmitted = true;
    stopDailyTimer();

    const result = document.getElementById("dailyTestResult");
    if (result) {
        result.innerHTML = `
            <div class="daily-result">
                <p style="color:#64748b;">Submitting your Daily Test...</p>
            </div>`;
    }

    try {
        const response = await fetch("/daily-test-submit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                answers: answers
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            dailyTestSubmitted = false;
            if (result) {
                result.innerHTML = `
                    <div class="message error">
                        ${escapeHtml(data.message || "Could not submit the test.")}
                    </div>`;
            }
            return;
        }

        if (result) {
            result.innerHTML = `
                <div class="daily-result">
                    <div class="daily-test-badge">✓ TEST SUBMITTED</div>
                    <div class="daily-score">${data.score}/${data.total}</div>
                    <p style="color:#64748b;font-size:16px;">
                        ${escapeHtml(data.message)}
                    </p>
                    <br>
                    <button class="btn" onclick="loadDailyTest()">
                        View Today's Result
                    </button>
                    <button class="btn btn-secondary" style="margin-left:8px;" onclick="backDashboard()">
                        Dashboard
                    </button>
                </div>
            `;
        }

        document.querySelectorAll(".daily-option input").forEach(function(input) {
            input.disabled = true;
        });

    } catch (error) {
        console.error(error);
        dailyTestSubmitted = false;
        if (result) {
            result.innerHTML = `
                <div class="message error">
                    Could not connect to the Daily Test server.
                </div>`;
        }
    }
}

async function loadDailyHistory() {
    const box = document.getElementById("dailyHistoryList");
    if (!box) return;

    try {
        const response = await fetch("/daily-test-history?ts=" + Date.now(), {
            cache: "no-store"
        });
        const data = await response.json();

        if (!data.success || !data.history.length) {
            box.innerHTML = '<p style="color:#64748b;">No previous daily tests yet.</p>';
            return;
        }

        box.innerHTML = data.history.map(function(item) {
            return `
                <div class="daily-history-row">
                    <span>${escapeHtml(item.date)} • ${escapeHtml(item.language)}</span>
                    <strong>${item.score}/${item.total}</strong>
                </div>
            `;
        }).join("");

    } catch (error) {
        box.innerHTML = '<p style="color:#64748b;">History could not be loaded.</p>';
    }
}


// ========================================================
// CHATBOT
// ========================================================

function openChat() {

    const page = document.getElementById("chatPage");

    if (!page) {
        alert("Chatbot page could not be loaded. Please restart the app.");
        return;
    }

    showPage("chatPage");

    setTimeout(function() {
        const input = document.getElementById("chatInput");
        if (input) input.focus();
    }, 50);

}

async function sendMessage() {

    const input = document.getElementById("chatInput");
    const chat = document.getElementById("chatMessages");

    const message = input.value.trim();

    if (!message) return;

    // User message
    chat.innerHTML += `
        <div class="chat-row user-row">
            <div class="chat-bubble user-bubble">
                ${escapeHTML(message)}
            </div>
            <div class="chat-avatar user-avatar-chat">👤</div>
        </div>
    `;

    input.value = "";
    input.style.height = "auto";

    // Thinking message
    chat.innerHTML += `
        <div id="typing" class="chat-row bot-row">
            <div class="chat-avatar bot-avatar">🤖</div>
            <div class="chat-bubble bot-bubble">
                <div class="bot-name">AI Coding Mentor</div>
                <span class="thinking-text">Thinking...</span>
            </div>
        </div>
    `;

    chat.scrollTop = chat.scrollHeight;

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        if (!response.ok) {
            throw new Error("Server error");
        }

        const data = await response.json();

        const typing = document.getElementById("typing");

        if (typing) {
            typing.remove();
        }

        let reply = data.reply || "Something went wrong.";

        // Escape HTML
        reply = escapeHTML(reply);

        // Convert new lines to <br>
        reply = reply.replace(/\r?\n/g, "<br>");

        // Basic markdown formatting
        reply = reply.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        reply = reply.replace(/`([^`]+)`/g, "<code>$1</code>");

        chat.innerHTML += `
            <div class="chat-row bot-row">
                <div class="chat-avatar bot-avatar">🤖</div>

                <div class="chat-bubble bot-bubble">

                    <div class="bot-name">
                        AI Coding Mentor
                    </div>

                    <div class="bot-answer">
                        ${reply}
                    </div>

                </div>
            </div>
        `;

        chat.scrollTop = chat.scrollHeight;

    } catch (error) {

        console.error("Chat error:", error);

        const typing = document.getElementById("typing");

        if (typing) {
            typing.remove();
        }

        chat.innerHTML += `
            <div class="chat-row bot-row">

                <div class="chat-avatar bot-avatar">🤖</div>

                <div class="chat-bubble bot-bubble">

                    <div class="bot-name">
                        AI Coding Mentor
                    </div>

                    ❌ Unable to connect to AI Mentor.

                </div>

            </div>
        `;

        chat.scrollTop = chat.scrollHeight;
    }
}


function escapeHTML(text) {

    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
// ========================================================
// PROGRESS
// ========================================================

async function openProgress() {

    showPage("progressPage");


    try {

        const response =
            await fetch("/progress");


        const data =
            await response.json();


        if (!data.success) {

            return;

        }


        document
            .getElementById("progressFill")
            .style.width =
            data.progress + "%";


        document
            .getElementById("progressText")
            .innerText =
            data.progress + "%";


        document
            .getElementById("quizScore")
            .innerText =
            data.quiz_score;


        document
            .getElementById("progressLanguage")
            .innerText =
            data.language;

    }

    catch(error) {

        console.error(error);

    }

}
</script>

<script src="{{ url_for('static', filename='js_actual.js') }}"></script>

</body>

</html>
"""


# Ensure an old database is repaired before the first request.
init_db()

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template_string(PAGE)


# =========================================================
# FLASK CONNECTION TEST
# =========================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"success": True, "message": "Flask Connected Successfully!"})


# =========================================================
# REGISTER
# =========================================================
@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json(silent=True) or request.form.to_dict() or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()


    if not name or not email or not password:

        return jsonify({
            "success": False,
            "message": "Name, email and password are required."
        }), 400


    conn = get_db()


    try:

        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()


        if existing_user:

            return jsonify({
                "success": False,
                "message": "Email already registered."
            })


        cursor = conn.execute(
            """
            INSERT INTO users (username, name, email, password)
VALUES (?, ?, ?, ?)
            """,
           (
    name,
    name,
    email,
    generate_password_hash(password)
)
        )


        conn.commit()


        # Save the newly created user's information
        session["user_id"] = cursor.lastrowid
        session["user_name"] = name
        session["user_email"] = email


        return jsonify({

            "success": True,

            "message":
                "Account created successfully.",

            "name": name
        })


    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Email already registered."
        }), 400


    finally:

        conn.close()

# =========================================================
# LOGIN
# =========================================================

@app.route("/check-columns")
def check_columns():
    conn = get_db()
    try:
        rows = conn.execute("PRAGMA table_info(users)").fetchall()
        return jsonify([
            {"column": row["name"]}
            for row in rows
        ])
    finally:
        conn.close()
@app.route("/check-user")
def check_user():

    conn = get_db()

    try:
        users = conn.execute(
            "SELECT id, name, email FROM users"
        ).fetchall()

        result = []

        for user in users:
            result.append({
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            })

        return jsonify(result)

    finally:
        conn.close()



@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email ID and password are required."
        }), 400

    conn = get_db()

    try:
        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(TRIM(email)) = LOWER(?)
            LIMIT 1
            """,
            (email,)
        ).fetchone()

        if user is None:
            return jsonify({
                "success": False,
                "message": "Email not registered. Please sign up first."
            }), 401

        stored_password = str(user["password"] or "")
        password_ok = False

        # Current Werkzeug password hashes
        if stored_password.startswith(
            ("scrypt:", "pbkdf2:", "argon2:")
        ):
            try:
                password_ok = check_password_hash(
                    stored_password, password
                )
            except (ValueError, TypeError):
                password_ok = False

        # Legacy SHA-256 password hashes
        elif len(stored_password) == 64 and all(
            c in "0123456789abcdefABCDEF"
            for c in stored_password
        ):
            password_ok = (
                hashlib.sha256(password.encode("utf-8")).hexdigest()
                == stored_password.lower()
            )

        # Legacy plain-text passwords, if any
        else:
            password_ok = (stored_password == password)

        if not password_ok:
            return jsonify({
                "success": False,
                "message": "Incorrect password. Please check and try again."
            }), 401

        name = str(user["name"] or "").strip() if "name" in user.keys() else ""
        if not name and "username" in user.keys():
            name = str(user["username"] or "").strip()

        if not name:
            name = "Student"

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = name
        session["user_email"] = user["email"]

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "name": name,
            "email": user["email"]
        })

    except sqlite3.Error:
        app.logger.exception("Login database error")
        return jsonify({
            "success": False,
            "message": "Database error. Check the Flask terminal."
        }), 500

    finally:
        conn.close()

# =========================================================
# COURSE DATA - BOOK CONTENT + CHAPTER QUIZ
# =========================================================

@app.route("/course-data")
def course_data():
    language = request.args.get("language", "Python")

    if language not in LANGUAGES:
        return jsonify({
            "success": False,
            "message": "Invalid language.",
            "topics": []
        }), 400

    # Get chapters from the existing course data
    raw = courses.get(language, {})
    chapters = raw.get("chapters", []) if isinstance(raw, dict) else []

    # If chapters are missing, use COURSE_TOPICS
    if not chapters:
        chapter_names = COURSE_TOPICS.get(language, [])
        chapters = [
            {
                "chapter": i,
                "title": title,
                "definition": f"Introduction to {title}.",
                "content": f"In this chapter, you will learn {title} in {language}.",
                "syntax": "",
                "example": "",
                "output": "",
                "practice": [],
                "quiz": []
            }
            for i, title in enumerate(chapter_names, start=1)
        ]

    topics = []

    for ch in chapters:
        topics.append({
            "id": ch.get("chapter", len(topics) + 1),
            "title": ch.get("title", ""),
            "definition": ch.get(
                "definition",
                str(ch.get("content", "")).split("\n\n")[0]
                if ch.get("content") else ""
            ),
            "content": ch.get("content", ""),
            "syntax": ch.get("syntax", ""),
            "example": ch.get("example", ""),
            "output": ch.get("output", ""),
            "practice": ch.get("practice", []),
            "quiz": ch.get("quiz", [])
        })

    # Improve the Python Variables chapter if the preview file exists
    if language == "Python":
        preview_path = Path(__file__).with_name(
            "python_variables_preview.json"
        )

        if preview_path.exists():
            try:
                with preview_path.open("r", encoding="utf-8") as file:
                    improved = json.load(file)

                for topic in topics:
                    if (
                        topic["id"] == improved.get("chapter", 2)
                        and topic["title"].strip().lower() == "variables"
                    ):
                        for key in (
                            "definition", "content", "syntax",
                            "example", "output", "practice", "quiz"
                        ):
                            if key in improved:
                                topic[key] = improved[key]
                        break

            except (OSError, json.JSONDecodeError) as error:
                app.logger.error(
                    "Could not load Variables preview: %s", error
                )

    return jsonify({
        "success": True,
        "language": language,
        "topics": topics
    })


# =========================================================
# LANGUAGE
# =========================================================

@app.route(
    "/select-language",
    methods=["POST"]
)
def select_language():

    if "username" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        })


    data = request.get_json(silent=True) or {}

    language = data.get("language", "")


    if language not in LANGUAGES:

        return jsonify({
            "success": False,
            "message": "Invalid language."
        })


    conn = get_db()


    conn.execute(
        """
        UPDATE users
        SET language = ?
        WHERE username = ?
        """,
        (
            language,
            session["username"]
        )
    )


    conn.commit()

    conn.close()


    return jsonify({
        "success": True,
        "message":
            language + " selected."
    })


# =========================================================
# CODE EDITOR - RUN CODE
# =========================================================

@app.route(
    "/run-code",
    methods=["POST"]
)
def run_code():
    data = request.get_json(silent=True) or {}
    code = str(data.get("code", ""))
    language = str(data.get("language", "Python")).strip()

    if not code.strip():
        return jsonify({"success": False, "message": "Code is empty."}), 400
    if language not in LANGUAGES:
        return jsonify({"success": False, "message": f"Unsupported programming language: {language}"}), 400

    configs = {
        "Python": ("main.py", None, lambda d, f: [sys.executable, f], [sys.executable]),
        "C": ("main.c", lambda d, f: ["gcc", f, "-o", str(d / "main.exe")], lambda d, f: [str(d / "main.exe")], ["gcc"]),
        "C++": ("main.cpp", lambda d, f: ["g++", f, "-o", str(d / "main.exe")], lambda d, f: [str(d / "main.exe")], ["g++"]),
        "Java": ("Main.java", lambda d, f: ["javac", f], lambda d, f: ["java", "-cp", str(d), "Main"], ["javac", "java"]),
        "JavaScript": ("main.js", None, lambda d, f: ["node", f], ["node"]),
        "R": ("main.R", None, lambda d, f: ["Rscript", f], ["Rscript"]),
        "C#": ("Main.cs", None, lambda d, f: ["dotnet", "run", "--project", str(d / "Main.csproj"), "--no-restore"], ["dotnet"]),
        "Go": ("main.go", None, lambda d, f: ["go", "run", f], ["go"]),
        "PHP": ("main.php", None, lambda d, f: ["php", f], ["php"]),
        "Ruby": ("main.rb", None, lambda d, f: ["ruby", f], ["ruby"]),
        "Kotlin": ("Main.kt", lambda d, f: ["kotlinc", f, "-include-runtime", "-d", str(d / "main.jar")], lambda d, f: ["java", "-jar", str(d / "main.jar")], ["kotlinc", "java"]),
        "Swift": ("main.swift", None, lambda d, f: ["swift", f], ["swift"]),
        "TypeScript": ("main.ts", lambda d, f: ["tsc", f, "--target", "ES2020", "--module", "commonjs", "--outDir", str(d / "tsout")], lambda d, f: ["node", str(d / "tsout" / "main.js")], ["tsc", "node"]),
        "Rust": ("main.rs", lambda d, f: ["rustc", f, "-o", str(d / "main.exe")], lambda d, f: [str(d / "main.exe")], ["rustc"]),
        "Dart": ("main.dart", None, lambda d, f: ["dart", f], ["dart"]),
    }

    filename, compiler, runner, needed = configs[language]
    temp_dir = None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="ai_coding_mentor_"))
        source = temp_dir / filename
        source.write_text(code, encoding="utf-8")

        if language == "C#":
            (temp_dir / "Main.csproj").write_text(
                '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>disable</Nullable></PropertyGroup></Project>',
                encoding="utf-8"
            )

        missing = [x for x in needed if shutil.which(x) is None]
        if missing:
            return jsonify({"success": False, "error": f"{language} Run Code needs {', '.join(missing)} installed and available in PATH."}), 400

        if compiler:
            result = subprocess.run(compiler(temp_dir, filename), cwd=str(temp_dir), capture_output=True, text=True, timeout=5, shell=False)
            if result.returncode != 0:
                return jsonify({"success": False, "error": (result.stderr or result.stdout or f"{language} compilation failed.").strip()}), 400

        result = subprocess.run(runner(temp_dir, filename), cwd=str(temp_dir), capture_output=True, text=True, timeout=5, shell=False)
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()
        if result.returncode != 0:
            return jsonify({"success": False, "error": error or f"{language} program exited with an error.", "output": output}), 400
        return jsonify({"success": True, "output": output, "error": ""})

    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Execution timed out after 5 seconds."}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


# =========================================================
# CODE ANALYSIS
# =========================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():
    data = request.get_json(silent=True) or {}
    code = str(data.get("code", ""))
    language = str(data.get("language", "Python"))

    if not code.strip():
        return jsonify({
            "success": False,
            "message": "Code is empty."
        }), 400

    errors = []
    hints = []
    suggestions = []
    corrected_code = ""

    # ---------------------------------------------------------
    # STEP 1: Real syntax check for Python
    # ---------------------------------------------------------
    if language == "Python":
        try:
            compile(code, "<student_code>", "exec")
        except SyntaxError as e:
            line = e.lineno or "unknown"
            message = e.msg or "Invalid syntax."
            errors.append(f"Syntax error on line {line}: {message}")
            hints.append(
                "Check brackets, quotes, colons and indentation around the reported line."
            )
        except Exception as e:
            errors.append(f"Python analysis error: {str(e)}")

    
    # ---------------------------------------------------------
    # STEP 2: Basic checks and C/C++ compiler check
    # ---------------------------------------------------------
    runtime_error = ""

    if language in ["C", "C++"]:
        compact = re.sub(r"\s+", "", code)

        if "main(" not in compact and "main()" not in compact:
            errors.append("main() function was not detected.")

        if "#include" not in code and ("printf(" in code or "scanf(" in code):
            hints.append("Check that the required standard header is included.")

        meaningful_lines = [
            line.strip()
            for line in code.splitlines()
            if line.strip() and not line.strip().startswith("//")
        ]

        if meaningful_lines and any(
            line.startswith(("printf(", "scanf(", "return ", "int ", "float ",
                             "double ", "char ", "cout", "cin"))
            and not line.endswith((";", "{", "}"))
            for line in meaningful_lines
        ):
            hints.append("Check whether the statement should end with a semicolon.")

        temp_dir = None
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="ai_analysis_"))

            if language == "C":
                source_file = temp_dir / "main.c"
                compiler = "gcc"
            else:
                source_file = temp_dir / "main.cpp"
                compiler = "g++"

            executable = temp_dir / "main.exe"
            source_file.write_text(code, encoding="utf-8")

            if shutil.which(compiler) is None:
                errors.append(f"{compiler} is not available in PATH.")
            else:
                completed = subprocess.run(
                    [compiler, str(source_file), "-o", str(executable)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(temp_dir)
                )

                if completed.returncode != 0:
                    compiler_error = (
                        completed.stderr or completed.stdout or "Compilation failed."
                    ).strip()

                    runtime_error = compiler_error
                    errors.append(
                        f"{language} compilation error: {compiler_error}"
                    )

        except subprocess.TimeoutExpired:
            runtime_error = f"{language} compilation timed out."
            errors.append(runtime_error)

        except Exception as e:
            runtime_error = str(e)
            errors.append(
                f"{language} compiler check failed: {str(e)}"
            )

        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    elif language == "Java":
        if "class " not in code:
            errors.append("No Java class was detected.")
        if "System.out" in code and ";" not in code:
            hints.append("Check that Java statements end with a semicolon.")

    elif language == "JavaScript":
        if "console.log" not in code and "function" not in code and "=>" not in code:
            suggestions.append(
                "Add executable JavaScript logic such as a function or console.log()."
            )

    elif language == "R":
        if "<-" not in code and "=" not in code and code.strip():
            hints.append("Use <- or = for variable assignment.")

    elif language == "C#":
        if "class " not in code and "struct " not in code:
            errors.append("No C# class or struct was detected.")


    # ---------------------------------------------------------
    # STEP 3: REAL RUNTIME CHECK FOR PYTHON
    # ---------------------------------------------------------
    if language == "Python" and not errors:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8"
            ) as temp_file:
                temp_file.write(code)
                temp_path = temp_file.name

            completed = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            if completed.returncode != 0:
                runtime_error = (completed.stderr or "").strip()
                if runtime_error:
                    errors.append(
                        "Runtime error detected: " +
                        runtime_error.splitlines()[-1]
                    )

        except subprocess.TimeoutExpired:
            runtime_error = "Execution timed out after 5 seconds."
        except Exception as e:
            runtime_error = str(e)
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


    # ---------------------------------------------------------
    # STEP 4: GEMINI AI CODE REVIEW
    # ---------------------------------------------------------

    prompt = f"""
You are an expert programming teacher and code reviewer.

Analyze the student's complete {language} code.

Rules:
- Find ONLY real errors or clear bugs.
- If the code is correct, errors must be [].
- If the code is correct, provide a clear explanation in suggestions confirming that the code is correct.
- Always return at least one useful suggestion or explanation.
- Explain exactly why an error occurs.
- If an error exists, provide corrected complete code.
- Preserve the original purpose and logic.
- Do not change the programming language.
- Do not invent libraries, APIs, variables, or requirements.
- Return JSON only.

Return exactly:
{{
  "errors": ["real error and why it happens"],
  "hints": ["specific clue for fixing the error"],
  "suggestions": ["optional improvement"],
  "corrected_code": "complete corrected code"
}}

Runtime execution information:
{runtime_error or "No runtime error was observed."}

Student code:
---START CODE---
{code}
---END CODE---
"""

    gemini_api_key = os.getenv("GEMINI_API_KEY")


    if not gemini_api_key:
        return jsonify({
            "success": False,
            "message": "Gemini API key is not configured."
        }), 500

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": gemini_api_key
            },
            json={
                "system_instruction": {
                    "parts": [{
                        "text": "You are a careful programming code reviewer. Return valid JSON only."
                    }]
                },
                "contents": [{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            },
            timeout=90
        )

        if response.status_code != 200:
            print("Gemini Analysis Status:", response.status_code)
            print("Gemini Analysis Error:", response.text)

            return jsonify({
                "success": False,
                "message": "Gemini AI code analysis failed. Please try again."
            }), 500

        result = response.json()

        raw = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )

        raw = re.sub(
            r"^\s*```(?:json)?\s*|\s*```\s*$",
            "",
            raw,
            flags=re.IGNORECASE
        ).strip()

        ai_result = json.loads(raw)

        if not isinstance(ai_result, dict):
            raise ValueError("Invalid AI response format")

        ai_errors = ai_result.get("errors", [])
        ai_hints = ai_result.get("hints", [])
        ai_suggestions = ai_result.get("suggestions", [])
        ai_corrected = ai_result.get("corrected_code", "")

        if isinstance(ai_errors, list):
            for item in ai_errors:
                if str(item).strip():
                    errors.append(str(item).strip())

        if isinstance(ai_hints, list):
            for item in ai_hints:
                if str(item).strip():
                    hints.append(str(item).strip())

        if isinstance(ai_suggestions, list):
            for item in ai_suggestions:
                if str(item).strip():
                    suggestions.append(str(item).strip())

        if ai_corrected and str(ai_corrected).strip():
            corrected_code = str(ai_corrected).strip()

        errors = list(dict.fromkeys(errors))
        hints = list(dict.fromkeys(hints))
        suggestions = list(dict.fromkeys(suggestions))

        if not errors:
            corrected_code = ""

        return jsonify({
            "success": True,
            "errors": errors,
            "hints": hints,
            "suggestions": suggestions,
            "corrected_code": corrected_code,
            "ai_analysis": True
        })

    except requests.exceptions.RequestException as e:
        print("Gemini Analysis Connection Error:", repr(e))

        return jsonify({
            "success": False,
            "message": "Gemini AI could not connect. Please try again."
        }), 500

    except Exception as e:
        print("Gemini Code Analysis Error:", repr(e))

        return jsonify({
            "success": False,
            "message": "AI code analysis failed. Please check server logs."
        }), 500


# =========================================================
# QUIZ DATA
# =========================================================

QUIZZES = {

    "Python": [

        {
            "id": 1,
            "question":
                "Which keyword defines a function in Python?",
            "options":
                ["func", "def", "function", "define"],
            "answer":
                "def"
        },

        {
            "id": 2,
            "question":
                "Which data type stores True or False?",
            "options":
                ["int", "str", "bool", "float"],
            "answer":
                "bool"
        },

        {
            "id": 3,
            "question":
                "Which symbol is used for comments?",
            "options":
                ["//", "#", "/*", "--"],
            "answer":
                "#"
        }

    ],


    "C": [

        {
            "id": 1,
            "question":
                "Which function is the entry point of a C program?",
            "options":
                ["start()", "main()", "run()", "begin()"],
            "answer":
                "main()"
        },

        {
            "id": 2,
            "question":
                "Which symbol ends most C statements?",
            "options":
                [".", ":", ";", ","],
            "answer":
                ";"
        }

    ],


    "C++": [

        {
            "id": 1,
            "question":
                "Which language is C++ based on?",
            "options":
                ["Java", "C", "Python", "R"],
            "answer":
                "C"
        },

        {
            "id": 2,
            "question":
                "Which operator is used for output with cout?",
            "options":
                ["<<", ">>", "::", "->"],
            "answer":
                "<<"
        }

    ],


    "Java": [

        {
            "id": 1,
            "question":
                "Which keyword creates a class in Java?",
            "options":
                ["class", "define", "struct", "object"],
            "answer":
                "class"
        },

        {
            "id": 2,
            "question":
                "Which method is commonly the Java program entry point?",
            "options":
                [
                    "start()",
                    "main()",
                    "run()",
                    "execute()"
                ],
            "answer":
                "main()"
        }

    ],


    "JavaScript": [

        {
            "id": 1,
            "question":
                "Which keyword can declare a block-scoped variable?",
            "options":
                ["let", "define", "varname", "integer"],
            "answer":
                "let"
        },

        {
            "id": 2,
            "question":
                "Which function prints a message to the console?",
            "options":
                [
                    "print()",
                    "console.log()",
                    "write()",
                    "display()"
                ],
            "answer":
                "console.log()"
        }

    ],


    "R": [

        {
            "id": 1,
            "question":
                "Which operator is commonly used for assignment in R?",
            "options":
                ["<-", "=>", "===", "::"],
            "answer":
                "<-"
        }

    ],


    "C#": [

        {
            "id": 1,
            "question":
                "Which keyword defines a class in C#?",
            "options":
                ["class", "type", "object", "define"],
            "answer":
                "class"
        }

    ],


    "PHP": [

        {
            "id": 1,
            "question":
                "Which tag commonly starts PHP code?",
            "options":
                [
                    "<?php",
                    "<php>",
                    "<?",
                    "<script>"
                ],
            "answer":
                "<?php"
        }

    ]

}



# =========================================================
# DAILY CODING TEST
# =========================================================

DAILY_LANGUAGE_RULES = {
    "Python": {
        "function": "def",
        "output": "print()",
        "comment": "#",
        "entry": "The Python interpreter starts executing from the first executable statement."
    },
    "C": {
        "function": "A function definition can use a return type followed by the function name.",
        "output": "printf()",
        "comment": "//",
        "entry": "main()"
    },
    "C++": {
        "function": "A function definition can use a return type followed by the function name.",
        "output": "cout",
        "comment": "//",
        "entry": "main()"
    },
    "Java": {
        "function": "A method is declared with a return type (or void) and a method name.",
        "output": "System.out.println()",
        "comment": "//",
        "entry": "main()"
    },
    "JavaScript": {
        "function": "function",
        "output": "console.log()",
        "comment": "//",
        "entry": "JavaScript execution depends on its host environment."
    },
    "R": {
        "function": "function()",
        "output": "print()",
        "comment": "#",
        "entry": "R scripts execute statements in their program order."
    },
    "C#": {
        "function": "A method is declared with a return type (or void) and a method name.",
        "output": "Console.WriteLine()",
        "comment": "//",
        "entry": "Main()"
    },
    "Go": {
        "function": "func",
        "output": "fmt.Println()",
        "comment": "//",
        "entry": "main()"
    },
    "PHP": {
        "function": "function",
        "output": "echo",
        "comment": "//",
        "entry": "PHP executes statements in the script from top to bottom."
    },
    "Ruby": {
        "function": "def",
        "output": "puts",
        "comment": "#",
        "entry": "Ruby executes statements in program order."
    },
    "Kotlin": {
        "function": "fun",
        "output": "println()",
        "comment": "//",
        "entry": "main()"
    },
    "Swift": {
        "function": "func",
        "output": "print()",
        "comment": "//",
        "entry": "main app lifecycle or the program's top-level entry mechanism."
    },
    "TypeScript": {
        "function": "function",
        "output": "console.log()",
        "comment": "//",
        "entry": "TypeScript is compiled to JavaScript, which is then executed by a JavaScript runtime."
    },
    "Rust": {
        "function": "fn",
        "output": "println!()",
        "comment": "//",
        "entry": "main()"
    },
    "Dart": {
        "function": "void",
        "output": "print()",
        "comment": "//",
        "entry": "main()"
    }
}

def _daily_shuffle(options, seed):
    import random
    rng = random.Random(seed)
    options = list(options)
    rng.shuffle(options)
    return options

def generate_daily_questions(language, test_day=None):
    """Generate a deterministic 10-question test for one language/day.
    The date changes the question values and rotates the question templates,
    so a new calendar day produces a new test while the same day is stable.
    """
    import random

    language = language if language in LANGUAGES else "Python"
    test_day = test_day or date.today().isoformat()

    try:
        seed = int(test_day.replace("-", "")) + sum(ord(c) for c in language)
    except Exception:
        seed = sum(ord(c) for c in (test_day + language))

    rng = random.Random(seed)

    # Different values each day.
    a = rng.randint(2, 9)
    b = rng.randint(2, 9)
    c = rng.randint(2, 6)
    n = rng.randint(4, 12)
    percent = rng.choice([10, 15, 20, 25, 30, 40, 50])
    number = rng.randint(2, 9)
    base = rng.randint(2, 8)

    questions = [
        {
            "id": "u1",
            "question": f"What is the value of {a} + {b} × {c}?",
            "options": [
                str(a + b * c),
                str((a + b) * c),
                str(a * b + c),
                str(a + b + c),
            ],
            "answer": str(a + b * c),
        },
        {
            "id": "u2",
            "question": f"A value of {number * 10} is increased by {percent}%. What is the new value?",
            "options": [
                str(number * 10 * (100 + percent) // 100),
                str(number * 10 + percent),
                str(number * 10 * percent // 100),
                str(number * 10 - percent),
            ],
            "answer": str(number * 10 * (100 + percent) // 100),
        },
        {
            "id": "u3",
            "question": "Which data structure follows FIFO order?",
            "options": ["Stack", "Queue", "Tree", "Graph"],
            "answer": "Queue",
        },
        {
            "id": "u4",
            "question": "What is the time complexity of scanning all n elements of an array once?",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"],
            "answer": "O(n)",
        },
        {
            "id": "u5",
            "question": f"If a loop runs from 1 through {n} inclusive, how many iterations does it make?",
            "options": [str(n), str(n - 1), str(n + 1), str(n * 2)],
            "answer": str(n),
        },
        {
            "id": "u6",
            "question": f"What is {base}²?",
            "options": [str(base * base), str(base * 2), str(base + base), str(base ** 3)],
            "answer": str(base * base),
        },
        {
            "id": "u7",
            "question": "Why is a base case important in recursion?",
            "options": [
                "It stops recursive calls from continuing indefinitely.",
                "It always makes the program run in constant time.",
                "It removes the need for a return value.",
                "It converts recursion into a loop automatically.",
            ],
            "answer": "It stops recursive calls from continuing indefinitely.",
        },
        {
            "id": "u8",
            "question": "Which OOP concept means bundling data and related methods inside a class?",
            "options": ["Encapsulation", "Inheritance", "Compilation", "Iteration"],
            "answer": "Encapsulation",
        },
        {
            "id": "u9",
            "question": "What does a variable normally represent in a program?",
            "options": [
                "A named storage location for a value",
                "Only a printed message",
                "A compiler error",
                "A network connection",
            ],
            "answer": "A named storage location for a value",
        },
        {
            "id": "u10",
            "question": "Which SQL command is commonly used to retrieve rows from a table?",
            "options": ["SELECT", "INSERT", "DELETE", "UPDATE"],
            "answer": "SELECT",
        },
    ]

    rules = DAILY_LANGUAGE_RULES[language]

    language_questions = [
        {
            "id": "l1",
            "question": f"In {language}, which choice is associated with defining a function or method?",
            "options": [
                rules["function"],
                "loop",
                "package",
                "return",
            ],
            "answer": rules["function"],
        },
        {
            "id": "l2",
            "question": f"In {language}, which choice is commonly used to display output?",
            "options": [
                rules["output"],
                "input()",
                "sizeof",
                "break",
            ],
            "answer": rules["output"],
        },
        {
            "id": "l3",
            "question": f"In {language}, which marker starts a common single-line comment?",
            "options": [
                rules["comment"],
                "=>",
                "::",
                "&&",
            ],
            "answer": rules["comment"],
        },
        {
            "id": "l4",
            "question": f"Which statement about program execution in {language} is accurate?",
            "options": [
                rules["entry"],
                "Every program must execute SQL before any other statement.",
                "Every program must begin with a for loop.",
                "Every program must create a class before any statement can run.",
            ],
            "answer": rules["entry"],
        },
        {
            "id": "l5",
            "question": f"Which topic is directly relevant when learning {language}?",
            "options": [
                rng.choice(COURSE_TOPICS.get(language, ["Variables"])),
                "Only image editing",
                "Only video compression",
                "Only spreadsheet formatting",
            ],
            "answer": None,
        },
    ]

    # The topic question's answer is the first option.
    language_questions[-1]["answer"] = language_questions[-1]["options"][0]

    # Rotate universal and language-specific templates by day so the
    # composition changes from day to day.
    rng.shuffle(questions)
    rng.shuffle(language_questions)

    selected = (questions[:5] + language_questions[:5])

    # Deterministically shuffle option order, preserving the answer text.
    final = []
    for index, q in enumerate(selected, start=1):
        opts = _daily_shuffle(q["options"], seed + index * 97)
        final.append({
            "id": q["id"],
            "question": q["question"],
            "options": opts,
            "answer": q["answer"],
        })

    return final

@app.route("/daily-test")
def daily_test():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    conn = get_db()

    try:
        user = conn.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        language = "Python"
        today = date.today().isoformat()

        attempt = conn.execute(
            """
            SELECT score, total
            FROM daily_test_attempts
            WHERE username = ? AND test_date = ? AND language = ?
            """,
            (user["email"], today, language)
        ).fetchone()

    finally:
        conn.close()

    if attempt:
        return jsonify({
            "success": True,
            "completed": True,
            "date": today,
            "language": language,
            "score": attempt["score"],
            "total": attempt["total"]
        })

    questions = generate_daily_questions(language, today)

    return jsonify({
        "success": True,
        "completed": False,
        "date": today,
        "language": language,
        "questions": [
            {
                "id": q["id"],
                "question": q["question"],
                "options": q["options"]
            }
            for q in questions
        ]
    })

@app.route("/daily-test-submit", methods=["POST"])
def daily_test_submit():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    data = request.get_json(silent=True) or {}

    answers = data.get("answers", {})

    if not isinstance(answers, dict):
        answers = {}

    conn = get_db()

    user = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    language = "Python"
    today = date.today().isoformat()

    existing = conn.execute(
        """
        SELECT score, total
        FROM daily_test_attempts
        WHERE username = ? AND test_date = ? AND language = ?
        """,
        (user["email"], today, language)
    ).fetchone()

    if existing:
        conn.close()

        return jsonify({
            "success": True,
            "already_completed": True,
            "score": existing["score"],
            "total": existing["total"],
            "message": "Today's Daily Test is already completed."
        })

    questions = generate_daily_questions(language, today)

    score = 0

    for q in questions:

        if str(answers.get(q["id"], "")) == str(q["answer"]):
            score += 1

    total = len(questions)

    conn.execute(
        """
        INSERT INTO daily_test_attempts
        (username, test_date, language, score, total)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user["email"],
            today,
            language,
            score,
            total
        )
    )

    reward = 3 if score >= 8 else (2 if score >= 5 else 1)

    conn.execute(
        """
        UPDATE users
        SET progress = MIN(100, progress + ?)
        WHERE id = ?
        """,
        (
            reward,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    percent = round((score / total) * 100) if total else 0

    if percent >= 80:
        message = "Excellent! Keep your daily streak going."
    elif percent >= 60:
        message = "Good job! Review the weak topics and come back tomorrow."
    else:
        message = "Keep practicing. Tomorrow you will get a fresh test."

    return jsonify({
        "success": True,
        "already_completed": False,
        "score": score,
        "total": total,
        "percent": percent,
        "message": message
    })


@app.route("/daily-test-history")
def daily_test_history():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    conn = get_db()

    user = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if not user:
        conn.close()

        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    rows = conn.execute(
        """
        SELECT test_date, language, score, total
        FROM daily_test_attempts
        WHERE username = ?
        ORDER BY test_date DESC
        LIMIT 30
        """,
        (user["email"],)
    ).fetchall()

    conn.close()

    return jsonify({
        "success": True,
        "history": [
            {
                "date": row["test_date"],
                "language": row["language"],
                "score": row["score"],
                "total": row["total"]
            }
            for row in rows
        ]
    })

# =========================================================
# QUIZ
# =========================================================

@app.route("/quiz")
def quiz():

    language = request.args.get(
        "language",
        "Python"
    )


    questions = QUIZZES.get(
        language,
        QUIZZES["Python"]
    )


    clean_questions = []


    for q in questions:

        clean_questions.append({

            "id": q["id"],

            "question":
                q["question"],

            "options":
                q["options"]

        })


    return jsonify({

        "success": True,

        "questions":
            clean_questions

    })


# =========================================================
# QUIZ ANSWER
# =========================================================

@app.route(
    "/quiz-answer",
    methods=["POST"]
)
def quiz_answer():

    if "username" not in session:

        return jsonify({
            "success": False,
            "message":
                "Please login first."
        })


    data = request.get_json(
        silent=True
    ) or {}


    question_id = data.get("id")

    answer = data.get("answer")


    language = "Python"


    conn = get_db()


    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (session["username"],)
    ).fetchone()


    if user:

        language = user["language"]


    questions = QUIZZES.get(
        language,
        QUIZZES["Python"]
    )


    correct = False


    for q in questions:

        if q["id"] == question_id:

            if q["answer"] == answer:

                correct = True

            break


    if correct:

        new_score = user["quiz_score"] + 1

        new_progress = min(
            100,
            user["progress"] + 5
        )


        conn.execute(
            """
            UPDATE users
            SET quiz_score = ?,
                progress = ?
            WHERE username = ?
            """,
            (
                new_score,
                new_progress,
                session["username"]
            )
        )


        conn.commit()

        conn.close()


        return jsonify({

            "success": True,

            "message":
                "✅ Correct answer!"

        })


    conn.close()


    return jsonify({

        "success": True,

        "message":
            "❌ Try again. Check the concept."

    })


# =========================================================
# PROGRESS
# =========================================================

@app.route("/progress")
def progress():

    if "username" not in session:

        return jsonify({
            "success": False,
            "message":
                "Please login first."
        })


    conn = get_db()


    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (session["username"],)
    ).fetchone()


    conn.close()


    if not user:

        return jsonify({
            "success": False
        })


    return jsonify({

        "success": True,

        "progress":
            user["progress"],

        "quiz_score":
            user["quiz_score"],

        "language":
            user["language"]

    })


# =========================================================
# CHATBOT
# =========================================================



@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()
    language = str(data.get("language", "Python")).strip()

    if not message:
        return jsonify({
            "success": False,
            "reply": "Please type a question."
        })

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return jsonify({
            "success": False,
            "reply": "Gemini API key is not configured."
        })

    system_prompt = f"""
You are an AI Coding Mentor.

Programming language: {language}

Answer the student's exact question.
Use simple English.

For programming questions:
- Give a clear definition.
- Explain briefly.
- Give a simple example when useful.
- If code is provided, identify errors and give corrected code.
- Do not confuse programming languages.

Keep answers concise but complete.
"""

    try:
        response = requests.post(
         "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "system_instruction": {
                    "parts": [
                        {"text": system_prompt}
                    ]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": message}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 500
                }
            },
            timeout=60
        )

        if response.status_code != 200:
            print("Gemini API status:", response.status_code)
            print("Gemini API error:", response.text[:2000])

            return jsonify({
                "success": False,
                "reply": "Gemini AI could not respond. Please check the server logs."
            })

        result = response.json()

        parts = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )

        reply = "\n".join(
            part.get("text", "")
            for part in parts
            if part.get("text")
        ).strip()

        if not reply:
            reply = "Sorry, I could not generate an answer. Please try again."

        return jsonify({
            "success": True,
            "reply": reply
        })

    except requests.exceptions.Timeout:
        print("Gemini API timeout")

        return jsonify({
            "success": False,
            "reply": "AI Mentor is taking too long. Please try again."
        })

    except requests.exceptions.RequestException as e:
        print("Gemini connection error:", repr(e))

        return jsonify({
            "success": False,
            "reply": "Unable to connect to Gemini AI. Please try again."
        })

    except Exception as e:
        print("Gemini chat error:", repr(e))

        return jsonify({
            "success": False,
            "reply": "AI Mentor could not process this question."
        })


# =========================================================
# LOGOUT
# =========================================================

@app.route(
    "/logout",
    methods=["POST"]
)
def logout():

    session.clear()


    return jsonify({

        "success": True

    })


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    init_db()

    print()
    print("=" * 60)
    print("       AI CODING MENTOR")
    print("=" * 60)
    print()
    print("Server running...")
    print()
    print("Open this in your browser:")
    print("http://127.0.0.1:5000")
    print()
    print("=" * 60)


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )