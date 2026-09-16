"""
app.py
Flask web application for the AI-powered Recipe Management System.
Run with: python app.py   then open http://127.0.0.1:5000
"""
from flask import Flask, render_template, request, redirect, url_for, flash

import database as db
from ml_engine import engine

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"


def split_csv(text):
    return [t.strip() for t in text.split(",") if t.strip()]


@app.route("/")
def home():
    query = request.args.get("q", "").strip()
    all_recipes = db.get_all_recipes()

    if query:
        ranked = engine.smart_search(query)
        recipes = [r for r, score in ranked]
        scores = {r["id"]: score for r, score in ranked}
    else:
        recipes = all_recipes
        scores = {}

    return render_template("index.html", recipes=recipes, query=query,
                            scores=scores, total=len(all_recipes))


@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    recipe = db.get_recipe(recipe_id)
    if not recipe:
        flash("Recipe not found.", "error")
        return redirect(url_for("home"))
    similar = engine.similar_recipes(recipe_id, top_n=4)
    return render_template("recipe_detail.html", recipe=recipe, similar=similar)


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

        new_id = db.add_recipe(title, cuisine, ingredients, instructions, prep_time,
                                cook_time, servings, calories, tags, cuisine_predicted)
        engine.refresh()

        if prediction_note:
            flash(prediction_note, "info")
        flash(f'"{title}" added successfully!', "success")
        return redirect(url_for("recipe_detail", recipe_id=new_id))

    return render_template("add_recipe.html", recipe=None)


@app.route("/edit/<int:recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    recipe = db.get_recipe(recipe_id)
    if not recipe:
        flash("Recipe not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        calories = request.form.get("calories") or None
        db.update_recipe(
            recipe_id,
            title=request.form["title"].strip(),
            cuisine=request.form.get("cuisine", "").strip() or "Other",
            ingredients=request.form["ingredients"].strip(),
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


if __name__ == "__main__":
    db.init_db()
    engine.refresh()
    app.run(debug=True, host="127.0.0.1", port=5000)
