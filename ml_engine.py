"""
ml_engine.py
All AI / Machine Learning functionality for the Recipe Management System.

Features implemented:
1. RecipeRecommender  - TF-IDF + cosine similarity content-based recommendations
                         ("recipes similar to this one")
2. CuisineClassifier   - Multinomial Naive Bayes text classifier that predicts a
                         recipe's cuisine from its ingredient list when the user
                         doesn't specify one.
3. IngredientMatcher   - "What can I cook?" - ranks recipes by how well they match
                         a pantry list the user provides (weighted Jaccard overlap).
4. RecipeClusterer     - KMeans clustering over recipe TF-IDF vectors to auto-group
                         the collection into discovered "flavor families".
5. Smart search        - free-text semantic-ish search using TF-IDF similarity over
                         title + ingredients + instructions, instead of plain LIKE.

All models are trained lazily/in-memory from whatever is currently in the database,
so the "AI" stays up to date as recipes are added, with no external services needed.
"""
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.naive_bayes import MultinomialNB
from sklearn.cluster import KMeans

import database as db


def _clean(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s,]", " ", text)
    return text


def _ingredients_text(recipe):
    """Turn the comma separated ingredients field into a clean bag-of-words string."""
    return _clean(recipe["ingredients"].replace(",", " "))


class RecipeAI:
    """
    Wraps all ML models. Call `refresh()` whenever the recipe set changes
    (the Flask app does this after every add/edit/delete) so recommendations
    and predictions always reflect the latest data.
    """

    def __init__(self):
        self.recipes = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.cuisine_model = None
        self.cuisine_vectorizer = None
        self.cluster_model = None
        self.cluster_labels = None
        self.refresh()

    # ------------------------------------------------------------------
    def refresh(self):
        self.recipes = db.get_all_recipes()
        if not self.recipes:
            self.vectorizer = None
            self.tfidf_matrix = None
            self.cuisine_model = None
            self.cluster_model = None
            return

        corpus = [self._full_text(r) for r in self.recipes]
        self.vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

        self._train_cuisine_classifier()
        self._train_clusters()

    def _full_text(self, recipe):
        return _clean(f"{recipe['title']} {recipe['ingredients']} {recipe['instructions']}")

    # ------------------------------------------------------------------
    # 1) CONTENT-BASED RECOMMENDER
    # ------------------------------------------------------------------
    def similar_recipes(self, recipe_id, top_n=4):
        idx = self._index_of(recipe_id)
        if idx is None or self.tfidf_matrix is None:
            return []
        sims = cosine_similarity(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()
        ranked = np.argsort(-sims)
        results = []
        for i in ranked:
            if i == idx:
                continue
            if sims[i] <= 0:
                continue
            results.append((self.recipes[i], round(float(sims[i]) * 100, 1)))
            if len(results) >= top_n:
                break
        return results

    def _index_of(self, recipe_id):
        for i, r in enumerate(self.recipes):
            if r["id"] == recipe_id:
                return i
        return None

    # ------------------------------------------------------------------
    # 2) CUISINE CLASSIFIER (Multinomial Naive Bayes)
    # ------------------------------------------------------------------
    def _train_cuisine_classifier(self):
        labeled = [r for r in self.recipes if r.get("cuisine") and not r.get("cuisine_predicted")]
        cuisines = set(r["cuisine"] for r in labeled)
        if len(labeled) < 4 or len(cuisines) < 2:
            self.cuisine_model = None
            return
        texts = [_ingredients_text(r) for r in labeled]
        labels = [r["cuisine"] for r in labeled]
        self.cuisine_vectorizer = TfidfVectorizer(stop_words="english")
        X = self.cuisine_vectorizer.fit_transform(texts)
        self.cuisine_model = MultinomialNB()
        self.cuisine_model.fit(X, labels)

    def predict_cuisine(self, ingredients_text):
        """Returns (predicted_label, confidence_pct) or (None, 0) if model unavailable."""
        if not self.cuisine_model:
            return None, 0.0
        X = self.cuisine_vectorizer.transform([_clean(ingredients_text)])
        probs = self.cuisine_model.predict_proba(X)[0]
        best_idx = int(np.argmax(probs))
        label = self.cuisine_model.classes_[best_idx]
        return label, round(float(probs[best_idx]) * 100, 1)

    # ------------------------------------------------------------------
    # 3) "WHAT CAN I COOK?" INGREDIENT MATCHER
    # ------------------------------------------------------------------
    def match_by_ingredients(self, pantry_list, top_n=8):
        pantry = set(_clean(p).strip() for p in pantry_list if p.strip())
        if not pantry:
            return []
        scored = []
        for r in self.recipes:
            recipe_ings = set(i.strip() for i in _clean(r["ingredients"]).split(","))
            recipe_ings = {i for i in recipe_ings if i}
            if not recipe_ings:
                continue
            overlap = pantry & recipe_ings
            missing = recipe_ings - pantry
            # weighted score: reward high coverage of the recipe's ingredient list
            coverage = len(overlap) / len(recipe_ings)
            if coverage <= 0:
                continue
            scored.append({
                "recipe": r,
                "coverage_pct": round(coverage * 100, 1),
                "have": sorted(overlap),
                "missing": sorted(missing),
            })
        scored.sort(key=lambda x: x["coverage_pct"], reverse=True)
        return scored[:top_n]

    # ------------------------------------------------------------------
    # 4) RECIPE CLUSTERING - auto-discovered "flavor families"
    # ------------------------------------------------------------------
    def _train_clusters(self, k=None):
        n = len(self.recipes)
        if n < 4:
            self.cluster_model = None
            self.cluster_labels = None
            return
        k = k or max(2, min(6, n // 4))
        self.cluster_model = KMeans(n_clusters=k, random_state=42, n_init=10)
        self.cluster_labels = self.cluster_model.fit_predict(self.tfidf_matrix)

    def get_clusters(self):
        """Returns dict: cluster_id -> {label, recipes}"""
        if self.cluster_model is None:
            return {}
        terms = np.array(self.vectorizer.get_feature_names_out())
        centers = self.cluster_model.cluster_centers_
        clusters = {}
        for cid in sorted(set(self.cluster_labels)):
            top_terms = terms[np.argsort(-centers[cid])[:3]]
            members = [self.recipes[i] for i, c in enumerate(self.cluster_labels) if c == cid]
            clusters[cid] = {
                "label": " / ".join(t.title() for t in top_terms),
                "recipes": members,
            }
        return clusters

    # ------------------------------------------------------------------
    # 5) SMART SEARCH
    # ------------------------------------------------------------------
    def smart_search(self, query, top_n=10):
        if not query.strip() or self.tfidf_matrix is None:
            return []
        q_vec = self.vectorizer.transform([_clean(query)])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        ranked = np.argsort(-sims)
        results = []
        for i in ranked:
            if sims[i] <= 0:
                break
            results.append((self.recipes[i], round(float(sims[i]) * 100, 1)))
            if len(results) >= top_n:
                break
        return results


# Singleton instance used by the Flask app
engine = RecipeAI()
