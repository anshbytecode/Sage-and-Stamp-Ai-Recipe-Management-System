"""
test_app.py
Comprehensive verification test suite for Sage & Stamp – Advanced AI Edition.
Tests Auth (Signup, Login, Logout, Profile), ML, GenAI, RAG, and Dietary Compliance.
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import app as application
import database as db

client = application.app.test_client()

print("========================================")
print("RUNNING SAGE & STAMP VERIFICATION TESTS")
print("========================================")

# 1. Cultural & Dietary Compliance
print("\n[1] Checking Dietary & Cultural Compliance...")
recipes = db.get_all_recipes()
prohibited_found = []
for r in recipes:
    is_safe, msg = db.check_dietary_compliance(r["title"], r["ingredients"])
    if not is_safe:
        prohibited_found.append((r["title"], msg))

assert len(prohibited_found) == 0, f"Found prohibited dishes: {prohibited_found}"
print(f"[OK] All {len(recipes)} recipes are 100% India-compliant (No beef, steak, or pork).")

# 2. Check Footer Copyright
print("\n[2] Checking Footer Copyright...")
home_res = client.get("/")
home_html = home_res.get_data(as_text=True)
assert "© 2025 Anshul Bhilare. All rights reserved." in home_html or "&copy; 2025 Anshul Bhilare. All rights reserved." in home_html
print("[OK] Footer correctly reflects '© 2025 Anshul Bhilare. All rights reserved.'")

# 3. Check Top Header for Auth Links
print("\n[3] Checking Top Navigation Header for Auth Links...")
assert "Log In" in home_html or "Sign Up" in home_html or "Logout" in home_html
print("[OK] Header includes top Sign Up / Log In / Profile access.")

# 4. Test Authentication & User Profiles
print("\n[4] Testing Signup, Login, and Profile...")
# Login with default Anshul account
login_res = client.post("/login", data={"email": "anshul@example.com", "password": "password123"}, follow_redirects=True)
assert login_res.status_code == 200
login_html = login_res.get_data(as_text=True)
assert "Welcome" in login_html
print("[OK] Login successful for 'anshul@example.com'.")

# Check Profile Page
profile_res = client.get("/profile")
assert profile_res.status_code == 200
profile_html = profile_res.get_data(as_text=True)
assert "Palate Profile" in profile_html
print("[OK] Profile page renders modeled palate and statistics.")

# Test Profile Update
update_res = client.post("/profile", data={
    "name": "Anshul Bhilare",
    "palate": "North Indian & Awadhi",
    "diet_pref": "Vegetarian",
    "healthy_affinity": 100,
    "spicy_affinity": 55,
    "quick_affinity": 100
}, follow_redirects=True)
assert update_res.status_code == 200
print("[OK] Profile preferences updated successfully.")

# Test Save Recipe & Cook Recipe
save_res = client.post("/recipe/1/save")
assert save_res.status_code == 200 and "saved" in save_res.get_json()
print(f"[OK] Recipe save toggle: {save_res.get_json()['message']}")

cook_res = client.post("/recipe/1/cook")
assert cook_res.status_code == 200 and "cooked_count" in cook_res.get_json()
print(f"[OK] Recipe cook action: {cook_res.get_json()['message']}")

# Test Signup new user
new_email = "testuser_99@example.com"
# ensure clean
conn = db.get_connection()
conn.execute("DELETE FROM users WHERE email = ?", (new_email,))
conn.commit()
conn.close()

signup_res = client.post("/signup", data={
    "name": "Chef Rahul",
    "email": new_email,
    "password": "mypassword123",
    "palate": "South Indian Coastal",
    "diet_pref": "Vegetarian"
}, follow_redirects=True)
assert signup_res.status_code == 200
print(f"[OK] Signup successful for new user '{new_email}'.")

# Test Logout
logout_res = client.get("/logout", follow_redirects=True)
assert logout_res.status_code == 200
print("[OK] Logout successful.")

# 5. Test Web Endpoints
print("\n[5] Testing Web Page Endpoints...")
routes_to_test = [
    ("/", "Recipe Box & Dashboard"),
    ("/recipe/1", "Recipe Detail View"),
    ("/genai", "GenAI Recipe Studio"),
    ("/login", "Login Page"),
    ("/signup", "Signup Page"),
    ("/profile", "Profile Page"),
    ("/assistant", "SAGE AI Chef Assistant"),
    ("/compare", "Compare Recipes View"),
    ("/cook-with", "Pantry Ingredient Matcher"),
    ("/badges", "Culinary Badges"),
    ("/collections", "Curated Collections"),
    ("/meal-planner", "AI Meal Planner"),
    ("/nutrition", "Nutrition AI Dashboard"),
    ("/budget-prep", "Budget & Meal Prep"),
    ("/sustainability", "Sustainability Tracker"),
    ("/agents", "ML Suite & MCP Console"),
    ("/food-vision", "Vision AI (Food Recognition)"),
    ("/graph-sentiment", "Graph & Sentiment View"),
    ("/rag-cookbooks", "RAG Cookbook Assistant"),
    ("/grocery", "Smart Grocery Assistant"),
    ("/discover", "Discover Flavor Families"),
    ("/cicd", "CI/CD & DevOps Pipeline View"),
    ("/add", "Add Recipe Form")
]

for path, desc in routes_to_test:
    res = client.get(path)
    assert res.status_code == 200, f"Failed route {path} with status {res.status_code}"
    print(f"[OK] [200] {desc} ({path})")

# 6. Test Live CI/CD Pipeline Execution API
print("\n[6] Testing Live CI/CD Pipeline Trigger API...")
pipe_res = client.post("/api/cicd/trigger")
assert pipe_res.status_code == 200
pdata = pipe_res.get_json()
assert pdata["status"] == "SUCCESS"
assert len(pdata["stages"]) == 6
print(f"[OK] CI/CD Pipeline {pdata['build_id']} passed all 6 automated stages in {pdata['total_duration_ms']}ms.")

print("\n========================================")
print("ALL TESTS PASSED! SAGE & STAMP AUTH & SUITE READY.")
print("========================================")
