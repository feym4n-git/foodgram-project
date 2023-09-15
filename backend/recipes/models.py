from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import IntegerField, Model


class CoolModelBro(Model):
    limited_integer_field = IntegerField(
        default=1, validators=[MaxValueValidator(100), MinValueValidator(1)]
    )


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="recipes")
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="recipes/images/")
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(
        validators=[MaxValueValidator(4320), MinValueValidator(1)]
    )
    tags = models.ManyToManyField("Tag")
    ingredients = models.ManyToManyField("Ingredient",
                                         through="RecipeIngredient")

    def __str__(self):
        return f"{self.name}"


class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return f"{self.name}"


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    measurement_unit = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipeingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name="ingredients"
    )
    amount = models.PositiveIntegerField(
        validators=[MaxValueValidator(10000), MinValueValidator(1)]
    )

    def __str__(self):
        return f"{self.ingredient}, {self.amount}"


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscribers"
    )

    class Meta:
        unique_together = ("user", "author")

    def __str__(self):
        return f"{self.user} follows {self.author}"


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "recipe")

    def __str__(self):
        return f"{self.user} favorites {self.recipe}"


class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        return f"Shopping list for {self.user}"
