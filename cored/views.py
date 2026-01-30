from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes



from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import Resume, Job, MatchReport
from .serializers import ResumeSerializer, JobSerializer
from .services import rank_jobs_for_resume, top_matches_for_job
from cored.services import build_match_reports_for_job
from .llm import generate_ai_report


# ===================== PAGES =====================

def auth_page(request):
    return render(request, "auth.html")


@login_required
def reports_page(request):
    return render(request, "reports.html")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user

    return Response({
        "resumes": Resume.objects.filter(user=user).count(),
        "jobs": Job.objects.count(),
        "matches": MatchReport.objects.filter(resume__user=user).count(),
        "recent_jobs": list(
            Job.objects.order_by("-created_at")[:5]
            .values("id", "title")
        ),
        "recent_resumes": list(
            Resume.objects.filter(user=user)
            .order_by("-created_at")[:5]
            .values("id", "title", "file")
        ),
    })



def dashboard_page(request):
    return render(request, "dashboard.html", {
        "active_tab": "overview",
    })




def resumes_ui(request):
    rid = request.GET.get("resume_id")

    # 🔒 SAFETY GUARD
    if rid in ("null", "undefined"):
        return redirect("/api/resumes-ui/")

    return render(request, "resumes_list.html")



def jobs_ui_page(request):
    return render(request, "jobs_list.html", {"active_tab": "jobs"})


# ===================== PERMISSIONS =====================

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, "user_id", None) == request.user.id


# ===================== RESUME VIEWSET =====================

class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]

    # 🔥 REQUIRED FOR FILE UPLOAD (THIS WAS MISSING)
    parser_classes = [MultiPartParser, FormParser]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "id"]
    ordering = ["-created_at"]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_matches(self, request):
        # 1. latest resume of logged-in user
        resume = (
            self.get_queryset()
            .filter(user=request.user)
            .order_by("-created_at")
            .first()
        )

        if not resume:
            return Response(
                {"detail": "No resume found. Upload a resume first."},
                status=400
            )

        resume_text = (
    getattr(resume, "content", None)
    or getattr(resume, "parsed_text", None)
    or ""
)


        results = []

        # 2. loop through all jobs
        for job in Job.objects.all():
            report = generate_ai_report(
                resume_text=resume_text,
                job_title=job.title,
                job_desc=job.description or "",
                job_skills=job.skills or "",
            )

            results.append({
                "job_id": job.id,
                "job_title": job.title,
                "ats_score": report["ats_score"],
                "missing_skills": report["missing_skills"],
                "improvements": report["improvements"],
                "interview_questions": report["interview_questions"],
            })

        # 3. sort by ATS score (high → low)
        results.sort(key=lambda x: x["ats_score"], reverse=True)

        return Response({
            "resume_id": resume.id,
             "resume_title": resume.title, 
            "matches": results
        })


    def get_serializer_context(self):
        return {"request": self.request}


    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def match(self, request, pk=None):
        resume = self.get_object()
        jobs_qs = Job.objects.all().order_by("-created_at")[:200]

        jobs = [{
            "id": j.id,
            "title": j.title,
            "description": j.description,
            "skills": j.skills,
        } for j in jobs_qs]

        ranked = rank_jobs_for_resume(resume.content, jobs)

        min_score = float(request.query_params.get("min_score", 0))
        must_have = request.query_params.get("must_have", "")

        ranked = [r for r in ranked if float(r.get("score", 0)) >= min_score]

        if must_have.strip():
            must = [s.strip().lower() for s in must_have.split(",") if s.strip()]
            ranked = [
                r for r in ranked
                if all(m in [x.lower() for x in r.get("matched_skills", [])] for m in must)
            ]

        return Response({"resume_id": resume.id, "results": ranked})

    @action(detail=True, methods=["post"], url_path="report")
    def report(self, request, pk=None):
        resume = self.get_object()
        job_id = request.data.get("job_id")

        if not job_id:
            return Response({"error": "job_id is required"}, status=400)

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"error": "job not found"}, status=404)

        ranked = rank_jobs_for_resume(resume.content, [{
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "skills": job.skills,
        }])

        rank0 = ranked[0] if ranked else {}
        ml_score = rank0.get("score", 0)

        matched_skills = rank0.get("matched_skills", [])
        missing_skills = rank0.get("missing_skills", [])
        breakdown = rank0.get("breakdown", {})

        ai = generate_ai_report(resume.content, job.title, job.description, job.skills)

        report_obj, _ = MatchReport.objects.update_or_create(
            resume=resume,
            job=job,
            defaults={
                "score": ml_score,
                "ats_score": int(ai.get("ats_score", 0)),
                "missing_skills": missing_skills,
                "tailored_summary": ai.get("tailored_summary", ""),
                "cover_letter": ai.get("cover_letter", ""),
                "interview_questions": ai.get("interview_questions", []),
                "improvements": ai.get("improvements", []),
            }
        )

        return Response({
            "resume_id": resume.id,
            "job_id": job.id,
            "ml_score": report_obj.score,
            "ats_score": report_obj.ats_score,
            "missing_skills": report_obj.missing_skills,
            "tailored_summary": report_obj.tailored_summary,
            "cover_letter": report_obj.cover_letter,
            "interview_questions": report_obj.interview_questions,
            "matched_skills": matched_skills,
            "breakdown": breakdown,
        })


