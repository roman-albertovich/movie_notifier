import requests
from tmdb.models import Movie

class TelegramSender:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    def send_movie_notification(self, movie: Movie, torrent_url: str) -> bool:
        if not self.token or not self.chat_id:
            print("[Telegram] Ошибка: TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заполнены.")
            return False

        # Формируем текст подписи с HTML-разметкой
        short_overview = (
            (movie.overview[:250] + "...")
            if len(movie.overview) > 250
            else movie.overview
        )

        caption = (
            f"🎬 <b><a href='{movie.url}'>{movie.title}</a></b> ({movie.year})\n"
            f"<b>Оригинальное название:</b> {movie.original_title or '—'}\n"
            f"<b>Рейтинг TMDb:</b> ⭐ {movie.rating}\n"
            f"<b>Жанры:</b> {movie.genre}\n\n"
            f"<b>Описание:</b>\n{short_overview}\n\n"
            f"📥 <a href='{torrent_url}'>Скачать торрент на Кинозале</a>"
        )

        # Если есть постер — шлем фото с подписью, иначе просто текстовое сообщение
        if movie.poster_path:
            endpoint = f"{self.api_url}/sendPhoto"
            payload = {
                "chat_id": self.chat_id,
                "photo": movie.poster_path,
                "caption": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
        else:
            endpoint = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }

        try:
            res = requests.post(endpoint, json=payload, timeout=10)
            data = res.json()
            if res.status_code == 200 and data.get("ok"):
                return True
            else:
                print(f"[Telegram] Ошибка отправки: {data.get('description')}")
                return False
        except Exception as e:
            print(f"[Telegram] Ошибка запроса к Telegram API: {e}")
            return False