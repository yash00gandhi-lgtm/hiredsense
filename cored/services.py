from typing import List, Dict, Tuple
import re
from .models import Job, Resume, MatchReport
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db import transaction

from django.db.models import Q


STOP = {"and","or","the","a","an","to","in","of","for","with","on","at","is","are","as","be"}

def _tokens(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z\+\#\.]{2,}", (text or "").lower())
    return [w for w in words if w not in STOP]

def _skill_set(text: str) -> set:
    return set(_tokens(text))

def _join(*parts: str) -> str:
    return " ".join([p for p in parts if p])


def rank_jobs_for_resume(resume_text: str, jobs: List[Dict]) -> List[Dict]:
    """
    Returns jobs with:
    - score (0-100)
    - matched_skills, missing_skills
    - breakdown: skills_score, title_score, desc_score
    """

    resume_text = resume_text or ""
    resume_skills = _skill_set(resume_text)

    # ----- FIELD-WISE TFIDF -----
    titles = [j.get("title", "") for j in jobs]
    descs  = [j.get("description", "") for j in jobs]
    skills = [j.get("skills", "") for j in jobs]

    def tfidf_sim(query: str, docs: List[str]) -> List[float]:
        corpus = [query] + docs
        vec = TfidfVectorizer(stop_words="english", max_features=5000)
        X = vec.fit_transform(corpus)
        sims = cosine_similarity(X[0:1], X[1:]).flatten()
        return [float(s) for s in sims]

    title_sims = tfidf_sim(resume_text, titles)
    desc_sims  = tfidf_sim(resume_text, descs)
    skill_sims = tfidf_sim(resume_text, skills)

    # weights (tuneable)
    W_SKILLS = 0.55
    W_TITLE  = 0.25
    W_DESC   = 0.20

    ranked = []
    for i, j in enumerate(jobs):
        job_skill_text = j.get("skills", "") or ""
        job_blob = _join(j.get("title",""), j.get("description",""), job_skill_text)

        job_skills = _skill_set(job_skill_text)


        matched = sorted(list(resume_skills.intersection(job_skills)))
        missing = sorted(list(job_skills.difference(resume_skills)))

        skills_score = skill_sims[i]
        title_score  = title_sims[i]
        desc_score   = desc_sims[i]

        final = (
            W_SKILLS * skills_score +
            W_TITLE  * title_score  +
            W_DESC   * desc_score
        )

        score_100 = round(final * 100.0, 2)

        ranked.append({
            **j,
            "score": score_100,
            "matched_skills": matched[:25],     # cap for response size
            "missing_skills": missing[:25],
            "breakdown": {
                "skills_score": round(skills_score * 100, 2),
                "title_score":  round(title_score * 100, 2),
                "desc_score":   round(desc_score * 100, 2),
            }
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked

# -------------------------------
# Day 3: Job -> Resume Matching (MatchReport)
# ADD BELOW existing code (do not replace rank_jobs_for_resume)
# -------------------------------

# ==========================
# Day 3 FINAL: Job -> Resumes ranking + MatchReport upsert
# (Keep rank_jobs_for_resume as-is above. Replace any older Day3 blocks with this one.)
# ==========================




def _job_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "title": job.title or "",
        "description": job.description or "",
        "skills": job.skills or "",
    }




@transaction.atomic
def build_match_reports_for_job(job_id: int, user=None) -> dict:
    """
    Score ALL resumes against ONE job using existing rank_jobs_for_resume(),
    then upsert MatchReport.
    Returns counts.
    """
    created = 0
    updated = 0

    job = Job.objects.get(id=job_id)
    payload = _job_dict(job)

    resumes = Resume.objects.select_related("user").all()
    if user is not None:
        resumes = resumes.filter(user=user)

    for res in resumes:
        ranked = rank_jobs_for_resume(res.content or "", [payload])
        r0 = ranked[0] if ranked else {}

        # ✅ Normalize score to 0-100
        raw_score = float(r0.get("score", 0) or 0)

        # normalize to 0-100 robustly
        if raw_score <= 1.0:
            score = raw_score * 100.0
        else:
            score = raw_score

        # clamp + round
        score = round(max(0.0, min(100.0, score)), 2)


        missing_skills = r0.get("missing_skills", []) or []
        breakdown = r0.get("breakdown", {}) or {}

        # ATS = skills_score% (already 0-100)
        ats_score = int(round(float(breakdown.get("skills_score", 0) or 0), 0))

        obj, was_created = MatchReport.objects.update_or_create(
            resume=res,
            job=job,
            defaults={
                "score": score,
                "ats_score": ats_score,
                "missing_skills": missing_skills,
            },
        )

        if was_created:
            created += 1
        else:
            updated += 1

    return {"created": created, "updated": updated, "job_id": job_id}



def top_matches_for_job(job_id: int, user=None, min_score=None, must_have=None, limit=None):
    """
    Returns MatchReport queryset (with resume + user preloaded) for ONE job.
    - user: required (only that user's resumes)
    - min_score: optional (float)
    - must_have: list[str] optional (resume.content contains all keywords)
    - limit: optional (int)
    """
    if user is None:
        raise ValueError("user is required")

    # normalize must_have safely
    if must_have is None:
        must_have = []
    if isinstance(must_have, str):
        # allow "python, django" or "python django"
        must_have = [x.strip() for x in must_have.replace("\n", ",").split(",") if x.strip()]
    else:
        must_have = [(x or "").strip() for x in must_have if (x or "").strip()]

    # Ensure reports exist (safe call)
    build_match_reports_for_job(job_id, user=user)

    qs = (
        MatchReport.objects
        .select_related("resume", "resume__user", "job")
        .filter(job_id=job_id, resume__user=user)
    )

    # min_score filter
    if min_score not in (None, ""):
        try:
            qs = qs.filter(score__gte=float(min_score))
        except (TypeError, ValueError):
            pass

    # must_have -> resume.content must include ALL keywords
    for kw in must_have:
        qs = qs.filter(resume__content__icontains=kw)

    # Highest score first
    qs = qs.order_by("-score", "-id")

    # limit
    if limit not in (None, ""):
        try:
            qs = qs[: int(limit)]
        except (TypeError, ValueError):
            pass

    return qs
