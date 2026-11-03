"""
app.py
Sage & Stamp – Culinary Intelligence & Advanced AI Platform.
Features:
- Exact faithful reproduction of the user's interface, header, status badges, and dual navigation.
- Strict 100% India compliance (Zero beef, steak, cow meat, or pork).
- Complete Machine Learning suite (TF-IDF, Naive Bayes, K-Means, Jaccard Pantry Matcher, Explainable AI).
- Generative AI (Conversational Chef Sage AI, Recipe Generation from Pantry, Recipe Modifications).
- RAG System (PDF & Text cookbook upload, chunking, embeddings, and cited Q&A).
- Agentic AI & MCP Console (4 specialized agents + Orchestrator + Model Context Protocol tool execution).
- Food Vision (Image recognition, dominant chromatic tones, ingredient identification).
- Smart Grocery Assistant (Aisle-categorized shopping lists with pantry deduction).
- Compare Dishes, Culinary Badges, Collections, Budget & Prep, and Sustainability trackers.
"""
import os
import json
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session

import database as db
from ml_engine import engine
from genai_engine import genai_engine
from rag_engine import rag_engine, COOKBOOK_DIR
from agent_engine import agent_orchestrator, execute_mcp_tool, MCP_TOOLS_SPEC
from vision_engine import vision_engine
from grocery_engine import grocery_assistant
from cicd_engine import cicd_engine

app = Flask(__name__)
app.secret_key = "sage-stamp-advanced-intelligence-key"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def split_csv(text):
    return [t.strip() for t in text.split(",") if t.strip()]


@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    user = None
    if user_id:
        user = db.get_user_by_id(user_id)
    if not user:
        user = db.get_user_by_email("anshul@example.com")
    if user:
        saved_list = [int(x) for x in user["saved_recipes"].split(",") if x.strip()]
        user["saved_count"] = len(saved_list)
    return {"current_user": user}


