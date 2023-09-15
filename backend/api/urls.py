from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (FavoriteRecipeView, ReadOnlyIngredientViewSet,
                    ReadOnlyTagViewSet, RecipeViewSet, ShoppingCartPDFView,
                    ShoppingCartView, SubscribeToAuthorView,
                    SubscriptionsListView)

app_name = 'api'

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', ReadOnlyIngredientViewSet)
router.register(r'tags', ReadOnlyTagViewSet)


urlpatterns = [
    path('users/subscriptions/', SubscriptionsListView.as_view(),
         name='subscriptions-list'),
    path('users/<int:author_id>/subscribe/', SubscribeToAuthorView.as_view(),
         name='subscribe-to-author'),
    path('recipes/<int:recipe_id>/favorite/', FavoriteRecipeView.as_view(),
         name='favorite-recipe'),
    path('recipes/<int:recipe_id>/shopping_cart/', ShoppingCartView.as_view(),
         name='shopping-cart'),
    path('recipes/download_shopping_cart/', ShoppingCartPDFView.as_view(),
         name='shopping-card-pdf'),
    path('', include(router.urls)),
]
