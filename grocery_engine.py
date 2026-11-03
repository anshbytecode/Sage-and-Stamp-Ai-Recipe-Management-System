"""
grocery_engine.py
AI Grocery Assistant for Sage & Stamp – Advanced AI Edition.
Features:
- Aggregates ingredients across selected recipes or weekly meal plans
- Compares against pantry inventory to identify missing items
- Groups ingredients into supermarket aisles with realistic quantities
- Formats exportable shopping lists (Markdown, text, checklist)
"""
import re
import database as db


AISLE_MAPPINGS = {
    "Fresh Produce & Herbs": [
        "tomato", "onion", "garlic", "ginger", "spinach", "potato", "cauliflower",
        "coriander", "mint", "lemon", "lime", "cucumber", "avocado", "bell pepper",
        "chili", "peas", "carrots", "eggplant", "zucchini", "basil", "mushrooms", "curry leaves"
    ],
    "Dairy & Refrigerated": [
        "paneer", "butter", "cream", "milk", "yogurt", "ghee", "curd",
        "cheese", "mozzarella", "cheddar", "feta", "parmesan", "eggs"
    ],
    "Grains, Lentils & Flours": [
        "rice", "basmati", "flour", "all purpose flour", "besan", "gram flour",
        "poha", "macaroni", "pasta", "fettuccine", "noodles", "chickpeas",
        "lentils", "black lentils", "kidney beans", "rajma", "urad dal", "moong dal", "buns", "pita", "bread"
    ],
    "Spices & Seasonings": [
        "garam masala", "cumin", "coriander powder", "turmeric", "red chili powder",
        "kasuri methi", "cardamom", "cloves", "cinnamon", "fennel", "ajwain",
        "asafoetida", "hing", "black pepper", "oregano", "mustard seeds", "saffron", "chole masala", "biryani masala"
    ],
    "Oils, Sauces & Pantry Staples": [
        "oil", "olive oil", "mustard oil", "sesame oil", "sugar", "salt",
        "soy sauce", "tamarind", "vinegar", "tahini", "cashews", "peanuts",
        "coconut milk", "tomato puree", "salsa", "breadcrumbs"
    ]
}


class GroceryAssistant:
    def __init__(self):
        pass

    def get_aisle_for_ingredient(self, ingredient_name: str):
        ing_lower = ingredient_name.lower()
        for aisle, keywords in AISLE_MAPPINGS.items():
            if any(k in ing_lower for k in keywords):
                return aisle
        return "Oils, Sauces & Pantry Staples"

    def estimate_quantity(self, ingredient_name: str, servings: int = 4):
        ing = ingredient_name.lower()
        if "paneer" in ing:
            return f"{100 * servings // 4}g fresh paneer"
        if "rice" in ing or "basmati" in ing:
            return f"{200 * servings // 4}g basmati rice"
        if "chicken" in ing:
            return f"{250 * servings // 4}g cut pieces"
        if "tomato" in ing:
            return f"{3 * servings // 4} medium ripe tomatoes"
        if "onion" in ing:
            return f"{2 * servings // 4} medium onions"
        if "potato" in ing:
            return f"{3 * servings // 4} medium potatoes"
        if "butter" in ing:
            return "50g salted butter"
        if "cream" in ing:
            return "100ml fresh cream"
        if "garlic" in ing:
            return "1 whole bulb"
        if "ginger" in ing:
            return "2-inch fresh root"
        if "coriander" in ing or "mint" in ing:
            return "1 fresh bunch"
        if "oil" in ing:
            return "1 bottle cooking oil"
        if "spinach" in ing:
            return "250g fresh washed leaves"
        if "chickpeas" in ing or "rajma" in ing or "lentils" in ing:
            return f"{200 * servings // 4}g dry"
        return "1 standard pack / to taste"

    def generate_shopping_list(self, recipe_ids: list, pantry_inventory: str = ""):
        """
        Takes recipe IDs, cross-references with pantry text, and returns categorized missing grocery items.
        """
        pantry_items = set([p.strip().lower() for p in pantry_inventory.split(",") if p.strip()])
        all_recipes = [db.get_recipe(rid) for rid in recipe_ids if db.get_recipe(rid)]

        if not all_recipes:
            # Fallback to top popular recipes if none selected
            all_recipes = db.get_all_recipes()[:3]

        raw_ingredients = []
        for r in all_recipes:
            for item in r.get("ingredients", "").split(","):
                cleaned = item.strip()
                if cleaned:
                    raw_ingredients.append((cleaned, r["title"]))

        # Deduplicate and check against pantry
        categorized = {
            "Fresh Produce & Herbs": [],
            "Dairy & Refrigerated": [],
            "Grains, Lentils & Flours": [],
            "Spices & Seasonings": [],
            "Oils, Sauces & Pantry Staples": []
        }

        seen = set()
        total_items_needed = 0
        already_in_pantry = []

        for ing, dish in raw_ingredients:
            ing_lower = ing.lower()
            if ing_lower in seen:
                continue
            seen.add(ing_lower)

            # Check if in pantry
            in_pantry = False
            for p in pantry_items:
                if p in ing_lower or ing_lower in p:
                    in_pantry = True
                    break

            if in_pantry:
                already_in_pantry.append(ing.title())
            else:
                total_items_needed += 1
                aisle = self.get_aisle_for_ingredient(ing)
                qty = self.estimate_quantity(ing)
                categorized[aisle].append({
                    "name": ing.title(),
                    "quantity": qty,
                    "needed_for": dish,
                    "aisle": aisle,
                    "checked": False
                })

        # Filter empty aisles
        active_aisles = {k: v for k, v in categorized.items() if v}

        return {
            "recipes_included": [r["title"] for r in all_recipes],
            "total_items_to_buy": total_items_needed,
            "items_in_pantry": already_in_pantry,
            "aisles": active_aisles
        }


grocery_assistant = GroceryAssistant()
