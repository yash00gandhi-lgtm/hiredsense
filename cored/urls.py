from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

from rest_framework.routers import DefaultRouter
from .views import ResumeViewSet, JobViewSet,auth_page,dashboard_page, resumes_ui, jobs_ui_page,reports_page, dashboard_stats

router = DefaultRouter()
router.register(r"resumes", ResumeViewSet, basename="resumes")
router.register(r"jobs", JobViewSet, basename="jobs")


urlpatterns = [
    
    path("auth/", auth_page, name="auth_page"), 
    path("resumes-ui/", resumes_ui, name="resumes_ui_page"),
    path("dashboard-stats/", dashboard_stats),


    path("jobs-ui/", jobs_ui_page, name="jobs_ui_page"),
    path("dashboard/", dashboard_page, name="dashboard_page"),
    path("auth-token/", obtain_auth_token, name="auth_token"), 
    path("", include(router.urls)),
    path("reports/", reports_page, name="reports_page"),



]