# ------------------------------------------------------------------
# AUTH & PROFILE ROUTES (Signup, Login, Profile)
# ------------------------------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        palate = request.form.get("palate", "North Indian & Mediterranean").strip()
        diet_pref = request.form.get("diet_pref", "Vegetarian").strip()

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("signup.html", name=name, email=email)

        try:
            new_uid = db.create_user(name, email, password, palate, diet_pref)
            session["user_id"] = new_uid
            session["logged_in"] = True
            flash(f"Welcome to Sage & Stamp, {name}! Your palate has been initialized.", "success")
            return redirect(url_for("home"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template("signup.html", name=name, email=email)

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        user = db.verify_user(email, password)
        if user:
            session["user_id"] = user["id"]
            session["logged_in"] = True
            flash(f"Welcome back, {user['name'].split()[0]}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template("login.html", email=email)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("logged_in", None)
    flash("You have been safely logged out.", "info")
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    user = db.get_user_by_id(user_id) if user_id else db.get_user_by_email("anshul@example.com")
    if not user:
        flash("Please log in to access your profile.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", user["name"]).strip()
        palate = request.form.get("palate", user["palate"]).strip()
        diet_pref = request.form.get("diet_pref", user["diet_pref"]).strip()
        healthy_affinity = int(request.form.get("healthy_affinity") or user["healthy_affinity"])
        spicy_affinity = int(request.form.get("spicy_affinity") or user["spicy_affinity"])
        quick_affinity = int(request.form.get("quick_affinity") or user["quick_affinity"])

        db.update_user_profile(
            user["id"],
            name=name,
            palate=palate,
            diet_pref=diet_pref,
            healthy_affinity=healthy_affinity,
            spicy_affinity=spicy_affinity,
            quick_affinity=quick_affinity
        )
        flash("Your profile and palate model have been updated!", "success")
        return redirect(url_for("profile"))

    saved_ids = [int(x) for x in user["saved_recipes"].split(",") if x.strip()]
    saved_recipes = [db.get_recipe(rid) for rid in saved_ids if db.get_recipe(rid)]

    return render_template("profile.html", user=user, saved_recipes=saved_recipes)


@app.route("/recipe/<int:recipe_id>/save", methods=["POST"])
def save_recipe(recipe_id):
    user_id = session.get("user_id")
    user = db.get_user_by_id(user_id) if user_id else db.get_user_by_email("anshul@example.com")
    if not user:
        return jsonify({"error": "User not found"}), 404

    is_saved, count = db.toggle_save_recipe(user["id"], recipe_id)
    msg = "Saved to favorites!" if is_saved else "Removed from favorites."
    return jsonify({"saved": is_saved, "count": count, "message": msg})


@app.route("/recipe/<int:recipe_id>/cook", methods=["POST"])
def cook_recipe(recipe_id):
    user_id = session.get("user_id")
    user = db.get_user_by_id(user_id) if user_id else db.get_user_by_email("anshul@example.com")
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_count = db.increment_cooked(user["id"])
    return jsonify({"cooked_count": new_count, "message": "Marked as cooked! Palate model updated."})


# ------------------------------------------------------------------
# 1. RECIPE BOX & DASHBOARD (Home Page)
# ------------------------------------------------------------------
@app.route("/")
def home():
    query = request.args.get("q", "").strip()
    selected_goal = request.args.get("goal", "").strip()
    all_recipes = db.get_all_recipes()

    # Search ranking
    if query:
        ranked = engine.smart_search(query)
        recipes = [r for r, score in ranked]
        scores = {r["id"]: score for r, score in ranked}
    else:
        recipes = all_recipes
        scores = {}

    # Goal Filters matching screenshot
    if selected_goal:
        g_lower = selected_goal.lower()
        if g_lower == "high protein":
            recipes = [r for r in recipes if any(k in r["ingredients"].lower() for k in ["paneer", "chicken", "mutton", "chana", "chickpeas", "rajma", "lentils", "dal", "tofu", "egg"])]
        elif g_lower == "low calorie":
            recipes = [r for r in recipes if (r.get("calories") or 500) <= 380]
        elif g_lower == "quick meals":
            recipes = [r for r in recipes if (r.get("prep_time", 15) + r.get("cook_time", 15)) <= 30]
        elif g_lower == "budget meals":
            recipes = [r for r in recipes if any(k in r["ingredients"].lower() for k in ["potato", "lentils", "poha", "flour", "rice", "dal"])]
        elif g_lower == "vegetarian":
            recipes = [r for r in recipes if "vegetarian" in r.get("tags", "").lower() or "paneer" in r.get("ingredients", "").lower()]
        elif g_lower == "vegan":
            recipes = [r for r in recipes if "vegan" in r.get("tags", "").lower()]
        elif g_lower == "high fiber":
            recipes = [r for r in recipes if any(k in r["ingredients"].lower() for k in ["beans", "rajma", "chickpeas", "spinach", "eggplant", "cauliflower", "lentils"])]
        elif g_lower == "breakfast":
            recipes = [r for r in recipes if "breakfast" in r.get("tags", "").lower() or any(k in r["title"].lower() for k in ["dosa", "poha", "dhokla", "pancakes", "shakshuka"])]
        elif g_lower == "weight-management":
            recipes = [r for r in recipes if (r.get("calories") or 500) <= 350 or "healthy" in r.get("tags", "").lower()]

    return render_template("index.html", recipes=recipes, query=query,
                           scores=scores, total=len(all_recipes),
                           selected_goal=selected_goal)


@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    recipe = db.get_recipe(recipe_id)
    if not recipe:
        flash("Recipe not found.", "error")
        return redirect(url_for("home"))

    similar = engine.similar_recipes(recipe_id, top_n=4)
    nutrition_expl = genai_engine.explain_nutrition(recipe)

    return render_template("recipe_detail.html", recipe=recipe, similar=similar,
                           nutrition=nutrition_expl)


@app.route("/add", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        title = request.form["title"].strip()
        cuisine = request.form.get("cuisine", "").strip()
        ingredients = request.form["ingredients"].strip()
        instructions = request.form["instructions"].strip()

        prep_time = int(request.form.get("prep_time") or 0)
        cook_time = int(request.form.get("cook_time") or 0)
        servings = int(request.form.get("servings") or 4)

        calories = request.form.get("calories") or None
        calories = int(calories) if calories else None
        tags = request.form.get("tags", "").strip()

        # India-cultural & dietary compliance check
        is_safe, warn_msg = db.check_dietary_compliance(title, ingredients)
        if not is_safe:
            flash(warn_msg, "error")
            return render_template("add_recipe.html", recipe=request.form)

        cuisine_predicted = 0
        prediction_note = None
        if not cuisine:
            predicted, confidence = engine.predict_cuisine(ingredients)
            if predicted:
                cuisine = predicted
                cuisine_predicted = 1
                prediction_note = f"AI predicted cuisine: {predicted} ({confidence}% confidence)"
            else:
                cuisine = "Other"

        try:
            new_id = db.add_recipe(title, cuisine, ingredients, instructions, prep_time,
                                   cook_time, servings, calories, tags, cuisine_predicted)
            engine.refresh()

            if prediction_note:
                flash(prediction_note, "info")
            flash(f'"{title}" added successfully!', "success")
            return redirect(url_for("recipe_detail", recipe_id=new_id))
        except ValueError as e:
            flash(str(e), "error")
            return render_template("add_recipe.html", recipe=request.form)

    return render_template("add_recipe.html", recipe=None)


@app.route("/edit/<int:recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    recipe = db.get_recipe(recipe_id)
    if not recipe:
        flash("Recipe not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form["title"].strip()
        ingredients = request.form["ingredients"].strip()

        # India compliance check
        is_safe, warn_msg = db.check_dietary_compliance(title, ingredients)
        if not is_safe:
            flash(warn_msg, "error")
            return render_template("add_recipe.html", recipe=request.form)

        calories = request.form.get("calories") or None
        try:
            db.update_recipe(
                recipe_id,
                title=title,
                cuisine=request.form.get("cuisine", "").strip() or "Other",
                ingredients=ingredients,
                instructions=request.form["instructions"].strip(),
                prep_time=int(request.form.get("prep_time") or 0),
                cook_time=int(request.form.get("cook_time") or 0),
                servings=int(request.form.get("servings") or 4),
                calories=int(calories) if calories else None,
                tags=request.form.get("tags", "").strip(),
                cuisine_predicted=0,
            )
            engine.refresh()
            flash("Recipe updated.", "success")
            return redirect(url_for("recipe_detail", recipe_id=recipe_id))
        except ValueError as e:
            flash(str(e), "error")
            return render_template("add_recipe.html", recipe=request.form)

    return render_template("add_recipe.html", recipe=recipe)


@app.route("/delete/<int:recipe_id>", methods=["POST"])
def delete_recipe(recipe_id):
    db.delete_recipe(recipe_id)
    engine.refresh()
    flash("Recipe deleted.", "success")
    return redirect(url_for("home"))


@app.route("/cook-with", methods=["GET", "POST"])
def cook_with():
    results = None
    pantry_text = ""
    if request.method == "POST":
        pantry_text = request.form.get("pantry", "")
        pantry_list = split_csv(pantry_text)
        results = engine.match_by_ingredients(pantry_list)
    return render_template("cook_with.html", results=results, pantry_text=pantry_text)


@app.route("/discover")
def discover():
    clusters = engine.get_clusters()
    return render_template("discover.html", clusters=clusters)


# ------------------------------------------------------------------
# 2. SAGE AI ASSISTANT & GENAI STUDIO
# ------------------------------------------------------------------
@app.route("/genai", methods=["GET", "POST"])
def genai_studio():
    generated_recipe = None
    modified_recipe = None
    all_recipes = db.get_all_recipes()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "generate":
            pantry = request.form.get("pantry", "paneer, tomatoes, garam masala, cream")
            cuisine = request.form.get("cuisine", "North Indian")
            diet = request.form.get("diet", "Vegetarian")
            generated_recipe = genai_engine.generate_recipe_from_ingredients(pantry, cuisine, diet)

        elif action == "modify":
            rec_id = int(request.form.get("recipe_id", 1))
            mod_type = request.form.get("mod_type", "make it spicy")
            base_rec = db.get_recipe(rec_id)
            if base_rec:
                modified_recipe = genai_engine.modify_recipe(base_rec, mod_type)

        elif action == "save_ai_recipe":
            title = request.form.get("title")
            cuisine = request.form.get("cuisine", "Fusion")
            ingredients = request.form.get("ingredients")
            instructions = request.form.get("instructions")
            calories = int(request.form.get("calories") or 400)
            prep_time = int(request.form.get("prep_time") or 15)
            cook_time = int(request.form.get("cook_time") or 20)
            tags = request.form.get("tags", "genai,ai-created,vegetarian")
            try:
                new_id = db.add_recipe(title, cuisine, ingredients, instructions, prep_time, cook_time, 4, calories, tags, cuisine_predicted=0)
                engine.refresh()
                flash(f"✨ AI Recipe '{title}' saved to your Recipe Box!", "success")
                return redirect(url_for("recipe_detail", recipe_id=new_id))
            except ValueError as e:
                flash(str(e), "error")

    return render_template("genai.html", generated=generated_recipe,
                           modified=modified_recipe, recipes=all_recipes)


@app.route("/assistant", methods=["GET", "POST"])
def assistant():
    generated_recipe = None
    modified_recipe = None
    all_recipes = db.get_all_recipes()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "generate":
            pantry = request.form.get("pantry", "paneer, tomatoes, garam masala, cream")
            cuisine = request.form.get("cuisine", "North Indian")
            diet = request.form.get("diet", "Vegetarian")
            generated_recipe = genai_engine.generate_recipe_from_ingredients(pantry, cuisine, diet)

        elif action == "modify":
            rec_id = int(request.form.get("recipe_id", 1))
            mod_type = request.form.get("mod_type", "make it spicy")
            base_rec = db.get_recipe(rec_id)
            if base_rec:
                modified_recipe = genai_engine.modify_recipe(base_rec, mod_type)

    return render_template("assistant.html", generated=generated_recipe,
                           modified=modified_recipe, recipes=all_recipes)


# ------------------------------------------------------------------
# 3. COMPARE RECIPES
# ------------------------------------------------------------------
@app.route("/compare", methods=["GET", "POST"])
def compare_recipes():
    all_recipes = db.get_all_recipes()
    r1_id = int(request.args.get("r1") or (all_recipes[0]["id"] if all_recipes else 1))
    r2_id = int(request.args.get("r2") or (all_recipes[1]["id"] if len(all_recipes) > 1 else 1))

    r1 = db.get_recipe(r1_id)
    r2 = db.get_recipe(r2_id)

    return render_template("compare.html", recipes=all_recipes, r1=r1, r2=r2)


# ------------------------------------------------------------------
# 4. BADGES VIEW
# ------------------------------------------------------------------
@app.route("/badges")
def badges_view():
    all_recipes = db.get_all_recipes()
    badges = [
        {"icon": "🛡️", "title": "India Dietary Guardian", "desc": "100% adherence to cultural harmony (Strictly Zero Beef & Pork)", "unlocked": True},
        {"icon": "🌶️", "title": "Spice Alchemist", "desc": "Mastered complex tadka and whole spice blooming", "unlocked": True},
        {"icon": "⏱️", "title": "Flash Gourmet", "desc": "Cooked 5-star meals in under 25 minutes", "unlocked": True},
        {"icon": "🌿", "title": "Ayurvedic Harmonizer", "desc": "Balanced Tridosha (Vata, Pitta, Kapha) with gut-friendly herbs", "unlocked": True},
        {"icon": "🌾", "title": "Legume & Grain Connoisseur", "desc": "Mastered slow-simmered Dal Makhani and Dum Biryani", "unlocked": True},
        {"icon": "🧀", "title": "Paneer Maestro", "desc": "Mastered keeping fresh cottage cheese ultra-soft and supple", "unlocked": True}
    ]
    return render_template("badges.html", badges=badges, total_recipes=len(all_recipes))


# ------------------------------------------------------------------
# 5. COLLECTIONS VIEW
# ------------------------------------------------------------------
@app.route("/collections")
def collections_view():
    all_recipes = db.get_all_recipes()
    collections = [
        {
            "name": "Royal Awadhi & Mughlai Durbari",
            "desc": "Rich slow-cooked gravies with cashews, saffron, and aromatic dum layering.",
            "recipes": [r for r in all_recipes if any(k in r["cuisine"].lower() for k in ["north indian", "mughlai", "awadhi", "kashmiri", "hyderabadi"])][:4]
        },
        {
            "name": "South Indian Crispy & Fermented",
            "desc": "Crisp dosas, fluffy fermented idlis, and mustard seed tempered sambars.",
            "recipes": [r for r in all_recipes if "south indian" in r["cuisine"].lower() or "dosa" in r["title"].lower()][:4]
        },
        {
            "name": "15-Minute Lightning Dinners",
            "desc": "Wholesome, vibrant weeknight dinners ready in 25 minutes or less.",
            "recipes": [r for r in all_recipes if (r.get("prep_time", 15) + r.get("cook_time", 15)) <= 25][:4]
        },
        {
            "name": "Global Vegetarian Tapas & Mains",
            "desc": "India-compliant international classics from Italy, Mexico, and Greece.",
            "recipes": [r for r in all_recipes if r["cuisine"] in ["Italian", "Mexican", "Greek", "Middle Eastern", "Thai"]][:4]
        }
    ]
    return render_template("collections.html", collections=collections)


# ------------------------------------------------------------------
# 6. BUDGET & PREP VIEW
# ------------------------------------------------------------------
@app.route("/budget-prep")
def budget_prep_view():
    all_recipes = db.get_all_recipes()
    return render_template("budget_prep.html", recipes=all_recipes)


# ------------------------------------------------------------------
# 7. SUSTAINABILITY VIEW
# ------------------------------------------------------------------
@app.route("/sustainability")
def sustainability_view():
    all_recipes = db.get_all_recipes()
    veg_ratio = sum(1 for r in all_recipes if "vegetarian" in r.get("tags", "").lower() or "paneer" in r.get("ingredients", "").lower()) / max(1, len(all_recipes))
    co2_saved_kg = round(len(all_recipes) * 3.8 * veg_ratio, 1)
    water_saved_liters = round(len(all_recipes) * 1250 * veg_ratio)

    return render_template("sustainability.html",
                           co2_saved=co2_saved_kg,
                           water_saved=water_saved_liters,
                           veg_pct=round(veg_ratio * 100, 1))


# ------------------------------------------------------------------
# 8. GRAPH & SENTIMENT VIEW
# ------------------------------------------------------------------
@app.route("/graph-sentiment")
def graph_sentiment_view():
    return render_template("graph_sentiment.html")


# ------------------------------------------------------------------
# 9. CI/CD PIPELINE & DEVOPS OBSERVABILITY
# ------------------------------------------------------------------
@app.route("/cicd")
def cicd_view():
    pipeline_result = cicd_engine.run_pipeline()
    workflow_path = os.path.join(os.path.dirname(__file__), ".github", "workflows", "ci-cd.yml")
    workflow_yaml = ""
    if os.path.exists(workflow_path):
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow_yaml = f.read()
    return render_template("cicd.html", pipeline=pipeline_result, workflow_yaml=workflow_yaml)


@app.route("/api/cicd/trigger", methods=["POST"])
def api_cicd_trigger():
    result = cicd_engine.run_pipeline()
    return jsonify(result)


# ------------------------------------------------------------------
# 9. RAG COOKBOOK ASSISTANT (Section C)
# ------------------------------------------------------------------
@app.route("/rag-cookbooks", methods=["GET", "POST"])
def rag_cookbooks():
    qa_result = None
    question = ""

    if request.method == "POST":
        if "cookbook_file" in request.files:
            file = request.files["cookbook_file"]
            if file and file.filename:
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)
                doc_meta = rag_engine.ingest_document(save_path, filename)
                flash(f"Successfully ingested '{filename}' ({doc_meta['chunks_count']} chunks indexed into vector store).", "success")

        elif "question" in request.form:
            question = request.form.get("question", "").strip()
            if question:
                qa_result = rag_engine.query(question)

    return render_template("rag_cookbooks.html",
                           documents=rag_engine.documents,
                           total_chunks=len(rag_engine.vector_store.chunks),
                           qa_result=qa_result,
                           question=question)


# ------------------------------------------------------------------
# 10. AGENTIC AI MEAL PLANNER & MCP (Section D)
# ------------------------------------------------------------------
@app.route("/meal-planner", methods=["GET", "POST"])
def meal_planner():
    weekly_plan = None
    target_cals = request.form.get("calories", "2000")
    diet = request.form.get("diet", "Vegetarian")
    cuisine = request.form.get("cuisine", "Any")

    if request.method == "POST":
        prefs = {
            "calories": int(target_cals),
            "diet": diet,
            "cuisine": cuisine,
            "allergies": request.form.getlist("allergies")
        }
        weekly_plan = agent_orchestrator.generate_weekly_plan(prefs)

    if not weekly_plan:
        weekly_plan = agent_orchestrator.generate_weekly_plan({"calories": 2000, "diet": "Vegetarian", "cuisine": "Any"})

    return render_template("meal_planner.html", plan=weekly_plan,
                           target_cals=target_cals, diet=diet, cuisine=cuisine)


@app.route("/agents")
def agents_dashboard():
    all_recipes = db.get_all_recipes()
    sample_mcp_output = execute_mcp_tool("mcp_allergy_scanner", {"ingredients": "paneer, butter, cashew nuts, garlic"})
    return render_template("agents.html", tools=MCP_TOOLS_SPEC,
                           sample_mcp=sample_mcp_output,
                           recipe_count=len(all_recipes))


# ------------------------------------------------------------------
# 11. FOOD VISION (Section E)
# ------------------------------------------------------------------
@app.route("/food-vision", methods=["GET", "POST"])
def food_vision():
    analysis = None
    samples = vision_engine.get_sample_gallery()

    if request.method == "POST":
        sample_id = request.form.get("sample_id")
        if sample_id:
            analysis = vision_engine.analyze_food_image(sample_id=sample_id)
        elif "photo" in request.files:
            file = request.files["photo"]
            if file and file.filename:
                fn = secure_filename(file.filename)
                analysis = vision_engine.analyze_food_image(filename=fn)

    if not analysis:
        analysis = vision_engine.analyze_food_image(sample_id="paneer_butter_masala")

    return render_template("food_vision.html", analysis=analysis, samples=samples)


# ------------------------------------------------------------------
# 12. AI GROCERY ASSISTANT (Section 6)
# ------------------------------------------------------------------
@app.route("/grocery", methods=["GET", "POST"])
def grocery():
    all_recipes = db.get_all_recipes()
    selected_ids = []
    pantry_text = "cumin, salt, turmeric, water, cooking oil"

    if request.method == "POST":
        selected_ids = [int(rid) for rid in request.form.getlist("recipe_ids")]
        pantry_text = request.form.get("pantry", pantry_text)
    else:
        selected_ids = [r["id"] for r in all_recipes[:3]]

    shopping_list = grocery_assistant.generate_shopping_list(selected_ids, pantry_text)

    return render_template("grocery.html", shopping=shopping_list,
                           recipes=all_recipes, selected_ids=selected_ids,
                           pantry_text=pantry_text)


# ------------------------------------------------------------------
# 13. NUTRITION DASHBOARD
# ------------------------------------------------------------------
@app.route("/nutrition")
def nutrition_dashboard():
    recipes = db.get_all_recipes()
    veg_count = sum(1 for r in recipes if "vegetarian" in r.get("tags", "").lower() or "paneer" in r.get("ingredients", "").lower())
    non_veg_count = len(recipes) - veg_count
    avg_calories = int(sum(r.get("calories", 400) for r in recipes) / max(1, len(recipes)))

    return render_template("nutrition.html", recipes=recipes,
                           veg_count=veg_count, non_veg_count=non_veg_count,
                           avg_calories=avg_calories)


# ------------------------------------------------------------------
# REST JSON APIS
# ------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "")
    res = genai_engine.chat_assistant(message)
    return jsonify(res)


@app.route("/api/predict-cuisine", methods=["POST"])
def api_predict_cuisine():
    data = request.get_json() or {}
    ingredients = data.get("ingredients", "")
    predictions = engine.predict_top_cuisines(ingredients)
    return jsonify({"predictions": predictions})


@app.route("/api/rag/ask", methods=["POST"])
def api_rag_ask():
    data = request.get_json() or {}
    q = data.get("question", "")
    result = rag_engine.query(q)
    return jsonify(result)


@app.route("/api/mcp/execute", methods=["POST"])
def api_mcp_execute():
    data = request.get_json() or {}
    tool_name = data.get("tool_name", "")
    arguments = data.get("arguments", {})
    res = execute_mcp_tool(tool_name, arguments)
    return jsonify(res)


if __name__ == "__main__":
    db.init_db()
    engine.refresh()
    app.run(debug=True, host="127.0.0.1", port=5000)
