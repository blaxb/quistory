from django.contrib import admin
from django.urls import path, include  # ← you must import include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),  # ← plug in your users app urls
]

