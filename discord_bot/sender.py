import requests
from tmdb.models import Movie

class DiscordSender:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_movie_notification(self, movie: Movie, torrent_url: str) -> bool:
        if not self.webhook_url:
            print("[Discord] Ошибка: DISCORD_WEBHOOK_URL не заполнен.")
            return False

        # Ограничиваем длинное описание для аккуратного отображения в Discord
        short_overview = (
            (movie.overview[:280] + '...')
            if len(movie.overview) > 280
            else movie.overview
        )

        embed = {
            "title": f"🎬 {movie.title} ({movie.year})",
            "url": movie.url,
            "description": f"**Описание:**\n{short_overview}",
            "color": 3066993,  # Зеленый цвет
            "fields": [
                {
                    "name": "Оригинальное название",
                    "value": movie.original_title or "—",
                    "inline": True
                },
                {
                    "name": "Рейтинг TMDb",
                    "value": f"⭐ {movie.rating}",
                    "inline": True
                },
                {
                    "name": "Жанры",
                    "value": movie.genre,
                    "inline": False
                },
                {
                    "name": "Ссылка на Кинозал",
                    "value": f"[📥 Скачать торрент]({torrent_url})",
                    "inline": False
                }
            ]
        }

        # Если у фильма есть картинка постера, добавляем её
        if movie.poster_path:
            embed["image"] = {"url": movie.poster_path}

        payload = {
            "username": "Movie Finder Bot",
            "embeds": [embed]
        }

        try:
            res = requests.post(self.webhook_url, json=payload, timeout=10)
            return res.status_code in (200, 204)
        except Exception as e:
            print(f"[Discord] Ошибка запроса: {e}")
            return False