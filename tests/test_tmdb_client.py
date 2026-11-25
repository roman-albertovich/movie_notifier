from tmdb.client import TMDBClient
from tmdb.models import Movie
import requests
import pytest


BASE = "https://api.themoviedb.org/3"

class FakeApi:
    def __init__(self):
        self.routes = {}
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.routes[url]

@pytest.fixture
def api(monkeypatch):
    fake = FakeApi()
    fake.routes[f"{BASE}/genre/movie/list"] = MockResponse(
        {"genres": [{"id": 18, "name": "Драма"}, {"id": 28, "name": "Боевик"}]}
    )
    monkeypatch.setattr("tmdb.client.requests.get", fake.get)
    return fake


def test_discover_maps_fields(api):
    api.routes[f"{BASE}/discover/movie"] = MockResponse({"results": [{
        "id": 603,
        "title": "Матрица",
        "original_title": "The Matrix",
        "vote_average": 8.2649,
        "genre_ids": [28, 18, 999],   # 999 неизвестен
        "release_date": "1999-03-31",
        "poster_path": "/abc.jpg",
        "overview": "Описание",
    }]})

    movies = TMDBClient("key").get_digital_releases_last_7_days()

    assert movies == [Movie(
        tmdb_id=603,
        title="Матрица",
        original_title="The Matrix",
        rating="8.3",
        genre="Боевик, Драма",
        year="1999",
        url="https://www.themoviedb.org/movie/603",
        poster_path="https://image.tmdb.org/t/p/w500/abc.jpg",
        overview="Описание",
    )]

class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_get_genres(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse({
            "genres": [
                {"id": 28, "name": "Боевик"},
                {"id": 18, "name": "Драма"},
            ]
        })

    monkeypatch.setattr(
        "tmdb.client.requests.get",
        mock_get,
    )

    client = TMDBClient("test_api_key")

    assert client.genres_map == {
        28: "Боевик",
        18: "Драма",
    }


def test_get_genres_returns_empty_dict_on_error(monkeypatch):
    def mock_get(*args, **kwargs):
        raise ConnectionError("API unavailable")

    monkeypatch.setattr(
        "tmdb.client.requests.get",
        mock_get,
    )

    client = TMDBClient("test_api_key")

    assert client.genres_map == {}


def test_get_english_overview(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse({
            "overview": "A space exploration movie."
        })

    monkeypatch.setattr(
        "tmdb.client.requests.get",
        mock_get,
    )

    client = TMDBClient("test_api_key")

    result = client._get_english_overview(123)

    assert result == "A space exploration movie."
