/* =====================================================
   AI CODING MENTOR - MAIN JAVASCRIPT
   Corrected version
   ===================================================== */

console.log("AI Coding Mentor JS loaded");

window.loginMode = true;
window.selectedLanguage = "Python";
window.currentTopics = [];
window.currentQuiz = [];
window.currentQuizIndex = 0;
window.currentQuizScore = 0;
window.currentQuizAnswered = false;

/* =====================================================
   PAGE CONTROL
   ===================================================== */

window.hideAll = function () {
    const pageIds = [
        "welcomePage", "authPage", "dashboard", "languagePage",
        "editorPage", "quizPage", "dailyTestPage", "chatPage",
        "progressPage", "coursePage", "lessonPage", "profilePage",
        "practicePage", "analysisPage", "aiAnalysisPage"
    ];

    pageIds.forEach(function (id) {
        const element = document.getElementById(id);
        if (element) element.classList.add("hidden");
    });
};

window.showPage = function (id) {
    window.hideAll();

    const page = document.getElementById(id);

    if (!page) {
        console.error("Page ID not found:", id);
        alert("Page not found: " + id);
        return false;
    }

    page.classList.remove("hidden");

    if (id === "profilePage") {
        window.loadProfileData();
    }

    if (id === "chatPage") {
        const input = document.getElementById("chatInput");
        if (input) input.focus();
    }

    return true;
};

window.backDashboard = function () {
    window.showPage("dashboard");
};

window.showLanguages = function () {
    window.showPage("languagePage");
};

/* =====================================================
   LOGIN / SIGNUP MODE
   ===================================================== */

window.renderAuthMode = function () {
    const isSignup = window.loginMode === false;

    const nameWrapper = document.getElementById("authNameWrapper");
    const nameInput = document.getElementById("authName");

    const confirmWrapper =
        document.getElementById("confirmPasswordWrapper");

    const confirmInput =
        document.getElementById("authConfirmPassword");

    const title = document.getElementById("authTitle");
    const description = document.getElementById("authDescription");
    const button = document.getElementById("authButton");
    const switchText = document.getElementById("switchText");
    const switchButton = document.getElementById("authSwitch");

    if (nameWrapper) {
        nameWrapper.classList.toggle("hidden", !isSignup);
        nameWrapper.style.display = isSignup ? "block" : "none";
    }

    if (nameInput) {
        nameInput.required = isSignup;
        nameInput.disabled = !isSignup;

        if (!isSignup) nameInput.value = "";
    }

    if (confirmWrapper) {
        confirmWrapper.classList.toggle("hidden", !isSignup);
        confirmWrapper.style.display = isSignup ? "block" : "none";
    }

    if (confirmInput) {
        confirmInput.required = isSignup;
        confirmInput.disabled = !isSignup;

        if (!isSignup) confirmInput.value = "";
    }

    if (title) {
        title.textContent = isSignup
            ? "Create Account 🚀"
            : "Welcome Back 👋";
    }

    if (description) {
        description.textContent = isSignup
            ? "Create your student account."
            : "Login to continue learning.";
    }

    if (button) {
        button.textContent = isSignup
            ? "Create Account"
            : "Login";
    }

    if (switchText) {
        switchText.textContent = isSignup
            ? "Already have an account?"
            : "Don't have an account?";
    }

    if (switchButton) {
        switchButton.textContent = isSignup ? "Login" : "Sign Up";
    }

    console.log("SIGNUP MODE:", isSignup);
};

window.toggleAuth = function () {
    window.loginMode = !window.loginMode;
    window.renderAuthMode();
};

/* =====================================================
   LOGIN / SIGNUP SUBMISSION
   ===================================================== */

window.submitAuth = async function () {
    const nameField = document.getElementById("authName");
    const emailField = document.getElementById("authEmail");
    const passwordField = document.getElementById("authPassword");
    const confirmField =
        document.getElementById("authConfirmPassword");

    const button = document.getElementById("authButton");

    const buttonLabel = button
        ? button.textContent.trim().toLowerCase()
        : "";

    const isSignup =
        window.loginMode === false ||
        buttonLabel.includes("create account");

    window.loginMode = !isSignup;

    const name = nameField
        ? String(nameField.value || "").trim()
        : "";

    const email = emailField
        ? String(emailField.value || "").trim()
        : "";

    const password = passwordField
        ? String(passwordField.value || "")
        : "";

    const confirmPassword = confirmField
        ? String(confirmField.value || "")
        : "";

    if (isSignup) {
        if (!name) {
            alert("Please enter your name.");
            nameField?.focus();
            return;
        }

        if (!email) {
            alert("Please enter your email.");
            emailField?.focus();
            return;
        }

        if (!password) {
            alert("Please enter your password.");
            passwordField?.focus();
            return;
        }

        if (!confirmPassword) {
            alert("Please confirm your password.");
            confirmField?.focus();
            return;
        }

        if (password !== confirmPassword) {
            alert("Passwords do not match.");
            confirmField?.focus();
            return;
        }
    } else {
        if (!email || !password) {
            alert("Please enter your email and password.");
            if (!email) emailField?.focus();
            else passwordField?.focus();
            return;
        }
    }

    if (button) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = isSignup
            ? "Creating Account..."
            : "Logging in...";
    }

    try {
        const requestBody = { email, password };

        if (isSignup) {
            requestBody.name = name;
            requestBody.confirm_password = confirmPassword;
        }

        const response = await fetch(
            isSignup ? "/signup" : "/login",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify(requestBody)
            }
        );

        const data = await response.json();

        if (!response.ok || data.success !== true) {
            alert(data.message || (
                isSignup ? "Signup failed." : "Login failed."
            ));
            return;
        }

        if (isSignup) {
            alert("Account created successfully! Please login.");

            window.loginMode = true;

            if (nameField) nameField.value = "";
            if (passwordField) passwordField.value = "";
            if (confirmField) confirmField.value = "";

            window.renderAuthMode();
            return;
        }

        const savedName = String(
            data.name || data.user_name ||
            data.user?.name || "Student"
        ).trim();

        const savedEmail = String(
            data.email || data.user_email ||
            data.user?.email || email
        ).trim();

        sessionStorage.setItem("userName", savedName);
        sessionStorage.setItem("userEmail", savedEmail);

        [
            "userDisplay",
            "dashboardName",
            "profileName",
            "profileTopName",
            "profileUserName"
        ].forEach(function (id) {
            const element = document.getElementById(id);
            if (element) element.textContent = savedName;
        });

        const profileEmail =
            document.getElementById("profileEmail");

        if (profileEmail) {
            profileEmail.textContent = savedEmail;
        }

        window.showPage("dashboard");

    } catch (error) {
        console.error("Login/Signup error:", error);
        alert("Login/Signup error: " + error.message);

    } finally {
        if (button) {
            button.disabled = false;

            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
                delete button.dataset.originalText;
            }

            window.renderAuthMode();
        }
    }
};

window.loginUser = window.submitAuth;

/* =====================================================
   PROFILE DATA
   ===================================================== */

