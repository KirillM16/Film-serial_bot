import sqlite3
import random


class MovieDatabase:
    def __init__(self, db_path="movie_database.db"):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_random_movie(self):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 1")
            return cur.fetchone()

    def get_movie_by_id(self, movie_id):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
            return cur.fetchone()

    def get_movies_by_ids(self, movie_ids):
        if not movie_ids:
            return []

        placeholders = ",".join("?" for _ in movie_ids)
        query = f"SELECT * FROM movies WHERE id IN ({placeholders})"

        with self._connect() as con:
            cur = con.cursor()
            cur.execute(query, movie_ids)
            return cur.fetchall()

    def search_movie(self, title):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM movies WHERE LOWER(title) LIKE ? LIMIT 1",
                (f"%{title.lower()}%",)
            )
            return cur.fetchone()

    def get_top_movies(self, limit=10):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM movies ORDER BY rating DESC LIMIT ?",
                (limit,)
            )
            return cur.fetchall()

    def get_random_movie_by_genre(self, genre):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM movies WHERE LOWER(genre) LIKE ? "
                "ORDER BY RANDOM() LIMIT 1",
                (f"%{genre.lower()}%",)
            )
            return cur.fetchone()