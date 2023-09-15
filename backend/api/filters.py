from django_filters import rest_framework as filters
from recipes.models import Recipe


class MyFilterBackend(filters.DjangoFilterBackend):
    def get_filterset_kwargs(self, request, queryset, view):
        kwargs = super().get_filterset_kwargs(request, queryset, view)
        kwargs['user'] = request.user
        if hasattr(view, 'get_filterset_kwargs'):
            kwargs.update(view.get_filterset_kwargs())

        return kwargs


class RecipeFilter(filters.FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart', label='Is in shopping cart'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited', label='Is_favorited'
    )
    tags = filters.CharFilter(
        method='filter_by_tags_slug',
        label='Tags (slug)',
        field_name='tags',
    )

    class Meta:
        model = Recipe
        fields = []

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            if self.user.is_authenticated:
                queryset = Recipe.objects.filter(shoppinglist__user=self.user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if value:
            if self.user.is_authenticated:
                queryset = Recipe.objects.filter(
                    favoriterecipe__user=self.user
                )
        return queryset

    def filter_by_tags_slug(self, queryset, name, value):
        return queryset.filter(tags__slug=value)
