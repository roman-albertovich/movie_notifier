import logging
from html import escape

import requests

from tmdb.models import Movie

logger = logging.getLogger(__name__)


class TelegramSender:
    # Максимальная длина caption для sendPhoto.
    # Telegram считает длину в UTF-16 code units.
    MAX_CAPTION_LENGTH = 1024

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    @staticmethod
    def _telegram_length(text: str) -> int:
        """
        Возвращает длину строки в UTF-16 code units.

        Telegram использует именно такую модель подсчёта длины
        текста для некоторых ограничений API.
        """
        return len(text.encode("utf-16-le")) // 2

    @staticmethod
    def _truncate_html_safe(text: str, max_length: int) -> str:
        """
        Безопасно обрезает обычный текст после HTML escaping.
        max_length задаётся в UTF-16 code units.
        """

        if not text or max_length <= 0:
            return ""

        result = []
        current_length = 0

        for char in text:
            escaped_char = escape(char)
            char_length = TelegramSender._telegram_length(escaped_char)

            if current_length + char_length > max_length:
                break

            result.append(escaped_char)
            current_length += char_length

        return "".join(result)

    def _build_caption(self, movie: Movie) -> str:
        """
        Формирует безопасный HTML-caption для Telegram.

        Гарантирует, что:
        - HTML-разметка валидна;
        - HTML entities не разрываются;
        - caption не превышает MAX_CAPTION_LENGTH;
        - обрезается только описание.
        """

        # Данные фильма экранируем ДО помещения в HTML.
        title = escape(str(movie.title or "—"))
        url = escape(str(movie.url or ""), quote=True)
        year = escape(str(movie.year or "—"))
        original_title = escape(str(movie.original_title or "—"))
        rating = escape(str(movie.rating or "—"))
        genre = escape(str(movie.genre or "—"))

        # Overview оставляем неэкранированным здесь.
        # Он будет безопасно обработан _truncate_html_safe().
        overview = str(movie.overview or "")

        # Эта часть caption никогда не обрезается.
        prefix = (
            f"🎬 <b><a href='{url}'>{title}</a></b> ({year})\n"
            f"<b>Оригинальное название:</b> {original_title}\n"
            f"<b>Рейтинг TMDb:</b> ⭐ {rating}\n"
            f"<b>Жанры:</b> {genre}\n\n"
            f"<b>Описание:</b>\n"
        )

        # На всякий случай проверяем длину prefix.
        # В нормальной ситуации сюда никогда не попадём.
        prefix_length = self._telegram_length(prefix)

        if prefix_length >= self.MAX_CAPTION_LENGTH:
            logger.warning(
                "[Telegram] Фиксированная часть caption превышает лимит 1024 символа."
            )

            # Здесь теоретически возможно повреждение HTML,
            # поэтому вместо произвольного обрезания возвращаем
            # безопасное сообщение без HTML-разметки.
            fallback = (
                f"🎬 {escape(str(movie.title or '—'))} "
                f"({escape(str(movie.year or '—'))})"
            )

            if self._telegram_length(fallback) <= self.MAX_CAPTION_LENGTH:
                return fallback

            return self._truncate_html_safe(fallback, self.MAX_CAPTION_LENGTH)

        # Сколько места осталось под описание.
        available = self.MAX_CAPTION_LENGTH - prefix_length

        escaped_overview = escape(overview)

        # Всё описание помещается целиком.
        if self._telegram_length(escaped_overview) <= available:
            return prefix + escaped_overview

        # Описание придётся обрезать.
        suffix = "..."

        suffix_length = self._telegram_length(suffix)

        # Если места недостаточно даже для suffix,
        # оставляем максимально возможное количество символов.
        if available <= suffix_length:
            return prefix + self._truncate_html_safe(overview, available)

        available_for_overview = available - suffix_length

        safe_overview = self._truncate_html_safe(overview, available_for_overview)

        return prefix + safe_overview + suffix

    def send_movie_notification(self, movie: Movie) -> bool:
        """
        Отправляет уведомление о фильме в Telegram.

        Если у фильма есть poster_path:
            используется sendPhoto.

        Если постера нет:
            используется sendMessage.
        """

        if not self.token:
            logger.error("[Telegram] TELEGRAM_BOT_TOKEN не заполнен.")
            return False

        if not self.chat_id:
            logger.error("[Telegram] TELEGRAM_CHAT_ID не заполнен.")
            return False

        caption = self._build_caption(movie)

        # Дополнительная защита.
        # Проверяем именно UTF-16 длину.
        caption_length = self._telegram_length(caption)

        if caption_length > self.MAX_CAPTION_LENGTH:
            logger.error(
                "[Telegram] Caption превышает лимит: "
                f"{caption_length}/{self.MAX_CAPTION_LENGTH}"
            )
            return False

        try:
            if movie.poster_path:
                endpoint = f"{self.api_url}/sendPhoto"

                payload = {
                    "chat_id": self.chat_id,
                    "photo": movie.poster_path,
                    "caption": caption,
                    "parse_mode": "HTML",
                }

            else:
                endpoint = f"{self.api_url}/sendMessage"

                payload = {
                    "chat_id": self.chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                }

            response = requests.post(
                endpoint,
                json=payload,
                timeout=10,
            )

            # Telegram API обычно возвращает JSON.
            try:
                data = response.json()
            except ValueError:
                logger.error(
                    "[Telegram] Telegram API вернул "
                    f"невалидный JSON. HTTP {response.status_code}: "
                    f"{response.text[:500]}"
                )
                return False

            if response.status_code == 200 and data.get("ok"):
                logger.info(f"[Telegram] Уведомление отправлено: {movie.title}")
                return True

            logger.error(
                "[Telegram] Ошибка отправки: "
                f"HTTP {response.status_code}; "
                f"{data.get('description', 'Неизвестная ошибка')}"
            )

            return False

        except requests.RequestException as e:
            logger.error(f"[Telegram] Ошибка HTTP-запроса: {e}")
            return False

        except Exception:
            logger.exception("[Telegram] Неожиданная ошибка при отправке сообщения")
            return False
