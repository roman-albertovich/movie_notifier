import logging

from config import Config
from database.db import Database
from telegram_bot.sender import TelegramSender
from tmdb.client import TMDBClient

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",  # Формат отображения даты и времени
)

logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("[Pipeline] Запуск процесса...")

    try:
        db = Database()
        tmdb_client = TMDBClient(Config.TMDB_API_KEY)
        telegram_sender = TelegramSender(
            Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID
        )

        # Получение релизов за 7 дней (оценка > 5.0)
        movies = tmdb_client.get_digital_releases_last_7_days()
        logger.info(f"[TMDb] Отфильтровано релизов: {len(movies)}")

        for movie in movies:
            # Проверяем по tmdb_id.
            # Если ID есть в БД, то фильм пропускается.
            if db.is_movie_processed(movie.tmdb_id):
                logger.info(
                    f"[Skip] Фильм {movie.title} (ID: {movie.tmdb_id}) уже обработан."
                )
                continue

            success = telegram_sender.send_movie_notification(movie)
            if success:
                db.add_movie(movie.tmdb_id, movie.title)
                logger.info(f"[DB] Фильм {movie.title} сохранён в БД.")

    except Exception:
        logger.exception("[Pipeline] Критическая ошибка")


if __name__ == "__main__":
    run_pipeline()
