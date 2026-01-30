import re
import pdfplumber

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
    "engineer","experience","skills","project","projects"
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
    return "backend"

# --------------------------------------------------
# PDF TEXT EXTRACTION
# --------------------------------------------------

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception:
        pass
    return text.lower()

# --------------------------------------------------
# MAIN ATS ENGINE
# --------------------------------------------------

def generate_ai_report(resume_file_path, job_title, job_desc, job_skills):

    resume_text = extract_text_from_pdf(resume_file_path)
    resume_skills = extract_skills(resume_text)

    job_text = f"{job_title} {job_desc} {job_skills}".lower()
    job_words = extract_skills(job_text)

    role = infer_role(job_title)
    role_core = ROLE_SKILLS[role]["core"]
    role_plus = ROLE_SKILLS[role]["plus"]

    # ---------------------------
    # ATS SCORING
    # ---------------------------

    core_score = (len(resume_skills & role_core) / len(role_core)) * 40
    plus_score = (len(resume_skills & role_plus) / max(1, len(role_plus))) * 20
    keyword_score = min(20, len(resume_skills & job_words) * 2)

    structure_score = (
        20 if len(resume_skills) >= 12 else
        15 if len(resume_skills) >= 8 else
        10 if len(resume_skills) >= 5 else
        5
    )

    ats_score = int(min(95, max(20, core_score + plus_score + keyword_score + structure_score)))

    # ---------------------------
    # MISSING SKILLS
    # ---------------------------

    missing_skills = list((role_core | role_plus) - resume_skills)[:8]

    return {
        "ats_score": ats_score,
        "missing_skills": missing_skills,
        "resume_skills_found": sorted(list(resume_skills)),
        "role_detected": role,
    }
