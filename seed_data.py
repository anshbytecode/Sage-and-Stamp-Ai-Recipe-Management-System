"""
seed_data.py
Populates the database with an authentic, India-compliant starter set of recipes:
- Absolutely NO beef, steak, cow meat, pork, bacon, or prohibited animal broths.
- Diverse Indian culinary masterpieces (without 'Indian' prefixed to titles: e.g. Paneer Butter Masala, Dal Makhani, Biryani, Chole Bhature).
- Beloved international vegetarian and chicken dishes (Margherita Pizza, Pad Thai, Falafel, etc.).
"""
import database as db

RECIPES = [
    # title, cuisine, ingredients, instructions, prep, cook, servings, calories, tags
    ("Paneer Butter Masala", "North Indian",
     "paneer, butter, tomato puree, cream, cashew nuts, garam masala, kasuri methi, ginger, garlic, red chili powder",
     "Soak cashews and blend into a paste. Saute ginger and garlic in butter. Add tomato puree and spices, simmer until aromatic. Stir in cashew paste and cream, then add paneer cubes. Finish with crushed kasuri methi.",
     20, 20, 4, 490, "vegetarian,dinner,rich,popular"),

    ("Dal Makhani", "North Indian",
     "whole black lentils, red kidney beans, butter, cream, ginger, garlic, tomato puree, garam masala, cumin",
     "Soak black lentils and rajma overnight. Pressure cook until completely tender. Simmer on low heat with butter, ginger, garlic and tomato puree for 45 minutes. Stir in fresh cream and garam masala.",
     15, 60, 5, 380, "vegetarian,dinner,comfort,protein"),

    ("Chole Bhature", "North Indian",
     "chickpeas, all purpose flour, yogurt, onion, tomato, ginger, garlic, chole masala, tea bag, green chili, oil",
     "Boil soaked chickpeas with a black tea bag for deep color. Saute onions, tomatoes, ginger and chole masala until fragrant. Simmer chickpeas in sauce. Knead flour with yogurt, roll into discs and deep fry bhature until puffed.",
     30, 40, 4, 620, "vegetarian,lunch,comfort,spicy"),

    ("Palak Paneer", "North Indian",
     "fresh spinach, paneer, garlic, ginger, green chili, onion, cumin seeds, cream, garam masala",
     "Blanch fresh spinach in boiling water for 2 minutes, then plunge into ice water and puree. Saute cumin, garlic, ginger and onions. Add spinach puree and spices. Gently fold in paneer cubes and a splash of cream.",
     15, 15, 4, 340, "vegetarian,dinner,healthy,iron-rich"),

    ("Pav Bhaji", "Maharashtrian",
     "potatoes, green peas, cauliflower, bell pepper, tomatoes, onion, pav bhaji masala, butter, pav buns, lemon, coriander",
     "Boil and mash vegetables smoothly. In a wide pan, melt generous butter, saute onions, tomatoes and pav bhaji masala. Add mashed vegetables with a splash of water and simmer. Toast pav buns in butter and serve with lemon.",
     20, 25, 4, 450, "vegetarian,street-food,dinner,popular"),

    ("Masala Dosa", "South Indian",
     "fermented rice batter, urad dal, potatoes, mustard seeds, curry leaves, green chili, turmeric, onion, ghee",
     "Boil and mash potatoes. Temper mustard seeds, curry leaves, onions and green chili in oil with turmeric, then toss with potatoes. Spread batter thinly on a hot greased griddle, drizzle ghee, cook until crisp, fill with potato masala.",
     20, 15, 4, 320, "vegetarian,breakfast,crispy,gluten-free"),

    ("Rajma Chawal", "North Indian",
     "red kidney beans, basmati rice, onion, tomato, ginger, garlic, cumin, coriander powder, garam masala, ghee",
     "Soak kidney beans overnight and boil until tender. Saute finely chopped onions, ginger, garlic and tomato paste with spices. Simmer rajma in gravy until thick. Serve hot over steamed basmati rice with a spoonful of ghee.",
     15, 45, 4, 410, "vegetarian,lunch,protein,comfort"),

    ("Hyderabadi Chicken Biryani", "Hyderabadi",
     "basmati rice, chicken thigh, yogurt, fried onions, saffron, mint, coriander, ginger, garlic, biryani masala, ghee",
     "Marinate chicken in yogurt, biryani masala, ginger-garlic paste and mint. Par-boil basmati rice with whole spices. Layer marinated chicken and fragrant rice in a heavy pot, drizzle saffron milk and ghee, seal tightly and cook on dum.",
     30, 45, 5, 580, "chicken,dinner,spicy,special"),

    ("Mutton Rogan Josh", "Kashmiri",
     "mutton, yogurt, kashmiri red chili, fennel powder, ginger powder, cardamom, cloves, cinnamon, mustard oil",
     "Heat mustard oil until smoking, sear mutton pieces until lightly browned. Whisk yogurt with kashmiri chili, dry ginger and fennel powder. Simmer mutton in spiced yogurt gravy on low heat until fork-tender and aromatic.",
     25, 60, 4, 540, "mutton,dinner,spicy,rich"),

    ("Aloo Gobi Adraki", "North Indian",
     "potatoes, cauliflower florets, fresh ginger, green chilies, cumin seeds, turmeric, coriander powder, fresh coriander",
     "Saute cumin seeds and julienned ginger in mustard oil. Add potato wedges and cauliflower florets with turmeric, coriander and salt. Cover and steam-cook on low flame until tender. Garnish with crisp ginger slivers.",
     15, 20, 4, 230, "vegetarian,vegan,quick,everyday"),

    ("Paneer Tikka", "North Indian",
     "paneer, bell pepper, red onion, hung curd, ajwain, tandoori masala, ginger garlic paste, lemon juice, chaat masala",
     "Whisk hung curd with tandoori masala, ajwain, lemon juice and salt. Coat diced paneer, bell peppers and onions in marinade. Thread onto skewers and grill at high heat until edges are charred. Dust with chaat masala.",
     20, 15, 4, 380, "vegetarian,appetizer,grill,high-protein"),

    ("Malai Kofta", "North Indian",
     "paneer, boiled potatoes, cashews, raisins, tomato puree, fresh cream, cardamom powder, kasuri methi, butter",
     "Mash paneer and potatoes together, stuff with cashews and raisins, shape into dumplings and fry golden. Prepare a velvety gravy with butter, pureed tomatoes, cashew cream and cardamom. Pour warm gravy over koftas before serving.",
     30, 30, 4, 530, "vegetarian,festive,rich,dinner"),

    ("Baingan Bharta", "Punjabi",
     "large eggplant, onions, ripe tomatoes, green peas, green chili, garlic, mustard oil, cumin, fresh coriander",
     "Roast whole eggplant directly over open flame until skin is completely charred and flesh is smoky and soft. Peel and mash. Saute garlic, onions, tomatoes and green peas in mustard oil. Mix in mashed eggplant and cook 10 minutes.",
     15, 25, 4, 210, "vegetarian,vegan,smoky,healthy"),

    ("Samosa Chaat", "North Indian",
     "boiled potatoes, green peas, pastry flour, chickpeas, tamarind chutney, mint coriander chutney, sev, yogurt, chaat masala",
     "Stuff pastry with spiced potato-pea mixture and fry crisp samosas. Crush two warm samosas in a bowl, top with hot chole gravy, chilled sweetened yogurt, zesty mint chutney, tangy tamarind chutney, fine sev and fresh coriander.",
     25, 25, 4, 460, "vegetarian,snack,street-food,crispy"),

    ("Khaman Dhokla", "Gujarati",
     "gram flour besan, ginger chili paste, lemon juice, turmeric, mustard seeds, curry leaves, green chilies, coriander",
     "Whisk besan with water, ginger-chili paste, turmeric and lemon into a smooth batter. Add fruit salt, pour into greased tin and steam 15 minutes until spongy. Temper mustard seeds, curry leaves and green chilies in oil with sweetened water, pour over.",
     10, 15, 6, 190, "vegetarian,vegan,breakfast,snack,low-calorie"),

    ("Kanda Poha", "Maharashtrian",
     "flattened rice poha, onions, roasted peanuts, mustard seeds, curry leaves, green chilies, turmeric, fresh coriander, lemon",
     "Rinse poha and drain. Splutter mustard seeds in oil, fry crunchy peanuts, then saute onions, curry leaves and green chilies. Stir in turmeric and rinsed poha. Toss gently on low heat and finish with freshly squeezed lemon juice.",
     10, 10, 3, 260, "vegetarian,breakfast,quick,light"),

    ("Gulab Jamun", "Dessert",
     "milk powder, all purpose flour, ghee, green cardamom, saffron strands, sugar syrup, rose water",
     "Knead milk powder, flour and a touch of ghee with milk into a soft pliable dough. Roll into smooth small balls without cracks. Fry on gentle low heat in ghee until uniformly deep golden. Soak in warm cardamom-saffron sugar syrup.",
     20, 25, 6, 320, "vegetarian,dessert,festive,sweet"),

    ("Chicken Tikka Masala", "Mughlai",
     "chicken breast, yogurt, garam masala, tomato puree, cream, garlic, ginger, onion, chili",
     "Marinate chicken in spiced yogurt. Grill chicken until charred. Simmer tomato puree with sauteed onion, garlic, ginger and cream. Fold grilled chicken pieces into velvety gravy.",
     30, 25, 4, 590, "chicken,dinner,spicy,popular"),

    ("Butter Chicken", "Mughlai",
     "chicken thigh, butter, tomato puree, cream, garam masala, garlic, ginger, kasuri methi, honey",
     "Cook marinated chicken with garlic and ginger. Simmer rich tomato puree, butter and cashew cream with garam masala and kasuri methi until thick. Fold in chicken and glaze.",
     20, 25, 4, 610, "chicken,dinner,rich,popular"),

    ("Vegetable Biryani", "Awadhi",
     "basmati rice, carrots, green beans, peas, yogurt, saffron, garam masala, onion, mint, ghee",
     "Fry sliced onions until deeply golden. Parboil basmati rice with whole spices. Layer fragrant spiced vegetables with rice, saffron milk and fresh mint. Steam on low flame.",
     25, 40, 4, 480, "vegetarian,dinner,fragrant"),

    # Global Favorites (100% India-compliant: no beef, no pork, no steak)
    ("Margherita Pizza", "Italian",
     "pizza dough, tomato sauce, mozzarella cheese, fresh basil, extra virgin olive oil, sea salt",
     "Roll out pizza dough. Spread rich tomato sauce, top generously with fresh mozzarella slices and fragrant basil leaves. Drizzle olive oil and bake at high heat until bubbling and crust is blistered.",
     20, 10, 2, 780, "vegetarian,dinner,italian"),

    ("Creamy Wild Mushroom Pasta", "Italian",
     "fettuccine pasta, cremini mushrooms, garlic, olive oil, parmesan cheese, heavy cream, fresh parsley, black pepper",
     "Boil fettuccine al dente. Saute sliced mushrooms and minced garlic in olive oil until golden brown. Pour in cream and cracked black pepper, simmer until luscious, toss with pasta and shaved parmesan.",
     10, 15, 2, 620, "vegetarian,dinner,italian,comfort"),

    ("Crispy Paneer Burger", "Fusion",
     "paneer patty, brioche burger buns, crisp lettuce, sliced tomato, spiced mayo, cheddar cheese, onion rings",
     "Coat spiced paneer patty in panko crumbs and shallow fry until crispy golden. Toast burger buns, spread zesty spiced mayo, layer fresh lettuce, tomato, warm crisp paneer patty and cheddar cheese.",
     15, 15, 2, 590, "vegetarian,quick,fusion,street-food"),

    ("Spiced Bean and Corn Tacos", "Mexican",
     "corn taco shells, black beans, sweet corn, avocado, shredded lettuce, cheddar cheese, cumin, salsa, sour cream",
     "Warm black beans and sweet corn with ground cumin and chili. Fill warm taco shells with bean-corn mixture, crisp lettuce, creamy diced avocado, fresh tomato salsa and shredded cheese.",
     15, 10, 4, 430, "vegetarian,mexican,quick,fiber-rich"),

    ("Guacamole", "Mexican",
     "ripe avocado, fresh lime juice, cilantro, red onion, ripe tomato, jalapeno, sea salt",
     "Coarsely mash ripe avocados with freshly squeezed lime juice. Fold in diced red onion, seeded tomato, minced jalapeno and chopped cilantro. Season with sea salt to taste.",
     10, 0, 4, 210, "vegetarian,vegan,appetizer,healthy"),

    ("Chicken Fried Rice", "Chinese",
     "cooked jasmine rice, chicken breast, eggs, soy sauce, green peas, carrots, garlic, spring onions, sesame oil",
     "Scramble eggs and set aside. Stir-fry diced chicken breast with minced garlic, carrots and sweet peas. Add cold cooked rice, soy sauce and eggs. Toss vigorously with toasted sesame oil and green onions.",
     15, 15, 3, 540, "chicken,dinner,quick,chinese"),

    ("Kung Pao Chicken", "Chinese",
     "chicken breast, crunchy peanuts, dried red chilies, soy sauce, garlic, ginger, spring onion, vinegar, szechuan pepper",
     "Stir-fry diced chicken until golden. Toss in garlic, ginger, dried red chilies and szechuan pepper. Pour in savory soy-vinegar glaze, fold in roasted peanuts and sliced spring onions.",
     15, 15, 3, 480, "chicken,dinner,spicy,chinese"),

    ("Mac and Cheese", "American",
     "macaroni pasta, sharp cheddar cheese, milk, butter, flour, crispy breadcrumbs, mustard powder, paprika",
     "Cook macaroni al dente. Prepare a roux with butter and flour, slowly whisk in milk until silky, melt in sharp cheddar cheese. Combine with macaroni, top with breadcrumbs and bake until bubbling.",
     10, 25, 4, 610, "vegetarian,comfort,american"),

    ("Greek Salad", "Greek",
     "crisp cucumber, ripe tomato, red onion, feta cheese, kalamata olives, extra virgin olive oil, dried oregano, lemon juice",
     "Chop fresh cucumber, ripe tomatoes and red onions. Gently toss with briny kalamata olives and cubes of creamy feta cheese. Drizzle generously with olive oil, lemon juice and dried wild oregano.",
     15, 0, 4, 320, "vegetarian,salad,healthy,mediterranean"),

    ("Chicken Souvlaki", "Greek",
     "chicken thigh, fresh lemon, garlic, oregano, olive oil, warm pita bread, tzatziki sauce",
     "Marinate chicken skewers in lemon juice, garlic, olive oil and fragrant wild oregano. Grill over high heat until juicy and charred. Serve inside soft warm pita with cool cucumber tzatziki.",
     20, 15, 4, 480, "chicken,dinner,grill,mediterranean"),

    ("Pad Thai", "Thai",
     "rice noodles, tender tofu, scrambled egg, bean sprouts, crushed peanuts, tamarind paste, lime wedges, scallions",
     "Soak rice noodles until pliable. Stir-fry firm tofu cubes, minced garlic and egg. Add noodles and tangy tamarind sauce. Toss with fresh crunchy bean sprouts, toasted peanuts and lime wedges.",
     20, 15, 3, 520, "vegetarian,thai,seafood-free,noodles"),

    ("Green Curry Chicken", "Thai",
     "chicken breast, thai green curry paste, coconut milk, thai basil, bamboo shoots, eggplants, lime leaves",
     "Fry fragrant green curry paste in coconut cream until aromatic oil separates. Add tender chicken breast slices, diced eggplant and bamboo shoots. Simmer in rich coconut milk, finish with sweet thai basil.",
     15, 20, 4, 510, "chicken,thai,spicy,dinner"),

    ("Ratatouille", "French",
     "eggplant, zucchini, bell peppers, ripe tomatoes, red onion, garlic, fresh thyme, olive oil",
     "Thinly slice colorful zucchini, eggplant and tomatoes. Spread savory garlic tomato sauce in a baking dish, arrange vegetable rounds in alternating spiral pattern, drizzle herb olive oil, bake until tender.",
     25, 45, 4, 240, "vegetarian,vegan,healthy,french"),

    ("Falafel Wrap", "Middle Eastern",
     "soaked chickpeas, fresh parsley, fresh coriander, garlic, cumin, coriander seeds, tahini sauce, pita bread, salad",
     "Coarsely blend chickpeas with fresh herbs, garlic and aromatic spices. Shape into patties and fry crisp. Tuck hot falafels into warm fluffy pita bread with drizzled sesame tahini, tomatoes and pickled cucumbers.",
     20, 15, 4, 430, "vegetarian,vegan,middle-eastern,lunch"),

    ("Hummus with Olive Oil", "Middle Eastern",
     "cooked chickpeas, tahini, freshly squeezed lemon juice, garlic, extra virgin olive oil, ground cumin, paprika",
     "Blend cooked chickpeas, silky tahini, lemon juice, garlic and ground cumin with ice water until ultra-smooth and creamy. Swirl in a bowl, drizzle with robust olive oil and dust with sweet paprika.",
     10, 0, 6, 180, "vegetarian,vegan,appetizer,middle-eastern"),

    ("Vegetarian Miso Ramen", "Japanese",
     "ramen noodles, white miso paste, shiitake mushrooms, soft boiled egg, sweet corn, green scallions, sesame oil, vegetable broth",
     "Simmer rich vegetable broth infused with shiitake mushrooms, ginger and white miso paste. Cook ramen noodles separately. Assemble in deep bowls with savory broth, halved soft-boiled eggs, sweet corn and scallions.",
     20, 20, 2, 490, "vegetarian,japanese,soup,comfort"),

    ("Chicken Teriyaki Rice Bowl", "Japanese",
     "chicken thigh, naturally brewed soy sauce, mirin, raw sugar, fresh ginger, garlic, toasted sesame seeds, steamed rice",
     "Sear tender chicken thigh pieces in a skillet until skin is golden. Glaze with reduced soy sauce, mirin, grated ginger and garlic until glossy. Slice and serve over hot steamed jasmine rice.",
     10, 20, 3, 560, "chicken,japanese,dinner,quick"),

    ("Shakshuka", "Middle Eastern",
     "farm eggs, ripe plum tomatoes, red bell peppers, yellow onion, garlic cloves, ground cumin, smoked paprika, cilantro",
     "Gently saute sliced bell peppers and onions with garlic and warm spices until soft. Simmer with crushed tomatoes until a thick sauce forms. Make small wells, crack fresh eggs into sauce, cover and gently poach.",
     10, 20, 3, 320, "vegetarian,breakfast,middle-eastern,protein"),

    ("Fluffy Buttermilk Pancakes", "American",
     "all purpose flour, buttermilk, fresh eggs, raw sugar, baking powder, pure butter, pure vanilla extract, maple syrup",
     "Whisk dry ingredients in one bowl and buttermilk, eggs and melted butter in another. Fold together gently. Ladle onto a hot buttered griddle, cook until bubbles burst on surface, flip and serve golden with maple syrup.",
     10, 15, 4, 350, "vegetarian,breakfast,american,sweet"),

    ("Caprese Salad", "Italian",
     "ripe vine tomatoes, fresh buffalo mozzarella, fresh basil leaves, extra virgin olive oil, aged balsamic glaze, flake salt",
     "Thickly slice vine-ripened tomatoes and buffalo mozzarella. Shingle attractively with vibrant fresh sweet basil leaves. Drizzle rich extra virgin olive oil, drizzle aged balsamic reduction, finish with flaky sea salt.",
     10, 0, 2, 280, "vegetarian,salad,italian,fresh"),

    ("Golden Yellow Lentil Soup", "Middle Eastern",
     "yellow lentils moong dal, sweet carrots, red onion, ground cumin, garlic cloves, vegetable broth, fresh lemon juice",
     "Saute diced onions, carrots and garlic in olive oil. Stir in yellow lentils, ground cumin and vegetable broth. Simmer until creamy and tender, blend smoothly, finish with freshly squeezed lemon juice and a touch of cumin oil.",
     10, 30, 4, 260, "vegetarian,vegan,soup,healthy")
]


def run():
    db.init_db()
    # Wipe old database to ensure no beef, steak, or pork remnants remain
    conn = db.get_connection()
    conn.execute("DELETE FROM recipes")
    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'recipes'")
    except Exception:
        pass
    conn.commit()
    conn.close()

    for (title, cuisine, ingredients, instructions, prep, cook, servings, calories, tags) in RECIPES:
        db.add_recipe(title, cuisine, ingredients, instructions, prep, cook,
                      servings, calories, tags, cuisine_predicted=0)
    print(f"Successfully seeded {len(RECIPES)} India-compliant recipes (No beef, no steak, no pork).")


if __name__ == "__main__":
    run()
