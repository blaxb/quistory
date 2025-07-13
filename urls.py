# urls.py  ← same directory as manage.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1) Serve your frontend app at /
    path("", include("frontend.urls")),

    # 2) Your API endpoints
    path("api/auth/", include("users.urls")),
    path("api/quiz/", include("quizzes.urls")),

    # 3) Admin panel
    path("admin/", admin.site.urls),
]

