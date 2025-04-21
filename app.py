from flask import Flask, request, render_template, redirect, url_for, session, flash
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load files
trending_products = pd.read_csv("models/trending_products.csv")
train_data = pd.read_csv("models/clean_data.csv")

# Configuration
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///ecom.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

# Helper functions
def truncate(text, length):
    return text[:length] + "..." if len(text) > length else text

def content_based_recommendations(train_data, item_name, top_n=10):
    if item_name not in train_data['Name'].values:
        return pd.DataFrame()

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix_content = tfidf_vectorizer.fit_transform(train_data['Tags'])
    cosine_similarities_content = cosine_similarity(tfidf_matrix_content, tfidf_matrix_content)

    item_index = train_data[train_data['Name'] == item_name].index[0]
    similar_items = list(enumerate(cosine_similarities_content[item_index]))
    similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)
    top_similar_items = similar_items[1:top_n+1]

    recommended_item_indices = [x[0] for x in top_similar_items]
    return train_data.iloc[recommended_item_indices][['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]

# Predefined image URLs
random_image_urls = [f"static/img/img_{i}.png" for i in range(1, 9)]

@app.route("/")
@app.route("/index")
def index():
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    prices = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html',
                           trending_products=trending_products.head(8),
                           truncate=truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price=random.choice(prices))

@app.route("/main")
def main():
    return render_template('main.html')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or Email already exists. Please try another.', 'danger')
            return redirect(url_for('signup'))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful. You can now log in.', 'success')
        return redirect(url_for('signin'))
    return render_template('signup.html')

@app.route('/signin', methods=['POST', 'GET'])
def signin():   
    if request.method == 'POST':
        username = request.form['signinUsername']
        password = request.form['signinPassword']
        
        # Check if user exists in the User table
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            # Login success
            random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
            price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
            return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                                   random_product_image_urls=random_product_image_urls, random_price=random.choice(price),
                                   signup_message=f'Welcome back, {username}!')
        else:
            # Invalid login
            return render_template('signin.html', message="Invalid username or password. Please try again.")

    return render_template('signin.html')


@app.route("/recommendations", methods=['POST', 'GET'])
def recommendations():
    if request.method == 'POST':
        prod = request.form.get('prod')
        nbr = int(request.form.get('nbr'))
        content_based_rec = content_based_recommendations(train_data, prod, top_n=nbr)

        if content_based_rec.empty:
            return render_template('main.html', message="No recommendations available for this product.")

        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(content_based_rec))]
        prices = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
        return render_template('main.html',
                               content_based_rec=content_based_rec,
                               truncate=truncate,
                               random_product_image_urls=random_product_image_urls,
                               random_price=random.choice(prices))
    return render_template('main.html', content_based_rec=None)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)