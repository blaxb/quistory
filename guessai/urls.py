from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/",       admin.site.urls),
    path("api/auth/",    include("users.urls")),
    path("api/quiz/",    include("quizzes.urls")),
    path("",             include("frontend.urls")),  # all UI pages are now public
]

