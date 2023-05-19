from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import NumberRange, InputRequired
import requests
import auth

import requests

AUTH_KEY = auth.API_KEY


search_name_url = "https://api.themoviedb.org/3/search/movie"
search_id_url = "https://api.themoviedb.org/3/movie"

headers = {
    "accept": "application/json",
    "Authorization": AUTH_KEY,
}


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


class MovieData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer(), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer(), nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f"MovieData(id={self.id}, title={self.title}, description = {self.description}, year={self.year}," \
               f"rating={self.rating}, ranking={self.ranking}, review = {self.review}, img_url = {self.img_url}"


class RateMovieForm(FlaskForm):
    rating = FloatField('Your Rating Out of 10 e.g. 7.5', validators=[NumberRange(min=0, max=10)])
    review = StringField('Your Review')
    submit = SubmitField('Update')


class AddMovie(FlaskForm):
    title = StringField('Movie Title', validators=[InputRequired()])
    submit = SubmitField('Search')


@app.route("/")
def home():
    with app.app_context():
        ranked_movies = MovieData.query.order_by(MovieData.rating).all()
    for num in range(len(ranked_movies)):
        ranked_movies[num].ranking = len(ranked_movies) - num
    db.session.commit()
    return render_template("index.html", movies=ranked_movies)


@app.route("/add", methods=["POST", "GET"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        movie_title = form.title.data
        return redirect(url_for('select', movie_title=movie_title))

    return render_template("add.html", form=form)


@app.route("/select")
def select():
    movie_search = request.args.get("movie_title")
    param = {
        "query": movie_search,
    }

    response = requests.get(search_name_url, headers=headers, params=param)
    all_results = response.json()["results"]
    print(all_results)
    return render_template("select.html", results=all_results)


@app.route("/new_entry/<int:movie_id>")
def entry(movie_id):
    id_params = {
        "language": "en-US",
    }

    response = requests.get(url=f"{search_id_url}/{movie_id}", headers=headers, params=id_params)
    movie_info = response.json()
    with app.app_context():
        new_movie = MovieData(
            title=movie_info['title'],
            year=movie_info['release_date'].split('-')[0],
            rating=0,
            review="NULL",
            ranking=0,
            description=movie_info['overview'],
            img_url=f"https://image.tmdb.org/t/p/w500/{movie_info['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', movie_id=new_movie.id))


@app.route("/edit/<int:movie_id>", methods=["POST", "GET"])
def edit(movie_id):
    with app.app_context():
        movie_to_update = db.session.get(MovieData, movie_id)
        form = RateMovieForm()

        if request.method == "POST" and form.validate_on_submit():
            movie_to_update.rating = form.rating.data
            movie_to_update.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))
    return render_template("edit.html", form=form)


@app.route("/delete/<int:movie_id>")
def delete(movie_id):
    with app.app_context():
        movie_to_delete = db.session.get(MovieData, movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
