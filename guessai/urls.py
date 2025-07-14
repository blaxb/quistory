from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/",       admin.site.urls),
    path("api/auth/",    include("users.urls")),
    path("api/quiz/",    include("quizzes.urls")),

    # this must come last so “/” and everything under it
    # is handled by your frontend app
    path("",             include("frontend.urls")),
]

