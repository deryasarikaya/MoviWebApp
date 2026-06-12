import requests
from collections import Counter
from models import Movie


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


def fetch_movie_by_title(title, api_key):
    """Fetch one movie from OMDb by title."""
    response = requests.get(
        f"http://www.omdbapi.com/?t={title}&apikey={api_key}",
        timeout=5
    )
    response.raise_for_status()
    return response.json()


def fetch_movie_by_imdb_id(imdb_id, api_key):
    """Fetch one movie from OMDb by IMDb ID."""
    if not api_key:
        return None

    try:
        response = requests.get(
            f"http://www.omdbapi.com/?i={imdb_id}&apikey={api_key}",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        if data.get('Response') == 'True':
            return data
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch demo movie from OMDb: {e}")

    return None
