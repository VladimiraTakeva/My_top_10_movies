from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
TMDB_API_KEY = os.environ["API_KEY"]
API_TOKEN = os.environ["API_TOKEN"]


url = "https://api.themoviedb.org/3/search/movie?query=%22The%20money%20pit%22&include_adult=false"


headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2M2I2ZDMxNDNlMGJmMGM4YTRmODU2NjY0YjY2MjQwYyIsInN1YiI6IjY0YjFiNzQwMGU0ZmM4MDEwMTgxY2ZjNyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.dgmT0ai6xDMpGnUUZsVf0OxNgw7hPagm3EfBb0aeTrE"
}

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies-collection.db"

db = SQLAlchemy()
db.init_app(app)


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out Of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review")
    done = SubmitField("Done")


class AddMovieForm(FlaskForm):
    movie_name = StringField("Movie Title", validators=[DataRequired()])
    done = SubmitField("Add")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Float, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = Movie.query.all()
    # result = db.session.execute(db.select(Movie))
    # all_movies = result.scalars()
    ratings = list(db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars())
    # result.scalars().all()
    print(ratings)
    for index in range(len(ratings)):
        ratings[index].ranking = index + 1
    db.session.commit()

    return render_template("index.html", movies=result)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        url_for_movie_details = f"https://api.themoviedb.org/3/movie/{movie_api_id}"
        response = requests.get(url_for_movie_details, headers=headers)
        movie_data = response.json()
        print(response.text)
        new_movie = Movie(
            title=movie_data["title"],
            year=movie_data["release_date"].split("-")[0],
            description=movie_data["overview"],
            rating=0,
            ranking=0,
            review="",
            img_url=f"https://image.tmdb.org/t/p/w500/{movie_data['poster_path']}",
        )

        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for('edit', id=new_movie.id))


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        if form.review.data != "":
            movie.review = form.review.data
            db.session.commit()
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.movie_name.data
        parameter = {
            "query": movie_title
        }
        response = requests.get(url, headers=headers, params=parameter)
        # print(response.text)
        data = response.json()["results"]

        return render_template("select.html", movies=data)

    return render_template("add.html", form=form)


if __name__ == '__main__':
    app.run(debug=True)
