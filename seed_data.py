from models import db, User, Movie
from movie_service import create_movie_from_omdb_data, fetch_movie_by_imdb_id


DEMO_COLLECTIONS = [
    {
        "name": "Derya",
        "movies": [
            {"imdb_id": "tt0068646", "personal_rating": 9.6},
            {"imdb_id": "tt0111161", "personal_rating": 9.4},
            {"imdb_id": "tt6751668", "personal_rating": 8.8},
            {"imdb_id": "tt0468569", "personal_rating": 9.2},
        ],
    },
    {
        "name": "Mina",
        "movies": [
            {"imdb_id": "tt1375666", "personal_rating": 9.1},
            {"imdb_id": "tt0816692", "personal_rating": 9.3},
            {"imdb_id": "tt0133093", "personal_rating": 8.7},
            {"imdb_id": "tt0120737", "personal_rating": 9.0},
        ],
    },
    {
        "name": "Noah",
        "movies": [
            {"imdb_id": "tt0110912", "personal_rating": 8.9},
            {"imdb_id": "tt0118799", "personal_rating": 9.0},
            {"imdb_id": "tt1853728", "personal_rating": 8.5},
            {"imdb_id": "tt0407887", "personal_rating": 8.6},
        ],
    },
]


FALLBACK_MOVIES = {
    "tt0068646": {"name": "The Godfather", "director": "Francis Ford Coppola", "year": 1972, "imdb_rating": 9.2, "genre": "Crime, Drama"},
    "tt0111161": {"name": "The Shawshank Redemption", "director": "Frank Darabont", "year": 1994, "imdb_rating": 9.3, "genre": "Drama"},
    "tt6751668": {"name": "Parasite", "director": "Bong Joon Ho", "year": 2019, "imdb_rating": 8.5, "genre": "Drama, Thriller"},
    "tt0468569": {"name": "The Dark Knight", "director": "Christopher Nolan", "year": 2008, "imdb_rating": 9.0, "genre": "Action, Crime, Drama"},
    "tt1375666": {"name": "Inception", "director": "Christopher Nolan", "year": 2010, "imdb_rating": 8.8, "genre": "Action, Adventure, Sci-Fi"},
    "tt0816692": {"name": "Interstellar", "director": "Christopher Nolan", "year": 2014, "imdb_rating": 8.7, "genre": "Adventure, Drama, Sci-Fi"},
    "tt0133093": {"name": "The Matrix", "director": "Lana Wachowski, Lilly Wachowski", "year": 1999, "imdb_rating": 8.7, "genre": "Action, Sci-Fi"},
    "tt0120737": {"name": "The Lord of the Rings: The Fellowship of the Ring", "director": "Peter Jackson", "year": 2001, "imdb_rating": 8.9, "genre": "Action, Adventure, Drama"},
    "tt0110912": {"name": "Pulp Fiction", "director": "Quentin Tarantino", "year": 1994, "imdb_rating": 8.9, "genre": "Crime, Drama"},
    "tt0118799": {"name": "Life Is Beautiful", "director": "Roberto Benigni", "year": 1997, "imdb_rating": 8.6, "genre": "Comedy, Drama, Romance"},
    "tt1853728": {"name": "Django Unchained", "director": "Quentin Tarantino", "year": 2012, "imdb_rating": 8.5, "genre": "Drama, Western"},
    "tt0407887": {"name": "The Departed", "director": "Martin Scorsese", "year": 2006, "imdb_rating": 8.5, "genre": "Crime, Drama, Thriller"},
}


def create_fallback_movie(imdb_id, user_id):
    """Create a fallback movie if OMDb is unavailable during seeding."""
    fallback = FALLBACK_MOVIES[imdb_id]
    return Movie(
        name=fallback["name"],
        director=fallback["director"],
        year=fallback["year"],
        poster_url=None,
        imdb_rating=fallback["imdb_rating"],
        genre=fallback["genre"],
        user_id=user_id
    )


def seed_demo_data(data_manager, api_key):
    """Create demo users and movies if the database is empty."""
    if data_manager.get_users():
        return

    try:
        for collection in DEMO_COLLECTIONS:
            user = User(name=collection["name"])
            db.session.add(user)
            db.session.flush()

            for movie_seed in collection["movies"]:
                movie_data = fetch_movie_by_imdb_id(movie_seed["imdb_id"], api_key)

                if movie_data:
                    movie = create_movie_from_omdb_data(movie_data, user.id)
                else:
                    movie = create_fallback_movie(movie_seed["imdb_id"], user.id)

                movie.personal_rating = movie_seed["personal_rating"]
                db.session.add(movie)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Could not create demo data: {e}")
