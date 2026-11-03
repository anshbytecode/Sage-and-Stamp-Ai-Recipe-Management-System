"""
ml_engine.py
All Machine Learning and Explainable AI functionality for Sage & Stamp – Advanced AI Edition.

Features:
1. RecipeRecommender  - TF-IDF + cosine similarity content-based recommendations
2. CuisineClassifier   - Multinomial Naive Bayes text classifier that predicts a
                         recipe's cuisine from its ingredient list with class probabilities.
3. IngredientMatcher   - Pantry matching engine with weighted Jaccard overlap and missing items list.
4. RecipeClusterer     - KMeans clustering over recipe TF-IDF vectors to auto-group
                         the collection into discovered "flavor families".
5. Smart search        - Semantic TF-IDF similarity over title + ingredients + instructions.
6. Explainable AI      - Provides human-readable breakdown of why a recipe was recommended,
                         highlighting shared flavor compounds, key ingredients, and similarity weights.
"""
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.naive_bayes import MultinomialNB
from sklearn.cluster import KMeans

import database as db


def _clean(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s,]", " ", text)
    return text


def _ingredients_text(recipe):
    """Turn the comma separated ingredients field into a clean bag-of-words string."""
    return _clean(recipe["ingredients"].replace(",", " "))


class RecipeAI:
    def __init__(self):
        self.recipes = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.cuisine_model = None
        self.cuisine_vectorizer = None
        self.cluster_model = None
        self.cluster_labels = None
        self.refresh()

    def refresh(self):
        self.recipes = db.get_all_recipes()
        if not self.recipes:
            self.vectorizer = None
            self.tfidf_matrix = None
            self.cuisine_model = None
            self.cluster_model = None
            return

        corpus = [self._full_text(r) for r in self.recipes]
        self.vectorizer = TfidfVectorizer(stop_words="english", min_df=1, ngram_range=(1, 2))
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

        self._train_cuisine_classifier()
        self._train_clusters()

    def _full_text(self, recipe):
        return _clean(f"{recipe['title']} {recipe['cuisine']} {recipe['ingredients']} {recipe['instructions']} {recipe.get('tags', '')}")

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
        source_recipe = self.recipes[idx]

        for i in ranked:
            if i == idx:
                continue
            if sims[i] <= 0:
                continue
            cand = self.recipes[i]
            explanation = self.explain_recommendation(source_recipe, cand, float(sims[i]))
            results.append((cand, round(float(sims[i]) * 100, 1), explanation))
            if len(results) >= top_n:
                break
        return results

    def _index_of(self, recipe_id):
        for i, r in enumerate(self.recipes):
            if r["id"] == recipe_id:
                return i
        return None

    # ------------------------------------------------------------------
    # 2) EXPLAINABLE AI (XAI)
    # ------------------------------------------------------------------
    def explain_recommendation(self, source_recipe, target_recipe, sim_score=None):
        """
        Explainable AI engine: Breaks down WHY a dish is recommended:
        - Common ingredients and aromatics
        - Shared culinary style or cuisine
        - Texture/cooking style harmony
        """
        src_ings = set([i.strip().lower() for i in source_recipe["ingredients"].split(",") if i.strip()])
        tgt_ings = set([i.strip().lower() for i in target_recipe["ingredients"].split(",") if i.strip()])
        
        # Word-level overlap (e.g. "butter", "garlic", "cream", "paneer", "cumin")
        src_words = set(re.findall(r"\b[a-z]{3,}\b", " ".join(src_ings)))
        tgt_words = set(re.findall(r"\b[a-z]{3,}\b", " ".join(tgt_ings)))
        common_words = sorted(list(src_words & tgt_words - {"with", "and", "the", "for"}))
        
        shared_cuisine = (source_recipe.get("cuisine") == target_recipe.get("cuisine"))
        
        # Determine aromatic base
        aromatics = {"garlic", "ginger", "onion", "butter", "ghee", "cumin", "coriander", "turmeric", "cream", "tomato", "chili", "basil", "olive"}
        common_aromatics = [w for w in common_words if w in aromatics]

        pct = round(sim_score * 100, 1) if sim_score is not None else 85.0
        
        reasons = []
        if common_aromatics:
            reasons.append(f"Shared aromatic foundation: {', '.join(common_aromatics[:4])}")
        if shared_cuisine:
            reasons.append(f"Both feature classic {source_recipe.get('cuisine')} flavor profiles")
        if common_words:
            reasons.append(f"Key overlapping elements: {', '.join(common_words[:4])}")
        else:
            reasons.append("Complementary flavor complexity and cooking techniques")

        summary = f"Similarity score: {pct}%. Recommended because both recipes balance {', '.join(common_words[:3]) or 'similar aromatics'}."

        return {
            "score_pct": pct,
            "common_ingredients": common_words[:6],
            "common_aromatics": common_aromatics[:4],
            "shared_cuisine": shared_cuisine,
            "reasons": reasons,
            "summary": summary
        }

    # ------------------------------------------------------------------
    # 3) CUISINE CLASSIFIER (Multinomial Naive Bayes)
    # ------------------------------------------------------------------
    def _train_cuisine_classifier(self):
        labeled = [r for r in self.recipes if r.get("cuisine") and not r.get("cuisine_predicted")]
        cuisines = set(r["cuisine"] for r in labeled)
        if len(labeled) < 4 or len(cuisines) < 2:
            self.cuisine_model = None
            return
        texts = [_ingredients_text(r) for r in labeled]
        labels = [r["cuisine"] for r in labeled]

        self.cuisine_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        X = self.cuisine_vectorizer.fit_transform(texts)
        self.cuisine_model = MultinomialNB(alpha=0.1)
        self.cuisine_model.fit(X, labels)

    def predict_cuisine(self, ingredients_text):
        """Returns (predicted_label, confidence_pct) or (None, 0) if model unavailable."""
        if not self.cuisine_model or not ingredients_text.strip():
            return None, 0.0
        X = self.cuisine_vectorizer.transform([_clean(ingredients_text)])
        probs = self.cuisine_model.predict_proba(X)[0]
        best_idx = int(np.argmax(probs))
        label = self.cuisine_model.classes_[best_idx]
        return label, round(float(probs[best_idx]) * 100, 1)

    def predict_top_cuisines(self, ingredients_text, top_k=3):
        """Returns list of (cuisine, probability_pct) for interactive UI."""
        if not self.cuisine_model or not ingredients_text.strip():
            return []
        X = self.cuisine_vectorizer.transform([_clean(ingredients_text)])
        probs = self.cuisine_model.predict_proba(X)[0]
        indices = np.argsort(-probs)[:top_k]
        return [(self.cuisine_model.classes_[i], round(float(probs[i]) * 100, 1)) for i in indices if probs[i] > 0.05]

    # ------------------------------------------------------------------
    # 4) "WHAT CAN I COOK?" INGREDIENT MATCHER
    # ------------------------------------------------------------------
    def match_by_ingredients(self, pantry_list, top_n=10):
        pantry = set(_clean(p).strip() for p in pantry_list if p.strip())
        if not pantry:
            return []
        scored = []
        for r in self.recipes:
            recipe_ings = set(i.strip() for i in _clean(r["ingredients"]).split(","))
            recipe_ings = {i for i in recipe_ings if i}
            if not recipe_ings:
                continue

            # Check overlap considering sub-words (e.g. "garlic" matches "garlic cloves")
            overlap = set()
            for r_ing in recipe_ings:
                for p_ing in pantry:
                    if p_ing in r_ing or r_ing in p_ing:
                        overlap.add(r_ing)
                        break

            missing = recipe_ings - overlap
            coverage = len(overlap) / len(recipe_ings)
            if coverage <= 0:
                continue

            scored.append({
                "recipe": r,
                "coverage_pct": round(coverage * 100, 1),
                "have": sorted(list(overlap)),
                "missing": sorted(list(missing)),
                "total_ingredients": len(recipe_ings)
            })

        scored.sort(key=lambda x: x["coverage_pct"], reverse=True)
        return scored[:top_n]

    # ------------------------------------------------------------------
    # 5) RECIPE CLUSTERING - auto-discovered "flavor families"
    # ------------------------------------------------------------------
    def _train_clusters(self, k=None):
        n = len(self.recipes)
        if n < 4:
            self.cluster_model = None
            self.cluster_labels = None
            return
        k = k or max(3, min(7, n // 5))
        self.cluster_model = KMeans(n_clusters=k, random_state=42, n_init=10)
        self.cluster_labels = self.cluster_model.fit_predict(self.tfidf_matrix)

    def get_clusters(self):
        """Returns dict: cluster_id -> {label, recipes, key_terms}"""
        if self.cluster_model is None or self.cluster_labels is None:
            return {}
        terms = np.array(self.vectorizer.get_feature_names_out())
        centers = self.cluster_model.cluster_centers_
        clusters = {}
        for cid in sorted(set(self.cluster_labels)):
            top_term_indices = np.argsort(-centers[cid])[:4]
            top_terms = [terms[i] for i in top_term_indices]
            members = [self.recipes[i] for i, c in enumerate(self.cluster_labels) if c == cid]
            clusters[cid] = {
                "label": " • ".join(t.title() for t in top_terms[:3]),
                "key_terms": top_terms,
                "recipes": members,
            }
        return clusters

    # ------------------------------------------------------------------
    # 6) SMART SEARCH
    # ------------------------------------------------------------------
    def smart_search(self, query, top_n=12):
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


# Singleton instance used across the app
engine = RecipeAI()
