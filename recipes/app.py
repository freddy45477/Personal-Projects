#import flask
# #render_template tells it to find the html file 
from flask import Flask, render_template, request
from recipes import user_input
#create web app instance called app, __name__ tells flask whether
#this file is running directly or imported
app = Flask(__name__)

#this tells if the person visits the homepage "/", run the next function
@app.route("/", methods=['POST'])
#this function runs when "/" is visited
def home():
    recipe = None
    if request.method == "POST":
        ingredients = request.form.get("ingredients")
        recipe = user_input(ingredients)
    return render_template("index.html", recipe=recipe)


#runs this code when you execute this file
if __name__ == "__main__":
    #allows auto-reload and shows error messages in the browser
    app.run(debug=True)