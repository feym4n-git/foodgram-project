import base64

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import transaction

from loguru import logger
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Subscription, Tag)
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    id = serializers.CharField(source='ingredient.id', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)

    def to_representation(self, obj):
        if obj:
            return settings.MEDIA_URL + str(obj)
        return None


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients',
        many=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_author(self, obj):
        author = obj.author
        user = self.context['request'].user
        is_subscribed = False
        if user.is_authenticated:
            is_subscribed = Subscription.objects.filter(
                user=user, author=author
            ).exists()
        return {
            'email': author.email,
            'id': author.id,
            'username': author.username,
            'first_name': author.first_name,
            'last_name': author.last_name,
            'is_subscribed': is_subscribed,
        }

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        is_favorited = False
        if user.is_authenticated:
            is_favorited = FavoriteRecipe.objects.filter(user=user,
                                                         recipe=obj).exists()
        return is_favorited

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        result = False
        if user.is_authenticated:
            result = ShoppingList.objects.filter(user=user,
                                                 recipe=obj).exists()
        return result

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        ingredients_data = data.get('ingredients', [])
        recipeingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            recipeingredient_data = {'amount': amount, 'id': ingredient_id}
            recipeingredients.append(recipeingredient_data)

        ret['recipeingredients'] = recipeingredients
        return ret

    def create_tags(self, tags_data):
        tags = []
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(id=tag_data)
            tags.append(tag)
        return tags

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredients')
        tags_data = self.initial_data.get('tags', [])
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        tags = self.create_tags(tags_data)
        recipe.tags.set(tags)

        return recipe

    def update(self, instance, validated_data):
        logger.info('Patch')
        if 'name' in validated_data:
            instance.name = validated_data['name']
        if 'image' in validated_data:
            instance.image = validated_data['image']
        if 'text' in validated_data:
            instance.text = validated_data['text']
        if 'cooking_time' in validated_data:
            instance.cooking_time = validated_data['cooking_time']
        instance.save()

        tags_data = self.initial_data.get('tags', [])
        tags = self.create_tags(tags_data)
        instance.tags.set(tags)

        ingredients_data = validated_data.get('recipeingredients', [])

        existing_ingredients = instance.ingredients.all()

        for existing_ingredient in existing_ingredients:
            instance.ingredients.remove(existing_ingredient)
        instance.save()

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            if ingredient_id and amount is not None:
                try:
                    ingredient = Ingredient.objects.get(id=ingredient_id)
                    RecipeIngredient.objects.create(
                        recipe=instance, ingredient=ingredient, amount=amount
                    )
                except RecipeIngredient.DoesNotExist:
                    pass
        instance.save()
        return instance


class AuthorRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AuthorSerializer(serializers.ModelSerializer):
    recipes = AuthorRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscription.objects.filter(user=user, author=obj).exists()
