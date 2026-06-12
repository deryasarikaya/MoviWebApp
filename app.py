import os
import requests
from collections import Counter
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template
from sqlalchemy import text
from data_manager import DataManager
from models import db, User, Movie

load_dotenv()
OMDB_API_KEY = os.environ.get('API_KEY')

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, "data/movies.db")
os.makedirs(os.path.dirname(database_path), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + database_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
data_manager = DataManager()


def ensure_movie_columns():
    """Add new movie columns to older SQLite databases."""
    columns = db.session.execute(text("PRAGMA table_info(movie)")).fetchall()
    column_names = {column[1] for column in columns}
    new_columns = {
        "imdb_rating": "FLOAT",
        "personal_rating": "FLOAT",
        "genre": "VARCHAR(200)",
    }

    for column_name, column_type in new_columns.items():
        if column_name not in column_names:
            db.session.execute(
                text(f"ALTER TABLE movie ADD COLUMN {column_name} {column_type}")
            )

    db.session.commit()


def parse_rating(value):
    """Return a float rating or None."""
    if not value or value == "N/A":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def build_movie_stats(movies):
    """Build simple statistics for a movie collection."""
    years = [movie.year for movie in movies if movie.year]
    genres = []

    for movie in movies:
        if movie.genre:
            genres.extend(genre.strip() for genre in movie.genre.split(',') if genre.strip())

    favorite_genre = Counter(genres).most_common(1)[0][0] if genres else None

    return {
        "total": len(movies),
        "oldest": min(years) if years else None,
        "newest": max(years) if years else None,
        "favorite_genre": favorite_genre,
    }


def create_movie_from_omdb_data(data, user_id):
    """Create a Movie object from OMDb data."""
    year_text = data.get('Year', '')[:4]
    year = int(year_text) if year_text.isdigit() else None

    poster_url = data.get('Poster')
    if poster_url == 'N/A':
        poster_url = None

    return Movie(
        name=data.get('Title', 'Unknown'),
        director=data.get('Director'),
        year=year,
        poster_url=poster_url,
        imdb_rating=parse_rating(data.get('imdbRating')),
        genre=data.get('Genre') if data.get('Genre') != 'N/A' else None,
        user_id=user_id
    )


def get_movie_from_omdb_by_id(imdb_id):
    """Fetch one movie from OMDb by IMDb ID."""
    if not OMDB_API_KEY:
        return None

    try:
        response = requests.get(
            f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        if data.get('Response') == 'True':
            return data
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch demo movie from OMDb: {e}")

    return None


def seed_demo_data():
    """Create demo users and movies if the database is empty."""
    if data_manager.get_users():
        return

    demo_collections = [
        {
            "name": "Derya",
            "movies": [
                {"imdb_id": "tt0068646", "personal_rating": 9.6},
                {"imdb_id": "tt0111161", "personal_rating": 9.4},
                {"imdb_id": "tt6751668", "personal_rating": 8.8},
            ],
        },
        {
            "name": "Mina",
            "movies": [
                {"imdb_id": "tt1375666", "personal_rating": 9.1},
                {"imdb_id": "tt0816692", "personal_rating": 9.3},
                {"imdb_id": "tt0133093", "personal_rating": 8.7},
            ],
        },
        {
            "name": "Noah",
            "movies": [
                {"imdb_id": "tt0110912", "personal_rating": 8.9},
                {"imdb_id": "tt0118799", "personal_rating": 9.0},
                {"imdb_id": "tt1853728", "personal_rating": 8.5},
            ],
        },
    ]

    fallback_movies = {
        "tt0068646": {"name": "The Godfather", "director": "Francis Ford Coppola", "year": 1972, "imdb_rating": 9.2, "genre": "Crime, Drama"},
        "tt0111161": {"name": "The Shawshank Redemption", "director": "Frank Darabont", "year": 1994, "imdb_rating": 9.3, "genre": "Drama"},
        "tt6751668": {"name": "Parasite", "director": "Bong Joon Ho", "year": 2019, "imdb_rating": 8.5, "genre": "Drama, Thriller"},
        "tt1375666": {"name": "Inception", "director": "Christopher Nolan", "year": 2010, "imdb_rating": 8.8, "genre": "Action, Adventure, Sci-Fi"},
        "tt0816692": {"name": "Interstellar", "director": "Christopher Nolan", "year": 2014, "imdb_rating": 8.7, "genre": "Adventure, Drama, Sci-Fi"},
        "tt0133093": {"name": "The Matrix", "director": "Lana Wachowski, Lilly Wachowski", "year": 1999, "imdb_rating": 8.7, "genre": "Action, Sci-Fi"},
        "tt0110912": {"name": "Pulp Fiction", "director": "Quentin Tarantino", "year": 1994, "imdb_rating": 8.9, "genre": "Crime, Drama"},
        "tt0118799": {"name": "Life Is Beautiful", "director": "Roberto Benigni", "year": 1997, "imdb_rating": 8.6, "genre": "Comedy, Drama, Romance"},
        "tt1853728": {"name": "Django Unchained", "director": "Quentin Tarantino", "year": 2012, "imdb_rating": 8.5, "genre": "Drama, Western"},
    }

    try:
        for collection in demo_collections:
            user = User(name=collection["name"])
            db.session.add(user)
            db.session.flush()

            for movie_seed in collection["movies"]:
                movie_data = get_movie_from_omdb_by_id(movie_seed["imdb_id"])

                if movie_data:
                    movie = create_movie_from_omdb_data(movie_data, user.id)
                else:
                    fallback = fallback_movies[movie_seed["imdb_id"]]
                    movie = Movie(
                        name=fallback["name"],
                        director=fallback["director"],
                        year=fallback["year"],
                        poster_url=None,
                        imdb_rating=fallback["imdb_rating"],
                        genre=fallback["genre"],
                        user_id=user.id
                    )

                movie.personal_rating = movie_seed["personal_rating"]
                db.session.add(movie)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Could not create demo data: {e}")


def initialize_database():
    """Prepare the database for local development and deployment."""
    with app.app_context():
        db.create_all()
        ensure_movie_columns()
        seed_demo_data()


@app.route('/')
def index():
    """Show all users on the homepage."""
    users = data_manager.get_users()
    user_cards = []

    for user in users:
        user_cards.append({
            "id": user.id,
            "name": user.name,
            "initial": user.name[:1].upper(),
            "movie_count": data_manager.count_movies(user.id)
        })

    return render_template('index.html', users=user_cards)


@app.route('/users', methods=['POST'])
def create_user():
    """Add a new user and redirect to homepage."""
    name = request.form.get('name', '').strip()
    if name:
        if data_manager.user_exists(name):
            return redirect(url_for('index', error='user_exists'))
        data_manager.create_user(name)
    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_movies(user_id):
    """Show all movies for a specific user."""
    if user_id <= 0:
        return "Invalid user ID", 400
    user = data_manager.get_user(user_id)
    if not user:
        return render_template('404.html'), 404
    movies = data_manager.get_movies(user_id)
    stats = build_movie_stats(movies)
    return render_template(
        'movies.html',
        movies=movies,
        user=user,
        user_id=user_id,
        stats=stats
    )


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """Fetch movie info from OMDb and add it to the user's list."""
    if user_id <= 0:
        return "Invalid user ID", 400
    title = request.form.get('title', '').strip()
    if not title:
        return redirect(url_for('get_movies', user_id=user_id))
    try:
        response = requests.get(
            f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        if data.get('Response') == 'False':
            return redirect(url_for('get_movies', user_id=user_id, error='not_found'))

        if data_manager.movie_exists(user_id, data.get('Title', '')):
            return redirect(url_for('get_movies', user_id=user_id, error='movie_exists'))

        movie = create_movie_from_omdb_data(data, user_id)
        data_manager.add_movie(movie)

    except requests.exceptions.RequestException as e:
        print(f"Could not connect to OMDb API: {e}")
    except ValueError as e:
        print(f"Could not read movie data correctly: {e}")
    except KeyError as e:
        print(f"Missing movie data from API response: {e}")

    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """Update the title of a specific movie."""
    if user_id <= 0 or movie_id <= 0:
        return "Invalid ID", 400
    movie = data_manager.get_movie(movie_id)
    if not movie or movie.user_id != user_id:
        return "Movie not found", 404
    new_title = request.form.get('title', '').strip()
    if new_title:
        data_manager.update_movie(movie_id, new_title)
    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/rating', methods=['POST'])
def update_personal_rating(user_id, movie_id):
    """Update the personal rating of a specific movie."""
    if user_id <= 0 or movie_id <= 0:
        return "Invalid ID", 400
    movie = data_manager.get_movie(movie_id)
    if not movie or movie.user_id != user_id:
        return "Movie not found", 404

    rating_text = request.form.get('personal_rating', '').strip()
    personal_rating = None

    if rating_text:
        try:
            personal_rating = float(rating_text)
        except ValueError:
            return redirect(url_for('get_movies', user_id=user_id))

        if personal_rating < 0 or personal_rating > 10:
            return redirect(url_for('get_movies', user_id=user_id))

    data_manager.update_personal_rating(movie_id, personal_rating)
    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """Delete a specific movie from the user's list."""
    if user_id <= 0 or movie_id <= 0:
        return "Invalid ID", 400
    movie = data_manager.get_movie(movie_id)
    if not movie or movie.user_id != user_id:
        return "Movie not found", 404
    data_manager.delete_movie(movie_id)
    return redirect(url_for('get_movies', user_id=user_id))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500


initialize_database()


if __name__ == '__main__':
    app.run(debug=True)
