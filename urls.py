from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Serve your React or Django‐templated home page at "/"
    path("", include("frontend.urls")),

    # API endpoints
    path("api/auth/", include("users.urls")),
    path("api/quiz/", include("quizzes.urls")),

    # Admin
    path("admin/", admin.site.urls),
]

