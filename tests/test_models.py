from tmdb.models import Movie


def test_movie_creation():
    movie = Movie(
        tmdb_id=123,
        title="Интерстеллар",
        original_title="Interstellar",
        rating="8.7",
        genre="Фантастика",
        year="2014",
        url="https://www.themoviedb.org/movie/123",
    )

    assert movie.tmdb_id == 123
    assert movie.title == "Интерстеллар"
    assert movie.original_title == "Interstellar"
    assert movie.rating == "8.7"
    assert movie.genre == "Фантастика"
    assert movie.year == "2014"


def test_movie_optional_fields():
    movie = Movie(
        tmdb_id=123,
        title="Интерстеллар",
        original_title="Interstellar",
        rating="8.7",
        genre="Фантастика",
        year="2014",
        url="https://www.themoviedb.org/movie/123",
    )

    assert movie.poster_path == ""
    assert movie.overview == ""
