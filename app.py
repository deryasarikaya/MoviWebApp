import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template
from data_manager import DataManager
from database_setup import initialize_database
from models import db
from movie_service import build_movie_stats, create_movie_from_omdb_data, fetch_movie_by_title

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
        data = fetch_movie_by_title(title, OMDB_API_KEY)

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


initialize_database(app, data_manager, OMDB_API_KEY)


if __name__ == '__main__':
    app.run(debug=True)
