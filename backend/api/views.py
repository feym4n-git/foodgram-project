from io import BytesIO

from django.contrib.auth.models import User
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingList,
                            Subscription, Tag)
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import MyFilterBackend, RecipeFilter
from .permissions import IsOwner
from .serializers import (AuthorRecipeSerializer, AuthorSerializer,
                          IngredientSerializer, RecipeSerializer,
                          TagSerializer)
from .utility import summarize_ingredients


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (MyFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [
                AllowAny,
            ]
        elif self.request.method == 'PATCH' or self.request.method == 'DELETE':
            self.permission_classes = [
                IsOwner,
            ]
        else:
            self.permission_classes = [
                IsAuthenticated,
            ]
        return [permission() for permission in self.permission_classes]


class ReadOnlyIngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    lookup_field = 'id'
    permission_classes = [
        AllowAny,
    ]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class ReadOnlyTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'
    permission_classes = [
        AllowAny,
    ]
    pagination_class = None


class SubscriptionsListView(ListAPIView):
    serializer_class = AuthorSerializer

    def get_queryset(self):
        user = self.request.user
        author_ids = Subscription.objects.filter(user=user).values_list(
            'author', flat=True
        )
        authors = User.objects.filter(pk__in=author_ids)
        return authors


class SubscribeToAuthorView(APIView):
    def post(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        user = request.user

        if author == user:
            return Response('Вы не можете подписаться на себя', status=400)

        subscription, created = Subscription.objects.get_or_create(
            user=user, author=author
        )
        if created:
            return self.get_response(user, author)
        else:
            return Response('Вы уже подписаны на этого автора', status=400)

    def delete(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        user = request.user

        try:
            subscription = Subscription.objects.get(user=user, author=author)
            subscription.delete()
            return Response(status=204)
        except Subscription.DoesNotExist:
            return Response('Вы уже отписались от этого автора', status=400)

    def get_response(self, user, author):
        user_serializer = AuthorSerializer(author,
                                           context={'request': self.request})
        return Response(user_serializer.data)


class FavoriteRecipeView(APIView):
    def post(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        favorite_exists = FavoriteRecipe.objects.filter(
            user=user, recipe=recipe
        ).exists()
        if favorite_exists:
            return Response(
                {'detail': 'Recipe is already in favorites.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        FavoriteRecipe.objects.create(user=user, recipe=recipe)
        return Response(self.get_response(recipe),
                        status=status.HTTP_201_CREATED)

    def get_response(self, recipe):
        recipe_serializer = AuthorRecipeSerializer(
            recipe, context={'request': self.request}
        )
        return recipe_serializer.data

    def delete(self, request, recipe_id):
        user = request.user

        recipe = get_object_or_404(Recipe, pk=recipe_id)
        favorite_recipe = FavoriteRecipe.objects.filter(
            user=user, recipe=recipe
        ).first()

        if not favorite_recipe:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite_recipe.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class ShoppingCartView(APIView):
    def post(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        shopping_list_exists = ShoppingList.objects.filter(
            user=user, recipe=recipe
        ).exists()
        if shopping_list_exists:
            return Response(
                {'detail': 'Recipe is already added'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ShoppingList.objects.get_or_create(user=user, recipe=recipe)

        return Response(self.get_response(recipe),
                        status=status.HTTP_201_CREATED)

    def get_response(self, recipe):
        recipe_serializer = AuthorRecipeSerializer(
            recipe, context={'request': self.request}
        )
        return recipe_serializer.data

    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        obj = ShoppingList.objects.filter(user=user, recipe=recipe)

        if obj:
            obj.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )


class ShoppingCartPDFView(APIView):
    def get(self, request):
        user = request.user
        shopping_list = ShoppingList.objects.filter(user=user).values_list(
            'recipe', flat=True
        )

        recipes = Recipe.objects.filter(pk__in=shopping_list)
        serializer_data = RecipeSerializer(
            recipes, many=True, context={'request': request}
        )
        data = summarize_ingredients(serializer_data.data)
        buffer = BytesIO()
        buffer.write('Вот список ингридиентов к покупке'.encode('utf-8'))
        buffer.write('\n\n'.encode('utf-8'))
        for item in data.items():
            buffer.write(
                f'{item[0].capitalize()} ({item[1]["unit"]}) — '
                f'{item[1]["amount"]}\n'.encode(
                    'utf-8'
                )
            )
        buffer.seek(0)

        response = FileResponse(buffer, content_type='text/plain')
        context = 'attachment; filename="shopping_list.txt"'
        response['Content-Disposition'] = context

        return response
