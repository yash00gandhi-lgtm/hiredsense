from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import Resume, Job, MatchReport
from .serializers import ResumeSerializer, JobSerializer
from .services import rank_jobs_for_resume, top_matches_for_job
from .llm import generate_ai_report


# ===================== PAGES =====================

from django.contrib.auth import authenticate, login
from django.contrib import messages

def auth_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            return redirect("/api/dashboard/")
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "auth.html")



@login_required
def dashboard_page(request):
    return render(request, "dashboard.html", {"active_tab": "overview"})


@login_required
def reports_page(request):
    return render(request, "reports.html")


def resumes_ui(request):
    rid = request.GET.get("resume_id")
    if rid in ("null", "undefined"):
        return redirect("/api/resumes-ui/")
    return render(request, "resumes_list.html")


def jobs_ui_page(request):
    return render(request, "jobs_list.html", {"active_tab": "jobs"})


# ===================== DASHBOARD API =====================

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


# ===================== RESUME VIEWSET =====================

class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["created_at", "id"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # 🔥 MAIN ATS ENDPOINT
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_matches(self, request):
        resume = (
            Resume.objects
            .filter(user=request.user)
            .order_by("-created_at")
            .first()
        )

        if not resume:
            return Response(
                {"detail": "No resume found. Upload a resume first."},
                status=400
            )

        results = []

        for job in Job.objects.all():
            report = generate_ai_report(
                resume_file_path=resume.file.path,   # ✅ REAL PDF
                job_title=job.title,
                job_desc=job.description or "",
                job_skills=job.skills or "",
            )

            results.append({
                "job_id": job.id,
                "job_title": job.title,
                "ats_score": report["ats_score"],
                "missing_skills": report["missing_skills"],
                "improvements": report.get("improvements", []),
                "interview_questions": report.get("interview_questions", []),
            })

        results.sort(key=lambda x: x["ats_score"], reverse=True)

        return Response({
            "resume_id": resume.id,
            "resume_title": resume.title,
            "matches": results,
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

        reports = top_matches_for_job(job.id, user=request.user)

        rows = []
        for r in reports:
            if r.resume.user_id != request.user.id:
                continue

            rows.append({
                "resume_id": r.resume.id,
                "resume_title": r.resume.title,
                "username": r.resume.user.username,
                "score": r.score,
                "ats_score": r.ats_score,
                "missing_skills": r.missing_skills,
            })

        return Response({
            "job_id": job.id,
            "results": rows
        })
