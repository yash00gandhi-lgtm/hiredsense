from rest_framework import serializers
from .models import Resume, Job, MatchReport

class ResumeSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ["id", "title", "file", "file_url", "created_at"]
        read_only_fields = ("user",)

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = "__all__"

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["id", "title", "description", "skills", "created_at"]
        read_only_fields = ["id", "created_at"]
        
class MatchReportMiniSerializer(serializers.ModelSerializer):
    resume_title = serializers.CharField(source="resume.title", read_only=True)
    username = serializers.CharField(source="resume.user.username", read_only=True)

    class Meta:
        model = MatchReport
        fields = [
            "resume_id",
            "resume_title",
            "username",
            "job_id",
            "score",
            "ats_score",
            "missing_skills",
        ]