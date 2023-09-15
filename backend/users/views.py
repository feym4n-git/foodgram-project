from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer
from .utility import get_tokens_for_user


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    '''
    Регистрирует нового пользователя.
    '''
    serializer = UserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(request.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    '''
    Получение токена.
    '''
    if 'email' not in request.data or 'password' not in request.data:
        return Response('Invalid data', status=status.HTTP_400_BAD_REQUEST)
    email = request.data['email']
    password = request.data['password']
    user = get_object_or_404(User, email=email)
    if not user.check_password(password):
        return Response('Invalid password', status=status.HTTP_400_BAD_REQUEST)
    return Response(get_tokens_for_user(user), status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    '''
    Обеспечивает CRUD-операции для пользователей.
    '''
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action == 'retrieve':
            return [IsAuthenticated()]
        return [AllowAny()]


class UserView(generics.RetrieveAPIView):
    '''
    Отображает информацию о текущем пользователе.
    '''
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = self.request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class DeleteTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user_token = Token.objects.get(user=request.user)
        user_token.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
