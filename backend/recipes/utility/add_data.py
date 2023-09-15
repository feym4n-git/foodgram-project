import codecs
import json

with open("ingredients.json", "r", encoding="utf-8") as json_file:
    data = json.load(json_file)
    for i in range(len(data)):
        data[i] = {
            "model": "recipes.ingredient",
            "pk": i + 1,
            "fields": {
                "name": data[i]["name"],
                "measurement_unit": data[i]["measurement_unit"],
            },
        }
    with codecs.open("ingredients_new.json", "w", encoding="utf-8") as js:
        json.dump(data, js, ensure_ascii=False)
