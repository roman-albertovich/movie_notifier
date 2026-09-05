import logging
from config import Config
from telegram_bot.sender import TelegramSender
from tmdb.client import TMDBClient
from database.db import Database

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S' # Формат отображения даты и времени
)


def run_pipeline():
  logging.info('[Pipeline] Запуск процесса...')

  try:
    db = Database()
    tmdb_client = TMDBClient(Config.TMDB_API_KEY)
    telegram_sender = TelegramSender(Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)

    # Получение релизов за 7 дней (оценка > 5.0)
    movies = tmdb_client.get_digital_releases_last_7_days()
    logging.info(f'[TMDb] Отфильтровано релизов: {len(movies)}')

    for movie in movies:
      # Проверяем по tmdb_id.
      # Если ID есть в БД, то фильм пропускается.
      if db.is_movie_processed(movie.tmdb_id):
        logging.info(
          f'[Skip] Фильм {movie.title} (ID: {movie.tmdb_id}) уже обработан.'
        )
        continue

      success = telegram_sender.send_movie_notification(movie)
      if success:
        db.add_movie(movie.tmdb_id, movie.title)
        logging.info(f'[DB] Фильм {movie.title} сохранен в БД.')

  except Exception:
    logging.exception('[Pipeline] Критическая ошибка')


if __name__ == '__main__':
  run_pipeline()