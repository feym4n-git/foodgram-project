from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingList, Subscription, Tag)


class UserAdmin(UserAdmin):
    list_display = ("username", "email")
    list_filter = ("username", "email")


# Регистрируем модель User с настройками фильтров
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Настраиваем админ-класс для модели Recipe
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author")
    list_filter = ("author", "name", "tags")

    # Добавляем общее число добавлений этого рецепта в избранное
    def favorites_count(self, obj):
        return obj.favoriterecipe_set.count()

    favorites_count.short_description = "Favorites Count"
    readonly_fields = ("favorites_count",)


admin.site.register(Recipe, RecipeAdmin)


# Настраиваем админ-класс для модели Ingredient
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    list_filter = ("name",)


# Регистрируем модель Ingredient с настройками фильтров
admin.site.register(Ingredient, IngredientAdmin)

# Регистрируем остальные модели
admin.site.register(Tag)
admin.site.register(RecipeIngredient)
admin.site.register(Subscription)
admin.site.register(FavoriteRecipe)
admin.site.register(ShoppingList)
