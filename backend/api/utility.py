def summarize_ingredients(recipes):
    data = {}
    for recipe in recipes:
        for ingredient in recipe['ingredients']:
            if ingredient['name'] not in data:
                data[ingredient['name']] = {
                    'amount': ingredient['amount'],
                    'unit': ingredient['measurement_unit'],
                }
            else:
                data[ingredient['name']]['amount'] += ingredient['amount']
    return data
