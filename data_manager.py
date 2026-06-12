from sqlalchemy.exc import SQLAlchemyError
from models import db, User, Movie


class DataManager:

    def create_user(self, name):
        """Add a new user to the database."""
        try:
            new_user = User(name=name)
            db.session.add(new_user)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return False

    def get_users(self):
        """Return a list of all users."""
        return User.query.all()

    def get_user(self, user_id):
        """Return one user by ID."""
        return User.query.get(user_id)

    def get_movies(self, user_id):
        """Return all movies for a specific user."""
        return Movie.query.filter_by(user_id=user_id).all()

    def count_movies(self, user_id):
        """Return the number of movies for a specific user."""
        return Movie.query.filter_by(user_id=user_id).count()

    def get_movie(self, movie_id):
        """Return one movie by ID."""
        return Movie.query.get(movie_id)

    def user_exists(self, name):
        """Check if user already exists (case-insensitive)."""
        return User.query.filter(
            User.name.ilike(name)
        ).first() is not None

    def movie_exists(self, user_id, title):
        """Check if movie already exists for this user (case-insensitive)."""
        return Movie.query.filter(
            Movie.user_id == user_id,
            Movie.name.ilike(title)
        ).first() is not None

    def add_movie(self, movie):
        """Add a new movie to the database."""
        try:
            db.session.add(movie)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return False

    def update_movie(self, movie_id, new_title):
        """Update the title of a specific movie."""
        try:
            movie = Movie.query.get(movie_id)
            if not movie:
                return False
            movie.name = new_title
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return False

    def update_personal_rating(self, movie_id, personal_rating):
        """Update the personal rating of a specific movie."""
        try:
            movie = Movie.query.get(movie_id)
            if not movie:
                return False
            movie.personal_rating = personal_rating
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return False

    def delete_movie(self, movie_id):
        """Delete a specific movie from the database."""
        try:
            movie = Movie.query.get(movie_id)
            if not movie:
                return False
            db.session.delete(movie)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            return False
