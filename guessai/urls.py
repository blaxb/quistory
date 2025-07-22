# guessai/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1) Serve your frontend at /
    path("",             include("frontend.urls")),

    # 2) API endpoints
    path("api/auth/",    include("users.urls")),
    path("api/quiz/",    include("quizzes.urls")),

    # 3) Admin
    path("admin/",       admin.site.urls),
]

