import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/all_recipes")
def all_recipes():
    recipes = mongo.db.recipes.find()
    food_tags = mongo.db.food_tags.find().sort("food_type", 1)

    return render_template(
        "recipes.html", recipes=recipes, food_tags=food_tags)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    recipes = mongo.db.recipes.find({"$text": {"$search": query}})
    food_tags = mongo.db.food_tags.find().sort("food_type", 1)
    
    return render_template(
        "recipes.html", recipes=recipes, food_tags=food_tags)


@app.route("/register", methods=['GET', 'POST'])
def register():
    password1 = request.form.get("password_1")
    password2 = request.form.get("password_2")
 
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists. Please try another one.")
            return redirect(url_for("register"))

        if password1 == password2:
            register = {
                "firstname": request.form.get("firstname").lower(),
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(
                    request.form.get("password_2"))
            }
            mongo.db.users.insert_one(register)

            # log user into 'session' cookie
            session['user'] = request.form.get("username").lower()
            flash("Registration Successful")
            return redirect(url_for("profile", username=session["user"]))

        else:
            flash("Passwords didn’t match. Try again.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                existing_user['password'], request.form.get("password_2")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get('username')))
                    return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                flash("Invalid Username and or Password")
                return redirect(url_for('login'))

        else:
            flash("Invalid Username and or Password")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for('login'))


@app.route("/logout")
def logout():
    flash("You have been log out")
    session.pop("user")
    return redirect(url_for('login'))


@app.route("/view_recipe/<recipe_id>", methods=["GET"])
def view_recipe(recipe_id):
    recipe = mongo.db.recipes.find_one(
        {"_id": ObjectId(recipe_id)})

    return render_template("individual_recipe.html", recipe=recipe)


@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        ingredients_list = request.form.get('ingredients_list').split(';')
        method = request.form.get('method').split(';')

        recipe = {
            "recipe_name": request.form.get('recipe_name'),
            "food_type": request.form.get('food_type'),
            "estimated_time": request.form.get('estimated_time'),
            "url_picture": request.form.get('url_picture'),
            "commentary": request.form.get('commentary'),
            "ingredients_list": ingredients_list,
            "method": method,
            "created_by": session['user']
        }

        mongo.db.recipes.insert_one(recipe)
        flash("Recipe Added with success!")
        return redirect(url_for('all_recipes'))

    food_tags = mongo.db.food_tags.find().sort("food_type", 1)
    return render_template('add_recipe.html', food_tags=food_tags)


@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        ingredients_list = request.form.get('ingredients_list').split(';')
        method = request.form.get('method').split(';')

        submit = {
            "recipe_name": request.form.get('recipe_name'),
            "food_type": request.form.get('food_type'),
            "estimated_time": request.form.get('estimated_time'),
            "url_picture": request.form.get('url_picture'),
            "commentary": request.form.get('commentary'),
            "ingredients_list": ingredients_list,
            "method": method,
            "created_by": session['user']
        }

        mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, submit)
        flash("Recipe Uptaded with success!")
        return redirect(url_for('all_recipes'))

    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    food_tags = mongo.db.food_tags.find().sort("food_type", 1)
    return render_template(
        'edit_recipe.html', food_tags=food_tags, recipe=recipe)


@app.route('/delete_recipe/<recipe_id>')
def delete_recipe(recipe_id):
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Recipe deleted with success!")
    return redirect(url_for('all_recipes'))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
