import sqlite3

from database.db import Database


def test_database_initialization(tmp_path):
    db_path = tmp_path / "test.db"

    db = Database(str(db_path))

    assert db.db_path == str(db_path)
    assert db_path.exists()

    with sqlite3.connect(db.db_path) as conn:
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

    assert "processed_movies" in tables


def test_movie_not_processed_initially(tmp_path):
    db = Database(str(tmp_path / "test.db"))

    assert db.is_movie_processed(123) is False


def test_add_movie(tmp_path):
    db = Database(str(tmp_path / "test.db"))

    db.add_movie(123, "Interstellar")

    assert db.is_movie_processed(123) is True


def test_duplicate_movie_is_not_added(tmp_path):
    db = Database(str(tmp_path / "test.db"))

    db.add_movie(123, "Interstellar")
    db.add_movie(123, "Interstellar 2")

    assert db.is_movie_processed(123) is True

    with sqlite3.connect(db.db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM processed_movies WHERE tmdb_id = ?",
            (123,),
        ).fetchone()[0]

        title = conn.execute(
            "SELECT title FROM processed_movies WHERE tmdb_id = ?", (123,)
        ).fetchone()[0]

    assert count == 1
    assert title == "Interstellar"


def test_movie_title_is_stripped(tmp_path):
    db = Database(str(tmp_path / "test.db"))

    db.add_movie(123, "  Interstellar  ")

    with sqlite3.connect(db.db_path) as conn:
        title = conn.execute(
            "SELECT title FROM processed_movies WHERE tmdb_id = ?",
            (123,),
        ).fetchone()[0]

    assert title == "Interstellar"