window.loadProfileData = async function () {
    let userName =
        sessionStorage.getItem("userName") || "Student";

    let userEmail =
        sessionStorage.getItem("userEmail") ||
        "Email not available";

    try {
        const response = await fetch("/profile-data", {
            credentials: "same-origin"
        });

        if (response.ok) {
            const data = await response.json();

            if (data.success) {
                userName = data.name || data.user_name || userName;
                userEmail = data.email || data.user_email || userEmail;

                sessionStorage.setItem("userName", userName);
                sessionStorage.setItem("userEmail", userEmail);
            }
        }
    } catch (error) {
        console.warn("Unable to refresh profile data:", error);
    }

    const fields = {
        profileUserName: userName,
        profileName: userName,
        profileTopName: userName,
        profileEmail: userEmail
    };

    Object.entries(fields).forEach(function ([id, value]) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    });
};
/* =====================================================
   AI CODING MENTOR
   PART 2: COURSE + CHAPTER CARDS + LESSONS
   ===================================================== */

window.currentLessonIndex = 0;
window.currentChapterQuiz = [];

/* =====================================================
   OPEN COURSE
   ===================================================== */

console.log("UPDATED CHAPTER CARD CODE LOADED");
window.openCourse = async function (language) {
    window.selectedLanguage =
        language || window.selectedLanguage || "Python";

    const container = document.getElementById("courseTopics");
    const title = document.getElementById("courseTitle");

    if (!container) {
        console.error("Course chapter container not found.");
        alert("Course chapter container not found in HTML.");
        return;
    }

    container.replaceChildren();

    // Display loading message
    const loading = document.createElement("p");
    loading.textContent = "Loading chapters...";
    container.appendChild(loading);

    try {
        const response = await fetch(
            "/course-data?language=" +
                encodeURIComponent(window.selectedLanguage),
            { credentials: "same-origin" }
        );

        const data = await response.json();

        if (!response.ok || data.success === false) {
            throw new Error(
                data.message || "Unable to load course."
            );
        }

        window.currentTopics = Array.isArray(data.topics)
            ? data.topics
            : [];

        if (title) {
            title.textContent =
                window.selectedLanguage + " Course";
        }

        // Set chapter grid layout
        container.replaceChildren();

        container.style.display = "grid";
        container.style.gridTemplateColumns =
            "repeat(auto-fit, minmax(250px, 1fr))";
        container.style.gap = "20px";
        container.style.marginTop = "25px";
        container.style.alignItems = "stretch";

        if (window.currentTopics.length === 0) {
            const emptyMessage = document.createElement("p");
            emptyMessage.textContent =
                "No chapters available for this language.";

            container.appendChild(emptyMessage);
            window.showPage("coursePage");
            return;
        }

        window.currentTopics.forEach(function (topic, index) {
            const card = document.createElement("div");

            card.className = "glass chapter-card";
            card.tabIndex = 0;
            card.setAttribute("role", "button");
            card.setAttribute(
                "aria-label",
                "Start learning chapter " + (index + 1)
            );

            card.style.cssText = `
                box-sizing: border-box;
                min-width: 0;
                min-height: 230px;
                padding: 22px;
                border-radius: 16px;
                cursor: pointer;
                display: flex;
                flex-direction: column;
                gap: 12px;
                transition: transform .2s ease, box-shadow .2s ease;
            `;

            // Chapter number
            const chapterNumber = document.createElement("p");

            chapterNumber.textContent =
                "CHAPTER " + String(index + 1).padStart(2, "0");

            chapterNumber.style.cssText = `
                color: #8db8ff;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1px;
                margin: 0;
            `;

            // Support different title field names
            const heading = document.createElement("h3");

            heading.textContent =
                topic.title ||
                topic.name ||
                topic.topic ||
                topic.chapter_title ||
                topic.lesson_title ||
                "Chapter " + (index + 1);

            heading.style.cssText = `
                font-size: 19px;
                line-height: 1.4;
                margin: 0;
                overflow-wrap: anywhere;
            `;

            // Chapter description
            const description = document.createElement("p");

            let descriptionText =
                topic.definition ||
                topic.description ||
                topic.content ||
                "Learn this topic step by step.";

            // Keep long chapter content from filling the entire card
            descriptionText = String(descriptionText);

            if (descriptionText.length > 150) {
                descriptionText =
                    descriptionText.slice(0, 147).trimEnd() + "...";
            }

            description.textContent = descriptionText;

            description.style.cssText = `
                color: #aebbd0;
                line-height: 1.7;
                font-size: 14px;
                margin: 0;
                flex-grow: 1;
                overflow-wrap: anywhere;
            `;

            // Start learning footer
            const footer = document.createElement("p");

            footer.textContent = "Start Learning →";

            footer.style.cssText = `
                color: #8db8ff;
                font-weight: 700;
                font-size: 14px;
                margin: 8px 0 0;
            `;

const actions = document.createElement("div");

actions.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 12px;
`;

const lessonButton = document.createElement("button");
lessonButton.className = "btn";
lessonButton.textContent = "Start Learning";

lessonButton.addEventListener("click", function(event) {
    event.stopPropagation();
    window.openLesson(index);
});

const quizButton = document.createElement("button");
quizButton.className = "btn";
quizButton.textContent = "Chapter Quiz / 10 Questions";

quizButton.addEventListener("click", function(event) {
    event.stopPropagation();
    window.openChapterQuiz(topic.id);
});

actions.append(lessonButton, quizButton);

card.append(
    chapterNumber,
    heading,
    description,
    actions
);

            card.addEventListener("mouseenter", function () {
                card.style.transform = "translateY(-4px)";
            });

            card.addEventListener("mouseleave", function () {
                card.style.transform = "translateY(0)";
            });

            function openThisLesson() {
                if (typeof window.openLesson === "function") {
                    window.openLesson(index);
                } else {
                    console.error("window.openLesson() not found.");
                }
            }

            card.addEventListener("click", openThisLesson);

            card.addEventListener("keydown", function (event) {
                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {
                    event.preventDefault();
                    openThisLesson();
                }
            });

            container.appendChild(card);
        });

        // Show the course page after rendering all cards
        window.showPage("coursePage");

        console.log(
            "Course loaded:",
            window.selectedLanguage,
            "| Topics:",
            window.currentTopics.length,
            "| Cards:",
            container.querySelectorAll(".chapter-card").length
        );

    } catch (error) {
        console.error("Course loading error:", error);

        container.replaceChildren();

        const message = document.createElement("p");
        message.textContent =
            "Unable to load chapters: " + error.message;

        container.appendChild(message);
    }
};


/* =====================================================
   OPEN BOOK-STYLE LESSON
   ===================================================== */


window.openLesson = function (index) {
    const topics = window.currentTopics || [];
    index = Number(index);

    if (!Number.isInteger(index) || index < 0 || index >= topics.length) {
        alert("Chapter not found. Please open the course again.");
        return;
    }

    const topic = topics[index] || {};
    window.currentLessonIndex = index;

function setText(id, value, fallback) {
    const el = document.getElementById(id);
    if (!el) return;

    const text =
        value !== undefined &&
        value !== null &&
        String(value).trim() !== ""
            ? String(value)
            : fallback;

    const importantWords = [
        "Python",
        "programming language",
        "high-level",
        "Guido van Rossum",
        "Artificial Intelligence",
        "Machine Learning",
        "Data Science",
        "Web development",
        "Automation",
        "syntax",
        "indentation",
        "variable",
        "function",
        "loop",
        "condition"
    ];

    const pattern = new RegExp(
        "(" + importantWords
            .sort((a, b) => b.length - a.length)
            .map(word => word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
            .join("|") + ")",
        "gi"
    );

    el.replaceChildren();

    String(text).split(pattern).forEach(part => {
        if (importantWords.some(
            word => word.toLowerCase() === part.toLowerCase()
        )) {
            const strong = document.createElement("strong");
            strong.textContent = part;
            el.appendChild(strong);
        } else {
            el.appendChild(document.createTextNode(part));
        }
    });
}

    function toArray(value) {
        if (Array.isArray(value)) return value;

        if (typeof value === "string" && value.trim()) {
            return value
                .split(/\n|\r|•/)
                .map(item => item.replace(/^\s*[-*\d.)]+\s*/, "").trim())
                .filter(Boolean);
        }

        return [];
    }

    const title = topic.title || "Chapter " + (index + 1);

    setText("bookLessonTitle", title, title);
    setText("bookLessonSubtitle", topic.subtitle || topic.summary,
        "Learn this topic step by step.");
    setText("bookChapterNumber",
        "CHAPTER " + String(index + 1).padStart(2, "0"),
        "");
    setText("lessonProgressText",
        "Chapter " + (index + 1) + " of " + topics.length, "");
    setText("bookDefinition", topic.definition || topic.description,
        "Definition of " + title + " will be added.");
    setText("bookExplanation",
        topic.explanation || topic.content || topic.details,
        "Detailed explanation of " + title + " will be added.");
    setText("bookSyntax", topic.syntax || topic.usage,
        "Syntax for " + title + " will be added.");
    setText("bookExample",
        topic.example || topic.example_code || topic.code || topic.program,
        "Example program for " + title + " will be added.");
    setText("bookOutput", topic.output || topic.expected_output,
        "Example output will be added.");
    setText("sideQuizChapter", "Chapter " + (index + 1), "");

    const pointsElement = document.getElementById("bookKeyPoints");
    if (pointsElement) {
        pointsElement.replaceChildren();

        const points = toArray(
            topic.key_points || topic.keyPoints || topic.features || topic.points
        );

        (points.length ? points : [
            "Understand " + title + ".",
            "Learn its syntax and purpose.",
            "Study the example program.",
            "Practise the concept."
        ]).forEach(point => {
            const li = document.createElement("li");
            li.textContent = point;
            pointsElement.appendChild(li);
        });
    }

    const practiceElement = document.getElementById("bookPractice");
    if (practiceElement) {
        practiceElement.replaceChildren();

        const practice = toArray(topic.practice || topic.exercises || topic.tasks);

        (practice.length ? practice : [
            "Write a program using " + title + ".",
            "Change the example values and check the output.",
            "Explain the program in your own words."
        ]).forEach(item => {
            const li = document.createElement("li");
            li.textContent = item;
            practiceElement.appendChild(li);
        });
    }

    const previousButton = document.getElementById("previousChapterBtn");
    const nextButton = document.getElementById("nextChapterBtn");

    if (previousButton) {
        previousButton.disabled = index === 0;
        previousButton.onclick = () => window.openLesson(index - 1);
    }

    if (nextButton) {
        nextButton.disabled = index === topics.length - 1;
        nextButton.onclick = () => window.openLesson(index + 1);
    }

    const quizButton = document.getElementById("sideStartQuizBtn");

    if (quizButton) {
        quizButton.onclick = function () {
            const chapterId = Number(topic.id ?? index + 1);

            if (typeof window.openChapterQuiz === "function") {
                window.openChapterQuiz(chapterId);
            } else if (typeof window.openQuiz === "function") {
                window.openQuiz(chapterId);
            } else {
                alert("Quiz function is not connected yet. The quiz handler must be added.");
            }
        };
    }

    if (typeof window.showPage === "function") {
        window.showPage("lessonPage");
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
};


/* =====================================================
   PREVIOUS / NEXT CHAPTER
   ===================================================== */

window.moveBookChapter = function (direction) {
    const nextIndex =
        window.currentLessonIndex + Number(direction);

    if (
        nextIndex >= 0 &&
        nextIndex < (window.currentTopics || []).length
    ) {
        window.openLesson(nextIndex);
    }
};

window.previousChapter = function () {
    window.moveBookChapter(-1);
};

window.nextChapter = function () {
    window.moveBookChapter(1);
};


/* =====================================================
   CHAPTER QUIZ
   ===================================================== */

window.startSideChapterQuiz = async function () {
    const topic =
        (window.currentTopics || [])[
            window.currentLessonIndex
        ];

    if (!topic) {
        alert("Please open a chapter first.");
        return;
    }

    window.currentQuizIndex = 0;
    window.currentQuizScore = 0;
    window.currentQuizAnswered = false;

    try {
        let questions =
            topic.quiz ||
            topic.questions ||
            topic.quiz_questions ||
            [];

        if (!Array.isArray(questions) || !questions.length) {
            const response = await fetch(
                "/quiz?language=" +
                encodeURIComponent(window.selectedLanguage),
                { credentials: "same-origin" }
            );

            const data = await response.json();

            if (!response.ok || data.success === false) {
                throw new Error(
                    data.message || "Unable to load quiz."
                );
            }

            const allQuestions =
                data.questions ||
                data.quiz ||
                data.data ||
                [];

            if (!Array.isArray(allQuestions) ||
                !allQuestions.length) {
                throw new Error("No quiz questions available.");
            }

            const chapterIndex = window.currentLessonIndex;

            const chapterQuestions = allQuestions.filter(
                function (question) {
                    const number =
                        question.chapter_index ??
                        question.chapterIndex ??
                        question.chapter_number ??
                        question.chapter;

                    return number != null && (
                        String(number) === String(chapterIndex) ||
                        String(number) === String(chapterIndex + 1) ||
                        String(number) === String(topic.id)
                    );
                }
            );

            questions = chapterQuestions.length
                ? chapterQuestions
                : allQuestions;
        }

        window.currentQuiz = questions.slice(0, 10);

        window.showPage("quizPage");

        const scoreElement =
            document.getElementById("quizScore");

        if (scoreElement) {
            scoreElement.textContent = "0";
        }

        window.renderQuizQuestion();

    } catch (error) {
        console.error("Chapter quiz error:", error);

        alert(
            "Unable to start chapter quiz: " + error.message
        );
    }
};


/* =====================================================
   COURSE PAGE BACK BUTTON
   ===================================================== */

window.backToCourse = function () {
    window.showPage("coursePage");
};


/* =====================================================
   CONNECT BUTTONS
   ===================================================== */

document.addEventListener("DOMContentLoaded", function () {
    const previousButton =
        document.getElementById("previousChapterBtn");

    const nextButton =
        document.getElementById("nextChapterBtn");

    const quizButton =
        document.getElementById("sideStartQuizBtn");

    if (previousButton) {
        previousButton.onclick = window.previousChapter;
    }

    if (nextButton) {
        nextButton.onclick = window.nextChapter;
    }

    if (quizButton) {
        quizButton.onclick = window.startSideChapterQuiz;
    }

    if (typeof window.renderAuthMode === "function") {
        window.renderAuthMode();
    }
});
// ============================================
// PART 3: CODE EDITOR, RUN CODE & AI ANALYSIS
// ============================================

window.getElement = function (id) {
    return document.getElementById(id);
};

window.getEditorCode = function () {
    const editor = window.getElement("codeEditor");

    if (!editor) {
        return "";
    }

    return editor.value || editor.innerText || "";
};

window.getSelectedLanguage = function () {
    return window.selectedLanguage || "Python";
};


// ============================================
// RUN CODE
// Backend endpoint: /run-code
// ============================================

window.runCode = async function () {
    const editor = window.getElement("codeEditor");

    if (!editor) {
        alert("Code editor not found. Please check the HTML id.");
        return;
    }

    const code = window.getEditorCode();
    const language = window.getSelectedLanguage();

    const outputBox =
        window.getElement("codeOutput") ||
        window.getElement("outputBox") ||
        window.getElement("runOutput");

    const runButton =
        window.getElement("runCodeBtn") ||
        window.getElement("runButton");

    if (!code.trim()) {
        if (outputBox) {
            outputBox.textContent = "Please enter your code first.";
        } else {
            alert("Please enter your code first.");
        }
        return;
    }

    if (outputBox) {
        outputBox.textContent = "Running your code...";
    }

    if (runButton) {
        runButton.disabled = true;
        runButton.textContent = "Running...";
    }

    try {
        const response = await fetch("/run-code", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                code: code,
                language: language
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                data.message ||
                "Unable to run the code."
            );
        }

        const output =
            data.output ??
            data.result ??
            data.stdout ??
            data.error ??
            data.message ??
            "Code executed successfully.";

        if (outputBox) {
            outputBox.textContent = String(output);
        }

    } catch (error) {
        console.error("Run Code Error:", error);

        if (outputBox) {
            outputBox.textContent =
                "Error: " + (error.message || "Unable to run code.");
        } else {
            alert(error.message || "Unable to run code.");
        }
    } finally {
        if (runButton) {
            runButton.disabled = false;
            runButton.textContent = "Run Code";
        }
    }
};


// Support existing HTML onclick names
window.executeCode = window.runCode;
window.runProgram = window.runCode;


// ============================================
// AI CODE ANALYSIS
// Backend endpoint: /analyze
// ============================================

window.analyzeCode = async function () {
    const code = window.getEditorCode();
    const language = window.getSelectedLanguage();

    const resultBox =
        window.getElement("analysisResult") ||
        window.getElement("aiAnalysisResult") ||
        window.getElement("analysisOutput");

    const analyzeButton =
        window.getElement("analyzeCodeBtn") ||
        window.getElement("analyzeButton");

    if (!code.trim()) {
        if (resultBox) {
            resultBox.textContent =
                "Please enter some code before asking AI to analyze it.";
        } else {
            alert("Please enter some code first.");
        }
        return;
    }

    if (resultBox) {
        resultBox.textContent = "AI is analyzing your code...";
    }

    if (analyzeButton) {
        analyzeButton.disabled = true;
        analyzeButton.textContent = "Analyzing...";
    }

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                code: code,
                language: language
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                data.message ||
                "AI analysis failed."
            );
        }

        const analysis =
            data.analysis ??
            data.explanation ??
            data.result ??
            data.message ??
            data.feedback ??
            "Analysis completed, but no explanation was returned.";

        if (resultBox) {
            // textContent keeps the returned text safe to display.
            resultBox.textContent = String(analysis);
        }

    } catch (error) {
        console.error("AI Analysis Error:", error);

        if (resultBox) {
            resultBox.textContent =
                "Unable to analyze your code: " +
                (error.message || "Please try again.");
        } else {
            alert(error.message || "AI analysis failed.");
        }
    } finally {
        if (analyzeButton) {
            analyzeButton.disabled = false;
            analyzeButton.textContent = "Analyze Code";
        }
    }
};


// ============================================
// CLEAR CODE EDITOR
// ============================================

window.clearCode = function () {
    const editor = window.getElement("codeEditor");

    if (editor) {
        editor.value = "";
        editor.focus();
    }

    const outputBox =
        window.getElement("codeOutput") ||
        window.getElement("outputBox") ||
        window.getElement("runOutput");

    if (outputBox) {
        outputBox.textContent = "";
    }

    const resultBox =
        window.getElement("analysisResult") ||
        window.getElement("aiAnalysisResult") ||
        window.getElement("analysisOutput");

    if (resultBox) {
        resultBox.textContent = "";
    }
};


// ============================================
// GENERAL QUIZ
// Backend endpoint: /quiz?language=Python
// ============================================

window.generalQuizQuestions = [];
window.generalQuizIndex = 0;
window.generalQuizScore = 0;
window.generalQuizAnswered = false;


window.loadQuiz = async function () {
    const questionBox =
        window.getElement("quizQuestion") ||
        window.getElement("questionText");

    const optionsBox =
        window.getElement("quizOptions") ||
        window.getElement("optionsContainer");

    if (questionBox) {
        questionBox.textContent = "Loading quiz questions...";
    }

    if (optionsBox) {
        optionsBox.replaceChildren();
    }

    try {
        const language = encodeURIComponent(
            window.getSelectedLanguage()
        );

        const response = await fetch(
            "/quiz?language=" + language
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || data.message || "Could not load quiz."
            );
        }

        let questions = [];

        if (Array.isArray(data)) {
            questions = data;
        } else if (Array.isArray(data.questions)) {
            questions = data.questions;
        } else if (Array.isArray(data.quiz)) {
            questions = data.quiz;
        } else if (Array.isArray(data.data)) {
            questions = data.data;
        }

        if (questions.length === 0) {
            if (questionBox) {
                questionBox.textContent =
                    "No quiz questions available for this language.";
            }
            return;
        }

        window.generalQuizQuestions = questions;
        window.generalQuizIndex = 0;
        window.generalQuizScore = 0;
        window.generalQuizAnswered = false;

        window.renderQuizQuestion();

    } catch (error) {
        console.error("Quiz Loading Error:", error);

        if (questionBox) {
            questionBox.textContent =
                "Unable to load quiz: " +
                (error.message || "Please try again.");
        }
    }
};


// ============================================
// DISPLAY ONE QUIZ QUESTION
// ============================================

window.renderQuizQuestion = function () {
    const questions = window.generalQuizQuestions;
    const index = window.generalQuizIndex;

    const questionBox =
        window.getElement("quizQuestion") ||
        window.getElement("questionText");

    const optionsBox =
        window.getElement("quizOptions") ||
        window.getElement("optionsContainer");

    const feedbackBox =
        window.getElement("quizFeedback");

    const scoreBox =
        window.getElement("quizScore");

    const nextButton =
        window.getElement("nextQuestionButton") ||
        window.getElement("nextQuizButton");

    if (!questionBox || !optionsBox) {
        console.error(
            "Quiz HTML elements missing. Check quizQuestion and quizOptions IDs."
        );
        return;
    }

    if (index >= questions.length) {
        questionBox.textContent =
            "Quiz completed! Your score: " +
            window.generalQuizScore +
            " / " +
            questions.length;

        optionsBox.replaceChildren();

        if (feedbackBox) {
            feedbackBox.textContent =
                "Great effort! You have completed the quiz.";
        }

        if (scoreBox) {
            scoreBox.textContent =
                "Score: " +
                window.generalQuizScore +
                " / " +
                questions.length;
        }

        if (nextButton) {
            nextButton.textContent = "Restart Quiz";
            nextButton.disabled = false;
        }

        window.generalQuizAnswered = true;
        return;
    }

    const item = questions[index];

    const questionText =
        item.question ??
        item.text ??
        item.question_text ??
        "Question " + (index + 1);

    questionBox.textContent =
        (index + 1) + ". " + questionText;

    optionsBox.replaceChildren();

    if (feedbackBox) {
        feedbackBox.textContent = "";
    }

    if (scoreBox) {
        scoreBox.textContent =
            "Score: " + window.generalQuizScore;
    }

    window.generalQuizAnswered = false;

    const rawOptions =
        item.options ??
        item.choices ??
        item.answers ??
        [];

    let options = rawOptions;

    if (typeof rawOptions === "string") {
        try {
            options = JSON.parse(rawOptions);
        } catch {
            options = rawOptions.split(",");
        }
    }

    if (!Array.isArray(options)) {
        options = Object.values(options || {});
    }

    if (options.length === 0) {
        const message = document.createElement("p");
        message.textContent =
            "Options are missing for this question.";
        optionsBox.appendChild(message);
    }

    options.forEach((option, optionIndex) => {
        const optionText =
            typeof option === "object" && option !== null
                ? String(
                    option.text ??
                    option.label ??
                    option.value ??
                    option.option ??
                    ""
                )
                : String(option);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "quiz-option";
        button.textContent = optionText;

        button.addEventListener("click", function () {
            window.checkQuizAnswer(
                option,
                optionText,
                button
            );
        });

        optionsBox.appendChild(button);
    });

    if (nextButton) {
        nextButton.textContent = "Next Question";
        nextButton.disabled = true;
    }
};


// ============================================
// CHECK QUIZ ANSWER
// ============================================

window.checkQuizAnswer = function (
    selectedOption,
    selectedText,
    selectedButton
) {
    if (window.generalQuizAnswered) {
        return;
    }

    const questions = window.generalQuizQuestions;
    const item = questions[window.generalQuizIndex];

    if (!item) {
        return;
    }

    window.generalQuizAnswered = true;

    const correctAnswer =
        item.answer ??
        item.correctAnswer ??
        item.correct_answer ??
        item.correct ??
        item.answer_text ??
        item.correct_option;

    const correctText =
        typeof correctAnswer === "object" && correctAnswer !== null
            ? String(
                correctAnswer.text ??
                correctAnswer.label ??
                correctAnswer.value ??
                correctAnswer.option ??
                ""
            )
            : String(correctAnswer ?? "");

    const chosenText = String(selectedText).trim();
    const expectedText = correctText.trim();

    const correctIndex =
        item.correct_index ??
        item.correctIndex ??
        item.answer_index;

    let isCorrect = false;

    if (
        correctIndex !== undefined &&
        correctIndex !== null &&
        correctIndex !== ""
    ) {
        isCorrect =
            Number(correctIndex) ===
            window.getSelectedOptionIndex(selectedButton);
    } else {
        isCorrect =
            chosenText.toLowerCase() ===
            expectedText.toLowerCase();
    }

    if (isCorrect) {
        window.generalQuizScore++;

        if (selectedButton) {
            selectedButton.style.borderColor = "#22c55e";
        }
    } else if (selectedButton) {
        selectedButton.style.borderColor = "#ef4444";
    }

    const feedbackBox =
        window.getElement("quizFeedback");

    if (feedbackBox) {
        feedbackBox.textContent = isCorrect
            ? "Correct! Well done."
            : "Incorrect. Correct answer: " +
              (expectedText || "Check the question answer data.");
    }

    const optionsBox =
        window.getElement("quizOptions") ||
        window.getElement("optionsContainer");

    if (optionsBox) {
        optionsBox.querySelectorAll("button").forEach(button => {
            button.disabled = true;
        });
    }

    const scoreBox =
        window.getElement("quizScore");

    if (scoreBox) {
        scoreBox.textContent =
            "Score: " + window.generalQuizScore;
    }

    const nextButton =
        window.getElement("nextQuestionButton") ||
        window.getElement("nextQuizButton");

    if (nextButton) {
        nextButton.disabled = false;
    }
};


// Get selected option position within the options container.
window.getSelectedOptionIndex = function (selectedButton) {
    if (!selectedButton || !selectedButton.parentElement) {
        return -1;
    }

    return Array.from(
        selectedButton.parentElement.children
    ).indexOf(selectedButton);
};


// ============================================
// NEXT QUESTION / RESTART QUIZ
// ============================================

window.nextQuizQuestion = function () {
    const questions = window.generalQuizQuestions;

    if (!questions.length) {
        window.loadQuiz();
        return;
    }

    if (window.generalQuizIndex >= questions.length - 1) {
        window.generalQuizIndex = questions.length;
    } else {
        window.generalQuizIndex++;
    }

    window.renderQuizQuestion();
};


// Support common HTML onclick names.
window.nextQuestion = window.nextQuizQuestion;
window.startQuiz = window.loadQuiz;
// ============================================
// PART 4: AI CHATBOT
// ============================================

window.sendChatMessage = async function () {
    const input =
        window.getElement("chatInput") ||
        window.getElement("chatMessageInput");

    const messages =
        window.getElement("chatMessages") ||
        window.getElement("chatHistory");

    if (!input || !messages) {
        console.error(
            "Chat elements missing. Check chatInput and chatMessages IDs."
        );
        return;
    }

    const message = input.value.trim();

    if (!message) {
        return;
    }

    // Display the user's message.
    const userMessage = document.createElement("div");
    userMessage.className = "chat-message user-message";
    userMessage.textContent = message;
    messages.appendChild(userMessage);

    input.value = "";

    const loadingMessage = document.createElement("div");
    loadingMessage.className = "chat-message bot-message";
    loadingMessage.textContent = "AI is thinking...";
    messages.appendChild(loadingMessage);

    messages.scrollTop = messages.scrollHeight;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                language: window.getSelectedLanguage()
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || data.message || "Chat request failed."
            );
        }

        loadingMessage.textContent =
            data.reply ??
            data.response ??
            data.answer ??
            data.message ??
            "AI did not return a response.";

    } catch (error) {
        console.error("Chat Error:", error);

        loadingMessage.textContent =
            "Unable to connect to AI. Please try again.";
    }

    messages.scrollTop = messages.scrollHeight;
};

window.sendMessage = window.sendChatMessage;


// Send a chat message when Enter is pressed.
document.addEventListener("DOMContentLoaded", function () {
    const input =
        window.getElement("chatInput") ||
        window.getElement("chatMessageInput");

    if (input && !input.dataset.chatEnterReady) {
        input.dataset.chatEnterReady = "true";

        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                window.sendChatMessage();
            }
        });
    }
});


// ============================================
// PART 4: LOAD PROGRESS
// ============================================

window.loadProgress = async function () {
    const progressBox =
        window.getElement("progressContent") ||
        window.getElement("progressContainer") ||
        window.getElement("progressPageContent");

    if (progressBox) {
        progressBox.textContent = "Loading your progress...";
    }

    try {
        const response = await fetch("/progress", {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || data.message ||
                "Unable to load progress."
            );
        }

        if (!progressBox) {
            console.log("Progress data:", data);
            return;
        }

        progressBox.replaceChildren();

        const heading = document.createElement("h3");
        heading.textContent = "Your Learning Progress";
        progressBox.appendChild(heading);

        const details = document.createElement("pre");
        details.style.whiteSpace = "pre-wrap";
        details.textContent = JSON.stringify(data, null, 2);
        progressBox.appendChild(details);

    } catch (error) {
        console.error("Progress Error:", error);

        if (progressBox) {
            progressBox.textContent =
                "Unable to load progress. Please try again.";
        }
    }
};


// ============================================
// PART 4: LOGOUT
// ============================================

window.logoutUser = async function () {
    const confirmed = window.confirm(
        "Are you sure you want to log out?"
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch("/logout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error("Logout request failed.");
        }

    } catch (error) {
        console.error("Logout Error:", error);

        alert(
            "Unable to log out from the server. Please try again."
        );
        return;
    }

    sessionStorage.removeItem("userName");
    sessionStorage.removeItem("userEmail");

    window.loginMode = true;

    if (typeof window.renderAuthMode === "function") {
        window.renderAuthMode();
    }

    if (typeof window.showPage === "function") {
        window.showPage("welcomePage");
    }

    window.location.reload();
};


// Common HTML onclick aliases.
window.logout = window.logoutUser;
// ============================================
// PART 5: DAILY TEST
// ============================================

window.dailyTestQuestions = [];
window.dailyTestIndex = 0;
window.dailyTestScore = 0;
window.dailyTestAnswered = false;


// Load daily test questions.
window.loadDailyTest = async function () {
    const questionBox =
        document.getElementById("dailyTestQuestion");

    const optionsBox =
        document.getElementById("dailyTestOptions");

    const feedbackBox =
        document.getElementById("dailyTestFeedback");

    if (questionBox) {
        questionBox.textContent = "Loading daily test...";
    }

    if (optionsBox) {
        optionsBox.replaceChildren();
    }

    if (feedbackBox) {
        feedbackBox.textContent = "";
    }

    try {
        const language = encodeURIComponent(
            window.selectedLanguage || "Python"
        );

        const response = await fetch(
            "/quiz?language=" + language
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Unable to load daily test."
            );
        }

        let questions = [];

        if (Array.isArray(data)) {
            questions = data;
        } else if (Array.isArray(data.questions)) {
            questions = data.questions;
        } else if (Array.isArray(data.quiz)) {
            questions = data.quiz;
        } else if (Array.isArray(data.data)) {
            questions = data.data;
        }

        if (!questions.length) {
            if (questionBox) {
                questionBox.textContent =
                    "Daily test questions are not available.";
            }
            return;
        }

        // Select up to 10 questions for the daily test.
        window.dailyTestQuestions = questions.slice(0, 10);
        window.dailyTestIndex = 0;
        window.dailyTestScore = 0;
        window.dailyTestAnswered = false;

        window.renderDailyTestQuestion();

    } catch (error) {
        console.error("Daily Test Error:", error);

        if (questionBox) {
            questionBox.textContent =
                "Unable to load the daily test. Please try again.";
        }
    }
};


// Display current daily test question.
window.renderDailyTestQuestion = function () {
    const questions = window.dailyTestQuestions;
    const index = window.dailyTestIndex;

    const questionBox =
        document.getElementById("dailyTestQuestion");

    const optionsBox =
        document.getElementById("dailyTestOptions");

    const feedbackBox =
        document.getElementById("dailyTestFeedback");

    const scoreBox =
        document.getElementById("dailyTestScore");

    const nextButton =
        document.getElementById("dailyTestNextBtn");

    if (!questionBox || !optionsBox) {
        console.error(
            "Daily test HTML IDs are missing."
        );
        return;
    }

    if (index >= questions.length) {
        questionBox.textContent = "Daily Test Completed!";

        optionsBox.replaceChildren();

        if (feedbackBox) {
            feedbackBox.textContent =
                "Your final score: " +
                window.dailyTestScore +
                " / " +
                questions.length;
        }

        if (scoreBox) {
            scoreBox.textContent =
                "Score: " +
                window.dailyTestScore +
                " / " +
                questions.length;
        }

        if (nextButton) {
            nextButton.textContent = "Restart Test";
            nextButton.disabled = false;
        }

        window.saveQuizScore(
            window.dailyTestScore,
            questions.length,
            "Daily Test"
        );

        return;
    }

    const item = questions[index];

    questionBox.textContent =
        (index + 1) + ". " +
        (
            item.question ||
            item.text ||
            item.question_text ||
            "Question"
        );

    optionsBox.replaceChildren();

    if (feedbackBox) {
        feedbackBox.textContent = "";
    }

    if (scoreBox) {
        scoreBox.textContent =
            "Score: " + window.dailyTestScore;
    }

    window.dailyTestAnswered = false;

    let options =
        item.options ||
        item.choices ||
        item.answers ||
        [];

    if (typeof options === "string") {
        try {
            options = JSON.parse(options);
        } catch {
            options = options.split(",");
        }
    }

    if (!Array.isArray(options)) {
        options = Object.values(options);
    }

    options.forEach(function (option, optionIndex) {
        const optionText =
            typeof option === "object" && option !== null
                ? String(
                    option.text ??
                    option.label ??
                    option.value ??
                    option.option ??
                    ""
                )
                : String(option);

        const button = document.createElement("button");

        button.type = "button";
        button.className = "daily-test-option";
        button.textContent = optionText;

        button.addEventListener("click", function () {
            window.checkDailyTestAnswer(
                optionText,
                optionIndex,
                button
            );
        });

        optionsBox.appendChild(button);
    });

    if (nextButton) {
        nextButton.textContent = "Next Question";
        nextButton.disabled = true;
    }
};


// Check daily test answer.
window.checkDailyTestAnswer = function (
    selectedText,
    selectedIndex,
    selectedButton
) {
    if (window.dailyTestAnswered) {
        return;
    }

    const item =
        window.dailyTestQuestions[window.dailyTestIndex];

    if (!item) {
        return;
    }

    window.dailyTestAnswered = true;

    const answer =
        item.answer ??
        item.correctAnswer ??
        item.correct_answer ??
        item.correct ??
        item.answer_text ??
        item.correct_option;

    const answerText =
        typeof answer === "object" && answer !== null
            ? String(
                answer.text ??
                answer.label ??
                answer.value ??
                answer.option ??
                ""
            )
            : String(answer ?? "");

    const answerIndex =
        item.correct_index ??
        item.correctIndex ??
        item.answer_index;

    let correct = false;

    if (answerIndex !== undefined && answerIndex !== null) {
        correct = Number(answerIndex) === selectedIndex;
    } else {
        correct =
            selectedText.trim().toLowerCase() ===
            answerText.trim().toLowerCase();
    }

    if (correct) {
        window.dailyTestScore++;

        if (selectedButton) {
            selectedButton.style.borderColor = "#22c55e";
        }
    } else if (selectedButton) {
        selectedButton.style.borderColor = "#ef4444";
    }

    const feedbackBox =
        document.getElementById("dailyTestFeedback");

    if (feedbackBox) {
        feedbackBox.textContent = correct
            ? "Correct answer! 🎉"
            : "Wrong answer. Correct answer: " + answerText;
    }

    const scoreBox =
        document.getElementById("dailyTestScore");

    if (scoreBox) {
        scoreBox.textContent =
            "Score: " + window.dailyTestScore;
    }

    const optionsBox =
        document.getElementById("dailyTestOptions");

    if (optionsBox) {
        optionsBox.querySelectorAll("button").forEach(function (button) {
            button.disabled = true;
        });
    }

    const nextButton =
        document.getElementById("dailyTestNextBtn");

    if (nextButton) {
        nextButton.disabled = false;
    }
};


// Move to the next daily test question.
window.nextDailyTestQuestion = function () {
    if (!window.dailyTestQuestions.length) {
        window.loadDailyTest();
        return;
    }

    if (
        window.dailyTestIndex >=
        window.dailyTestQuestions.length
    ) {
        window.loadDailyTest();
        return;
    }

    window.dailyTestIndex++;
    window.renderDailyTestQuestion();
};


// ============================================
// SAVE QUIZ SCORE
// Backend endpoint required: /save-quiz-score
// ============================================

window.saveQuizScore = async function (
    score,
    total,
    quizType
) {
    const percentage = total > 0
        ? Math.round((score / total) * 100)
        : 0;

    const result = {
        score: Number(score),
        total: Number(total),
        percentage: percentage,
        quiz_type: quizType || "Quiz",
        language: window.selectedLanguage || "Python"
    };

    console.log("Quiz result:", result);

    try {
        const response = await fetch("/save-quiz-score", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(result)
        });

        const data = await response.json();

        if (!response.ok) {
            console.warn(
                "Quiz score was not saved to the server:",
                data.message || data.error || response.status
            );
            return false;
        }

        console.log("Quiz score saved successfully.");
        return true;

    } catch (error) {
        console.warn(
            "Score saving endpoint is unavailable:",
            error.message
        );
        return false;
    }
};


// ============================================
// PROGRESS SUMMARY DISPLAY
// ============================================

window.updateProgressSummary = function (
    completedLessons,
    totalLessons,
    quizScore
) {
    const completedElement =
        document.getElementById("completedLessons");

    const totalElement =
        document.getElementById("totalLessons");

    const percentageElement =
        document.getElementById("progressPercentage");

    const progressBar =
        document.getElementById("progressBar");

    const percentage = totalLessons > 0
        ? Math.round(
            (completedLessons / totalLessons) * 100
        )
        : 0;

    if (completedElement) {
        completedElement.textContent = completedLessons;
    }

    if (totalElement) {
        totalElement.textContent = totalLessons;
    }

    if (percentageElement) {
        percentageElement.textContent = percentage + "%";
    }

    if (progressBar) {
        progressBar.style.width = percentage + "%";
        progressBar.setAttribute(
            "aria-valuenow",
            String(percentage)
        );
    }

    const quizScoreElement =
        document.getElementById("progressQuizScore");

    if (
        quizScoreElement &&
        quizScore !== undefined &&
        quizScore !== null
    ) {
        quizScoreElement.textContent = quizScore;
    }
};


// ============================================
// DAILY TEST BUTTON SUPPORT
// ============================================

document.addEventListener("DOMContentLoaded", function () {
    const dailyTestButton =
        document.getElementById("startDailyTestBtn");

    const nextButton =
        document.getElementById("dailyTestNextBtn");

    if (
        dailyTestButton &&
        !dailyTestButton.dataset.ready
    ) {
        dailyTestButton.dataset.ready = "true";

        dailyTestButton.addEventListener("click", function () {
            window.loadDailyTest();
        });
    }

    if (
        nextButton &&
        !nextButton.dataset.ready
    ) {
        nextButton.dataset.ready = "true";

        nextButton.addEventListener("click", function () {
            window.nextDailyTestQuestion();
        });
    }
});
// ============================================
// PART 6: DASHBOARD AND PAGE NAVIGATION
// ============================================

// Safely open a page using its HTML ID.
window.navigateToPage = function (pageId) {
    const page = document.getElementById(pageId);

    if (!page) {
        console.error("Page not found:", pageId);
        return;
    }

    if (typeof window.showPage === "function") {
        window.showPage(pageId);
    } else {
        document.querySelectorAll(".page").forEach(function (element) {
            element.style.display = "none";
        });

        page.style.display = "block";
    }
};


// Dashboard navigation.
window.goToDashboard = function () {
    if (typeof window.showPage === "function") {
        window.showPage("dashboard");
    }
};

window.openEditorPage = function () {
    if (typeof window.showPage === "function") {
        window.showPage("editorPage");
    }
};

window.openQuizPage = function () {
    if (typeof window.showPage === "function") {
        window.showPage("quizPage");
    }

    if (typeof window.loadQuiz === "function") {
        window.loadQuiz();
    }
};

window.openDailyTestPage = function () {
    if (typeof window.showPage === "function") {
        window.showPage("dailyTestPage");
    }

    if (typeof window.loadDailyTest === "function") {
        window.loadDailyTest();
    }
};

window.openProgressPage = function () {
    if (typeof window.showPage === "function") {
        window.showPage("progressPage");
    }

    if (typeof window.loadProgress === "function") {
        window.loadProgress();
    }
};

window.openProfilePage = function () {
    if (typeof window.showPage === "function") {
        window.showPage("profilePage");
    }

    if (typeof window.loadProfileData === "function") {
        window.loadProfileData();
    }
};

window.openChatPage = function () {
    if (typeof window.showPage === "function") {
        window.showPage("chatPage");
    }
};


// ============================================
// PART 6: UPDATE DASHBOARD USER NAME
// ============================================

window.updateDashboardUser = function (name, email) {
    const savedName =
        name ||
        sessionStorage.getItem("userName") ||
        "Student";

    const savedEmail =
        email ||
        sessionStorage.getItem("userEmail") ||
        "";

    const nameElements = [
        "dashboardUserName",
        "welcomeUserName",
        "profileName",
        "profileTopName",
        "profileUserName"
    ];

    nameElements.forEach(function (id) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = savedName;
        }
    });

    const emailElements = [
        "profileEmail",
        "userEmail"
    ];

    emailElements.forEach(function (id) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = savedEmail;
        }
    });
};


// ============================================
// PART 6: UPDATE PROFILE
// ============================================

window.updateProfile = async function () {
    const nameInput =
        document.getElementById("editProfileName") ||
        document.getElementById("profileEditName");

    const emailInput =
        document.getElementById("editProfileEmail") ||
        document.getElementById("profileEditEmail");

    const messageBox =
        document.getElementById("profileMessage");

    if (!nameInput || !emailInput) {
        console.error(
            "Profile input fields were not found. Check the HTML IDs."
        );
        return;
    }

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();

    if (!name) {
        if (messageBox) {
            messageBox.textContent = "Please enter your name.";
        } else {
            alert("Please enter your name.");
        }
        return;
    }

    if (!email) {
        if (messageBox) {
            messageBox.textContent = "Please enter your email.";
        } else {
            alert("Please enter your email.");
        }
        return;
    }

    try {
        const response = await fetch("/update-profile", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                email: email
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                data.message ||
                "Unable to update profile."
            );
        }

        sessionStorage.setItem(
            "userName",
            data.name || name
        );

        sessionStorage.setItem(
            "userEmail",
            data.email || email
        );

        window.updateDashboardUser(
            data.name || name,
            data.email || email
        );

        if (messageBox) {
            messageBox.textContent = "Profile updated successfully!";
        } else {
            alert("Profile updated successfully!");
        }

    } catch (error) {
        console.error("Profile Update Error:", error);

        if (messageBox) {
            messageBox.textContent =
                error.message || "Unable to update profile.";
        } else {
            alert(error.message || "Unable to update profile.");
        }
    }
};


// ============================================
// PART 6: MARK LESSON AS COMPLETED
// ============================================

window.completedLessons = window.completedLessons || [];

window.markLessonCompleted = async function (
    lessonIndex,
    lessonTitle
) {
    const index = Number(lessonIndex);

    if (!Number.isInteger(index) || index < 0) {
        console.error("Invalid lesson index:", lessonIndex);
        return;
    }

    const alreadyCompleted =
        window.completedLessons.includes(index);

    if (!alreadyCompleted) {
        window.completedLessons.push(index);
    }

    const statusElement =
        document.getElementById("lessonCompletionStatus");

    if (statusElement) {
        statusElement.textContent = "Lesson completed!";
    }

    const completeButton =
        document.getElementById("completeLessonBtn");

    if (completeButton) {
        completeButton.textContent = "Completed ✓";
        completeButton.disabled = true;
    }

    // Update visible progress using the loaded topic list.
    const totalLessons =
        Array.isArray(window.currentTopics)
            ? window.currentTopics.length
            : 0;

    if (typeof window.updateProgressSummary === "function") {
        window.updateProgressSummary(
            window.completedLessons.length,
            totalLessons
        );
    }

    // Optional backend save.
    // This requires a matching Flask endpoint.
    try {
        const response = await fetch("/complete-lesson", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                lesson_index: index,
                lesson_title: lessonTitle || "",
                language: window.selectedLanguage || "Python"
            })
        });

        if (!response.ok) {
            console.warn(
                "Lesson completion was updated in this page, " +
                "but the server did not save it."
            );
        }
    } catch (error) {
        console.warn(
            "Lesson completion endpoint is unavailable:",
            error.message
        );
    }
};


// ============================================
// PART 6: RESTORE USER NAME ON PAGE LOAD
// ============================================

document.addEventListener("DOMContentLoaded", function () {
    const savedName =
        sessionStorage.getItem("userName");

    const savedEmail =
        sessionStorage.getItem("userEmail");

    if (savedName || savedEmail) {
        window.updateDashboardUser(
            savedName,
            savedEmail
        );
    }

    // Complete current lesson when the button is clicked.
    const completeButton =
        document.getElementById("completeLessonBtn");

    if (
        completeButton &&
        !completeButton.dataset.ready
    ) {
        completeButton.dataset.ready = "true";

        completeButton.addEventListener("click", function () {
            const index =
                Number(window.currentLessonIndex || 0);

            const topic =
                Array.isArray(window.currentTopics)
                    ? window.currentTopics[index]
                    : null;

            const title = topic
                ? topic.title || topic.name || ""
                : "";

            window.markLessonCompleted(index, title);
        });
    }
});
// ============================================
// PART 7: FINAL INTEGRATION CHECK
// ============================================

window.checkCodingMentorApp = function () {
    console.clear();

    console.log("==================================");
    console.log("AI CODING MENTOR - INTEGRATION CHECK");
    console.log("==================================");

    // Check important JavaScript functions.
    const requiredFunctions = [
        "showPage",
        "submitAuth",
        "toggleAuth",
        "openCourse",
        "openLesson",
        "runCode",
        "analyzeCode",
        "loadQuiz",
        "renderQuizQuestion",
        "sendChatMessage",
        "loadProgress",
        "logoutUser"
    ];

    console.log("\n--- JavaScript Functions ---");

    requiredFunctions.forEach(function (functionName) {
        const available =
            typeof window[functionName] === "function";

        console.log(
            (available ? "OK: " : "MISSING: ") +
            functionName
        );
    });

    // Check important HTML elements.
    const requiredElements = [
        "welcomePage",
        "authPage",
        "dashboard",
        "languagePage",
        "editorPage",
        "quizPage",
        "chatPage",
        "progressPage",
        "profilePage",
        "codeEditor"
    ];

    console.log("\n--- HTML Elements ---");

    requiredElements.forEach(function (elementId) {
        const available =
            document.getElementById(elementId) !== null;

        console.log(
            (available ? "OK: " : "MISSING: ") +
            elementId
        );
    });

    console.log("\n--- Current App State ---");

    console.log(
        "Selected language:",
        window.selectedLanguage || "Python"
    );

    console.log(
        "Loaded chapters:",
        Array.isArray(window.currentTopics)
            ? window.currentTopics.length
            : "Not initialized"
    );

    console.log(
        "Saved session name:",
        sessionStorage.getItem("userName") || "No session name"
    );

    console.log(
        "Saved session email:",
        sessionStorage.getItem("userEmail") || "No session email"
    );

    console.log("==================================");
    console.log("Integration check completed.");
};


// ============================================
// CHECK JAVASCRIPT ERRORS
// ============================================

window.addEventListener("error", function (event) {
    console.error(
        "JavaScript Error:",
        event.message,
        "File:",
        event.filename,
        "Line:",
        event.lineno
    );
});


// ============================================
// INITIALIZE AUTH MODE SAFELY
// ============================================

document.addEventListener("DOMContentLoaded", function () {
    if (typeof window.renderAuthMode === "function") {
        window.renderAuthMode();
    }

    if (typeof window.checkCodingMentorApp === "function") {
        window.checkCodingMentorApp();
    }
});