# ===================== JOB VIEWSET =====================

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "description", "skills"]
    ordering_fields = ["created_at", "id"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["get"], url_path="matches")
    def matches(self, request, pk=None):
        job = self.get_object()

        min_score = request.query_params.get("min_score")
        must_have = request.query_params.get("must_have", "")
        must_have_list = [x.strip() for x in must_have.split(",") if x.strip()]

        search = (request.query_params.get("search") or "").strip().lower()
        ordering = (request.query_params.get("ordering") or "-created_at").strip()

        reports = top_matches_for_job(
            job.id,
            user=request.user,
            min_score=min_score,
            must_have=must_have_list,
        )

        rows = []
        for r in reports:
            if getattr(r.resume, "user_id", None) != request.user.id:
                continue

            rows.append({
                "resume_id": r.resume.id,
                "resume_title": r.resume.title or "",
                "username": r.resume.user.username if r.resume.user else "",
                "created_at": r.resume.created_at,
                "score": r.score,
                "ats_score": r.ats_score,
                "missing_skills": r.missing_skills,
            })

        if search:
            rows = [
                row for row in rows
                if search in f"{row['resume_title']} {row['username']}".lower()
            ]

        reverse = ordering.startswith("-")
        rows = sorted(rows, key=lambda x: x.get(ordering.lstrip("-"), 0), reverse=reverse)

        page = self.paginate_queryset(rows)
        if page is not None:
            return self.get_paginated_response({
                "job_id": job.id,
                "results": page,
            })

        return Response({"job_id": job.id, "results": rows})

    @action(detail=True, methods=["post"])
    def rebuild_matches(self, request, pk=None):
        stats = build_match_reports_for_job(int(pk), user=request.user) or {}
        return Response({"ok": True, **stats})

    @action(detail=True, methods=["get"], url_path="matches-export")
    def matches_export(self, request, pk=None):
        job = self.get_object()

        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="job_{job.id}_matches.csv"'

        import csv
        w = csv.writer(resp)
        w.writerow(["resume_id", "resume_title", "username", "score", "ats_score", "missing_skills"])

        qs = top_matches_for_job(job.id, user=request.user)
        for m in qs:
            w.writerow([
                m.resume_id,
                m.resume.title if m.resume else "",
                m.resume.user.username if m.resume and m.resume.user else "",
                m.score,
                m.ats_score,
                ", ".join(m.missing_skills or []),
            ])

        return resp
