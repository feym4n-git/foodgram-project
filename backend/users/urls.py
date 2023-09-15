from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views
from .views import DeleteTokenView, UserView, get_token

app_name = 'users'


router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

auth_urls = [
    path('token/login/', get_token, name='token'),
    path('token/logout/', DeleteTokenView.as_view(), name='delete_token'),
]

urlpatterns = [
    path('auth/', include(auth_urls)),
    path('users/me/', UserView.as_view(), name='user_view'),
    path(
        'users/set_password/',
        views.ChangePasswordView.as_view(),
        name='change-password',
    ),
    path('', include(router.urls)),
]
