import logging
from config import Config
from telegram_bot.sender import TelegramSender
from kinozal.search import KinozalSearch
from tmdb.client import TMDBClient
from database.db import Database

logging.basicConfig(level=logging.INFO)


def run_pipeline():
  logging.info('[Pipeline] Запуск процесса...')

  db = Database()
  tmdb_client = TMDBClient(Config.TMDB_API_KEY)
  kinozal_search = KinozalSearch()
  telegram_sender = TelegramSender(Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)

  # Получение релизов за 7 дней (оценка > 5.0)
  movies = tmdb_client.get_digital_releases_last_7_days()
  logging.info(f'[TMDb] Отфильтровано релизов: {len(movies)}')

  for movie in movies:
    # 1. ПЕРВАЯ ДЕЙСТВИЕ: Проверяем по tmdb_id.
    # Если ID есть в БД — Кинозал НЕ ВЗЫВАЕТСЯ.
    if db.is_movie_processed(movie.tmdb_id):
      logging.info(
        f'[Skip] Фильм {movie.title} (ID: {movie.tmdb_id}) уже обработан.'
      )
      continue

    logging.info(
        f'[Kinozal] Поиск: {movie.title} ({movie.year}) |'
        f' {movie.original_title}'
    )

    # Ищем раздачу (1080p/2160p, год == movie.year, ДБ -> ПМ)
    torrent_url = kinozal_search.find_torrent(movie.title, movie.year)

    if not torrent_url and movie.original_title != movie.title:
      torrent_url = kinozal_search.find_torrent(
          movie.original_title, movie.year
      )

    if torrent_url:
      logging.info(f'[Discord] Отправка карточки: {movie.title}')
      success = telegram_sender.send_movie_notification(movie, torrent_url)
      if success:
        db.add_movie(movie.tmdb_id, movie.title)
        logging.info(f'[DB] Фильм {movie.title} сохранен в БД.')


if __name__ == '__main__':
  run_pipeline()