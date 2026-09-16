"""
seed_data.py
Populates the database with a diverse starter set of recipes so the ML models
(cuisine classifier, clustering, recommender) have enough data to be useful
immediately. Run once: `python seed_data.py`
"""
import database as db

RECIPES = [
    # title, cuisine, ingredients, instructions, prep, cook, servings, calories, tags
    ("Margherita Pizza", "Italian",
     "pizza dough, tomato sauce, mozzarella, basil, olive oil, salt",
     "Roll out dough, spread tomato sauce, top with mozzarella and basil, "
     "drizzle olive oil, bake at 250C for 8 minutes.", 20, 10, 2, 780, "vegetarian,dinner"),
    ("Spaghetti Carbonara", "Italian",
     "spaghetti, eggs, pancetta, parmesan, black pepper, garlic",
     "Cook spaghetti. Fry pancetta with garlic. Mix eggs and parmesan, toss with "
     "hot pasta and pancetta off heat to create a creamy sauce.", 10, 15, 2, 650, "dinner,quick"),
    ("Chicken Tikka Masala", "Indian",
     "chicken breast, yogurt, garam masala, tomato puree, cream, garlic, ginger, onion, chili",
     "Marinate chicken in yogurt and spices. Grill chicken. Simmer tomato puree with "
     "onion, garlic, ginger, cream and add chicken.", 30, 25, 4, 590, "dinner,spicy"),
    ("Vegetable Biryani", "Indian",
     "basmati rice, mixed vegetables, yogurt, saffron, garam masala, onion, mint, ghee",
     "Fry onions until golden. Layer partially cooked rice with spiced vegetables and "
     "saffron milk. Cook on low heat until fragrant.", 25, 40, 4, 480, "vegetarian,dinner"),
    ("Beef Tacos", "Mexican",
     "ground beef, taco shells, lettuce, tomato, cheddar cheese, onion, cumin, chili powder",
     "Brown beef with cumin and chili powder. Fill taco shells with beef, lettuce, "
     "tomato, onion and cheese.", 15, 15, 4, 520, "dinner,quick"),
    ("Guacamole", "Mexican",
     "avocado, lime, cilantro, onion, tomato, jalapeno, salt",
     "Mash avocado, mix in lime juice, diced onion, tomato, jalapeno and cilantro. "
     "Season with salt.", 10, 0, 4, 210, "vegetarian,appetizer,vegan"),
    ("Chicken Fried Rice", "Chinese",
     "rice, chicken breast, egg, soy sauce, peas, carrot, garlic, spring onion, sesame oil",
     "Scramble egg and set aside. Stir-fry chicken, garlic, carrot and peas. Add rice, "
     "soy sauce and egg, toss with sesame oil and spring onion.", 15, 15, 3, 540, "dinner,quick"),
    ("Kung Pao Chicken", "Chinese",
     "chicken breast, peanuts, dried chili, soy sauce, garlic, ginger, spring onion, vinegar",
     "Stir-fry chicken until golden. Add garlic, ginger, dried chili, then soy sauce and "
     "vinegar. Toss with peanuts and spring onion.", 15, 15, 3, 480, "dinner,spicy"),
    ("Classic Beef Burger", "American",
     "ground beef, burger buns, cheddar cheese, lettuce, tomato, onion, ketchup, mustard",
     "Form beef patties, season and grill. Assemble on toasted buns with cheese, "
     "lettuce, tomato, onion and condiments.", 15, 10, 4, 700, "dinner,quick"),
    ("Mac and Cheese", "American",
     "macaroni, cheddar cheese, milk, butter, flour, breadcrumbs, mustard powder",
     "Make a roux with butter and flour, whisk in milk, melt in cheese. Combine with "
     "cooked macaroni, top with breadcrumbs and bake until golden.", 10, 25, 4, 610, "vegetarian,comfort"),
    ("Greek Salad", "Greek",
     "cucumber, tomato, red onion, feta cheese, olives, olive oil, oregano, lemon",
     "Chop cucumber, tomato and onion. Toss with olives and feta. Dress with olive oil, "
     "lemon juice and oregano.", 15, 0, 4, 320, "vegetarian,salad,healthy"),
    ("Chicken Souvlaki", "Greek",
     "chicken thigh, lemon, garlic, oregano, olive oil, pita bread, tzatziki",
     "Marinate chicken in lemon, garlic, oregano and olive oil. Skewer and grill. "
     "Serve in pita with tzatziki.", 20, 15, 4, 480, "dinner,grill"),
    ("Pad Thai", "Thai",
     "rice noodles, shrimp, egg, bean sprouts, peanuts, tamarind paste, fish sauce, lime, garlic",
     "Soak noodles. Stir-fry garlic, shrimp and egg. Add noodles, tamarind paste and "
     "fish sauce. Toss with bean sprouts, top with peanuts and lime.", 20, 15, 3, 560, "dinner,seafood"),
    ("Green Curry Chicken", "Thai",
     "chicken breast, green curry paste, coconut milk, thai basil, eggplant, fish sauce, chili",
     "Fry curry paste until fragrant, add coconut milk. Simmer chicken and eggplant, "
     "finish with fish sauce and thai basil.", 15, 20, 4, 510, "dinner,spicy"),
    ("Ratatouille", "French",
     "eggplant, zucchini, bell pepper, tomato, onion, garlic, thyme, olive oil",
     "Slice vegetables thinly. Layer with tomato sauce and garlic, drizzle olive oil "
     "and thyme, bake until tender.", 25, 45, 4, 240, "vegetarian,vegan,healthy"),
    ("French Onion Soup", "French",
     "onion, beef broth, butter, gruyere cheese, baguette, thyme, white wine",
     "Caramelize onions slowly in butter. Add broth and wine, simmer. Top with "
     "toasted baguette and melted gruyere.", 15, 60, 4, 380, "soup,comfort"),
    ("Falafel Wrap", "Middle Eastern",
     "chickpeas, garlic, parsley, cumin, coriander, tahini, pita bread, lettuce, tomato",
     "Blend chickpeas with garlic, herbs and spices, form balls and fry until crisp. "
     "Wrap in pita with tahini, lettuce and tomato.", 20, 15, 4, 430, "vegetarian,vegan"),
    ("Hummus", "Middle Eastern",
     "chickpeas, tahini, lemon, garlic, olive oil, cumin, salt",
     "Blend chickpeas, tahini, lemon juice, garlic and cumin until smooth. Drizzle "
     "with olive oil to serve.", 10, 0, 6, 180, "vegetarian,vegan,appetizer"),
    ("Miso Ramen", "Japanese",
     "ramen noodles, miso paste, pork belly, soft egg, corn, spring onion, garlic, chicken broth",
     "Simmer broth with miso and garlic. Cook noodles separately. Assemble with "
     "sliced pork, soft egg, corn and spring onion.", 20, 30, 2, 620, "dinner,soup"),
    ("Chicken Teriyaki", "Japanese",
     "chicken thigh, soy sauce, mirin, sugar, ginger, garlic, sesame seeds, rice",
     "Sear chicken skin-side down until crisp. Simmer with soy sauce, mirin, sugar, "
     "ginger and garlic until glazed. Serve over rice.", 10, 20, 3, 560, "dinner,quick"),
    ("Shakshuka", "Middle Eastern",
     "eggs, tomato, bell pepper, onion, garlic, cumin, paprika, cilantro",
     "Simmer tomato, pepper and onion with garlic and spices until thick. Crack eggs "
     "into the sauce and poach until set.", 10, 20, 3, 320, "vegetarian,breakfast"),
    ("Pancakes", "American",
     "flour, milk, eggs, sugar, baking powder, butter, vanilla extract",
     "Whisk dry and wet ingredients separately, then combine into a smooth batter. "
     "Cook on a griddle until bubbles form, flip and finish.", 10, 15, 4, 350, "breakfast,vegetarian"),
    ("Caprese Salad", "Italian",
     "tomato, mozzarella, basil, olive oil, balsamic glaze, salt",
     "Slice tomato and mozzarella, arrange with basil leaves, drizzle olive oil and "
     "balsamic glaze, season with salt.", 10, 0, 2, 280, "vegetarian,salad,quick"),
    ("Lentil Soup", "Middle Eastern",
     "red lentils, onion, carrot, cumin, garlic, vegetable broth, lemon, olive oil",
     "Saute onion, carrot and garlic. Add lentils, cumin and broth, simmer until soft. "
     "Finish with a squeeze of lemon.", 10, 30, 4, 260, "vegetarian,vegan,soup,healthy"),
    ("Butter Chicken", "Indian",
     "chicken thigh, butter, tomato puree, cream, garam masala, garlic, ginger, chili",
     "Cook chicken with garlic and ginger. Simmer in tomato puree, butter and cream "
     "with garam masala until thick and rich.", 20, 25, 4, 610, "dinner,spicy"),
]


def run():
    db.init_db()
    if db.count_recipes() > 0:
        print(f"Database already has {db.count_recipes()} recipes. Skipping seed.")
        return
    for (title, cuisine, ingredients, instructions, prep, cook, servings, calories, tags) in RECIPES:
        db.add_recipe(title, cuisine, ingredients, instructions, prep, cook,
                       servings, calories, tags, cuisine_predicted=0)
    print(f"Seeded {len(RECIPES)} recipes.")


if __name__ == "__main__":
    run()
