from rest_framework.permissions import BasePermission


class IsRecruiter(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_recruiter


class IsCandidate(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.is_recruiter