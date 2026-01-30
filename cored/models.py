from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_recruiter = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)

    # 🔥 ACTUAL FILE
    file = models.FileField(upload_to="resumes/")

    # 🔥 extracted text (optional for now)
    content = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class Job(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    skills = models.TextField(help_text="Comma separated skills")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class MatchReport(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    ats_score = models.IntegerField(default=0)
    missing_skills = models.JSONField(default=list, blank=True)
    improvements = models.JSONField(default=list, blank=True)
    tailored_summary = models.TextField(blank=True, default="")
    cover_letter = models.TextField(blank=True, default="")
    interview_questions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("resume", "job")

    def __str__(self):
        return f"{self.resume_id} -> {self.job_id}"


