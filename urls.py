# urls.py  ← this lives next to manage.py, not in guessai/
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Hook the homepage into your frontend app
    path("", include("frontend.urls")),

    # 2. Your API routes
    path("api/auth/", include("users.urls")),
    path("api/quiz/", include("quizzes.urls")),

    # 3. Django admin
    path("admin/", admin.site.urls),
]

