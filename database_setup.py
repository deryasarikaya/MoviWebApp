from sqlalchemy import text
from models import db
from seed_data import seed_demo_data


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


def initialize_database(app, data_manager, api_key):
    """Prepare the database for local development and deployment."""
    with app.app_context():
        db.create_all()
        ensure_movie_columns()
        seed_demo_data(data_manager, api_key)
