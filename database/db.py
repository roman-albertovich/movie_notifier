import os
import sqlite3
from contextlib import closing


class Database:
    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "movies.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Инициализирует таблицу обработанных фильмов."""
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                """
        CREATE TABLE IF NOT EXISTS processed_movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tmdb_id INTEGER UNIQUE,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
            )

    def is_movie_processed(self, tmdb_id: int) -> bool:
        """Проверяет наличие фильма по ID из TMDb."""
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_movies WHERE tmdb_id = ?",
                (tmdb_id,),
            )
            return cursor.fetchone() is not None

    def add_movie(self, tmdb_id: int, title: str) -> None:
        """Записывает ID и название фильма."""
        with closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                """
          INSERT OR IGNORE INTO processed_movies (tmdb_id, title)
          VALUES (?, ?)
          """,
                (tmdb_id, title.strip()),
            )
