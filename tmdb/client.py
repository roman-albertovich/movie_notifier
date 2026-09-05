from datetime import datetime, timedelta
import requests
from tmdb.models import Movie


class TMDBClient:

  BASE_URL = 'https://api.themoviedb.org/3'

  def __init__(self, api_key: str):
    self.api_key = api_key
    self.genres_map = self._get_genres()

  def _get_genres(self) -> dict:
    url = f'{self.BASE_URL}/genre/movie/list'
    params = {'api_key': self.api_key, 'language': 'ru-RU'}
    try:
      res = requests.get(url, params=params, timeout=10).json()
      return {g['id']: g['name'] for g in res.get('genres', [])}
    except Exception:
      return {}

  def _get_english_overview(self, movie_id: int) -> str:
    """Делает фоллбэк-запрос для получения описания на английском языке."""
    url = f'{self.BASE_URL}/movie/{movie_id}'
    params = {'api_key': self.api_key, 'language': 'en-US'}
    try:
      res = requests.get(url, params=params, timeout=5).json()
      return res.get('overview', '')
    except Exception:
      return ''

  def get_digital_releases_last_7_days(self) -> list[Movie]:
    """Фильтрует фильмы: цифровой релиз за последние 7 дней, оценка >= 5.0."""
    now = datetime.now()
    start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')
    # Дата 360 дней назад для фильтрации года/мировой премьеры фильма
    min_movie_age_date = (now - timedelta(days=360)).strftime('%Y-%m-%d')

    url = f'{self.BASE_URL}/discover/movie'
    params = {
        'api_key': self.api_key,
        'language': 'ru-RU',
        'region': 'US',
        'with_release_type': '4|5',  # Цифровые и физические релизы
        'release_date.gte': start_date,
        'release_date.lte': end_date,
        'primary_release_date.gte': min_movie_age_date,
        'vote_average.gte': 5.0,  # Оценка выше 5.0
        'sort_by': 'popularity.desc',
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    movies = []
    for item in data.get('results', []):
      movie_id = item.get('id')
      release_date = item.get('release_date', '')
      year = release_date.split('-')[0] if release_date else ''

      genre_ids = item.get('genre_ids', [])
      genres = [
          self.genres_map.get(gid, '')
          for gid in genre_ids
          if gid in self.genres_map
      ]

      # Логика подтягивания английского описания, если русское отсутствует
      overview = item.get('overview', '').strip()
      if not overview and movie_id:
        overview = self._get_english_overview(movie_id)

      movies.append(
          Movie(
              tmdb_id=item.get('id'),  # Сохраняем ID от TMDb
              title=item.get('title') or item.get('original_title'),
              original_title=item.get('original_title', ''),
              rating=str(round(item.get('vote_average', 0), 1)),
              genre=', '.join(filter(None, genres)) or 'Не указан',
              year=year,
              url=f"https://www.themoviedb.org/movie/{item.get('id')}",
              poster_path=(
                  f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                  if item.get('poster_path')
                  else ""
              ),
              overview=overview or 'Описание отсутствует.',
          )
      )

    return movies