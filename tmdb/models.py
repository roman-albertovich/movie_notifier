from dataclasses import dataclass

@dataclass
class Movie:
    tmdb_id: int
    title: str
    original_title: str
    rating: str
    genre: str
    year: str
    url: str
    poster_path: str = ""
    overview: str = ""