import random

recipes = {
    "chicken": [
        "Chicken Katsu",
        "Grilled Chicken",
        "Chicken Stir Fry",
        "Chicken Alfredo",
        "Chicken Tacos"
    ],

    "beef": [
        "Beef Stir Fry",
        "Beef Tacos",
        "Beef Stew",
        "Burger",
        "Beef Bulgogi"
    ],

    "pork": [
        "Pork Chops",
        "Pork Fried Rice",
        "BBQ Pork",
        "Pork Ramen"
    ],

    "fish": [
        "Grilled Fish",
        "Fish Tacos",
        "Baked Salmon",
        "Fish and Chips"
    ],

    "eggs": [
        "Scrambled Eggs",
        "Omelette",
        "Egg Fried Rice",
        "Egg Sandwich"
    ],

    "rice": [
        "Fried Rice",
        "Rice Bowl",
        "Chicken Rice",
        "Beef Rice Bowl"
    ],

    "pasta": [
        "Spaghetti Bolognese",
        "Pasta Alfredo",
        "Pasta Primavera",
        "Mac and Cheese"
    ],

    "vegetables": [
        "Vegetable Stir Fry",
        "Veggie Soup",
        "Roasted Vegetables",
        "Vegetable Curry"
    ],

    "bread": [
        "Grilled Cheese",
        "Ham Sandwich",
        "Avocado Toast",
        "French Toast"
    ],

    "cheese": [
        "Cheese Quesadilla",
        "Mac and Cheese",
        "Cheese Omelette"
    ]
}


def user_input(user_input_string):

    
   # while True: 
        clean_input = user_input_string.lower().replace(" ", "")
        ingredients = clean_input.split(",")
        possibe_recipe = []

        for ingredient in ingredients:
            if ingredient in recipes: 
                for recipe in recipes[ingredient]:
                    possibe_recipe.append(recipe)
            
        if possibe_recipe:
            return (random.choice(possibe_recipe))
        else:
            return("Recipe not found")


"""
        while True:
            question = input("Do you want another recipe? (Y/N): ")
            if question.lower() == "y":
                break
            elif question.lower() == "n":
                return
            else:
                print("Invalid Choice")
"""
         



