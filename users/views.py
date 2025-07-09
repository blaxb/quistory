from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer

User = get_user_model()

class RegisterView(CreateAPIView):
    """
    POST /api/auth/register/ with JSON
      { "username","email","password","password2" }
    will create a new user with a properly hashed password.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class   = RegisterSerializer

