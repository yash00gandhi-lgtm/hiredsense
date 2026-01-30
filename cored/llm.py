import re
from collections import defaultdict

# --------------------------------------------------
# SKILL NORMALIZATION
# --------------------------------------------------

SKILL_SYNONYMS = {
    "django-rest-framework": "drf",
    "django rest framework": "drf",
    "rest api": "api",
    "restful": "api",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "js": "javascript",
}

ROLE_SKILLS = {
    "backend": {
        "core": {"python", "django", "drf", "api", "sql"},
        "plus": {"celery", "redis", "docker", "postgresql", "mysql", "aws"},
    },
    "frontend": {
        "core": {"javascript", "html", "css", "react"},
        "plus": {"redux", "tailwind", "webpack"},
    },
    "fullstack": {
        "core": {"python", "django", "javascript", "react"},
        "plus": {"docker", "api"},
    },
}

STOPWORDS = {
    "and","or","the","a","an","to","in","of","for","with",
    "on","at","is","are","as","be","job","role","developer",
    "engineer","test","start"
}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def normalize_skill(word: str) -> str:
    return SKILL_SYNONYMS.get(word, word)

def extract_skills(text: str) -> set:
    words = re.findall(r"[a-zA-Z\+\#\.]{2,}", text.lower())
    skills = set()

    for w in words:
        if w in STOPWORDS:
            continue
        skills.add(normalize_skill(w))

    return skills

def infer_role(job_title: str) -> str:
    title = job_title.lower()
    if "backend" in title:
        return "backend"
    if "frontend" in title:
        return "frontend"
    if "full" in title:
        return "fullstack"
    return "backend"  # safe default

# --------------------------------------------------
# MAIN ATS ENGINE
# --------------------------------------------------

def generate_ai_report(
    resume_text: str,
    job_title: str,
    job_desc: str,
    job_skills: str
) -> dict:

    resume_skills = extract_skills(resume_text or "")
    job_text = f"{job_title} {job_desc} {job_skills}"
    job_words = extract_skills(job_text)

    # Role detection
    role = infer_role(job_title)
    role_core = ROLE_SKILLS[role]["core"]
    role_plus = ROLE_SKILLS[role]["plus"]

    # ---------------------------
    # ATS SCORING
    # ---------------------------

    # Core skills (40)
    core_matched = resume_skills.intersection(role_core)
    core_score = (len(core_matched) / max(1, len(role_core))) * 40

    # Plus skills (20)
    plus_matched = resume_skills.intersection(role_plus)
    plus_score = (len(plus_matched) / max(1, len(role_plus))) * 20

    # Keyword overlap (20)
    keyword_overlap = resume_skills.intersection(job_words)
    keyword_score = min(20, len(keyword_overlap) * 2)

    # Resume strength (20)
    if len(resume_skills) >= 12:
        structure_score = 20
    elif len(resume_skills) >= 8:
        structure_score = 15
    elif len(resume_skills) >= 5:
        structure_score = 10
    else:
        structure_score = 5

    raw_ats = core_score + plus_score + keyword_score + structure_score
    ats_score = int(max(20, min(95, round(raw_ats))))

    # ---------------------------
    # MISSING SKILLS
    # ---------------------------

    missing_core = sorted(list(role_core - resume_skills))
    missing_plus = sorted(list(role_plus - resume_skills))
    missing_skills = (missing_core + missing_plus)[:8]

    # ---------------------------
    # IMPROVEMENTS
    # ---------------------------

    improvements = [
        f"Strengthen core {role} skills like: {', '.join(list(role_core)[:3])}.",
        "Add 1–2 measurable projects with clear tech stack and outcomes.",
        "Mirror important keywords from the job description.",
        "Add GitHub, LinkedIn, and deployed project links.",
    ]

    # ---------------------------
    # INTERVIEW QUESTIONS (ROLE-AWARE)
    # ---------------------------

    interview_questions = [
        {
            "q": f"What are the core responsibilities of a {role} developer?",
            "ideal_answer": (
                f"Design, build, and maintain scalable {role} systems "
                f"with clean architecture, performance, and best practices."
            ),
        },
        {
            "q": "How do you design scalable APIs?",
            "ideal_answer": (
                "Use REST principles, proper status codes, pagination, "
                "authentication, caching, and optimized database queries."
            ),
        },
        {
            "q": "What is the N+1 query problem?",
            "ideal_answer": (
                "When a query triggers additional queries per item; "
                "solved using select_related or prefetch_related."
            ),
        },
        {
            "q": "How do you debug production issues?",
            "ideal_answer": (
                "Check logs, reproduce the issue, narrow down the root cause, "
                "add tests, and deploy a minimal safe fix."
            ),
        },
    ]

    # ---------------------------
    # FINAL RESPONSE
    # ---------------------------

    return {
        "ats_score": ats_score,
        "ats_breakdown": {
            "role_detected": role,
            "core_skills": round(core_score),
            "plus_skills": round(plus_score),
            "keywords": round(keyword_score),
            "resume_strength": structure_score,
        },
        "missing_skills": missing_skills,
        "improvements": improvements,
        "interview_questions": interview_questions,
    }
