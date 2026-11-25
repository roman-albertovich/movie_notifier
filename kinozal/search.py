import re
import urllib.parse

import requests
from bs4 import BeautifulSoup


class KinozalSearch:
    BASE_URL = "https://kinozal.me"

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def find_torrent(self, title: str, release_year: str) -> str | None:
        if not title:
            return None

        encoded_title = urllib.parse.quote_plus(title)
        search_url = f"{self.BASE_URL}/browse.php?s={encoded_title}"

        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.encoding = "windows-1251"

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            # Парсим строки таблицы раздач (.t_peer tr)
            rows = soup.select(".t_peer tr.bg, .t_peer tr.first.bg")

            matched_db = []  # Список с перевод "ДБ"
            matched_pm = []  # Список с перевод "ПМ"

            for row in rows:
                link_elem = row.select_one("td.nam a[href^='/details.php?id=']")
                if not link_elem:
                    continue

                torrent_title = link_elem.get_text()
                torrent_href = link_elem["href"]

                # 1. Проверка года выхода
                if release_year and release_year not in torrent_title:
                    continue

                # 2. Проверка качества (1080p или 2160p)
                if not re.search(r"1080p|2160p", torrent_title, re.IGNORECASE):
                    continue

                full_url = f"{self.BASE_URL}{torrent_href}"

                # 3. Разделение по типу перевода: ДБ vs ПМ
                if re.search(r"\bДБ\b", torrent_title):
                    matched_db.append(full_url)
                elif re.search(r"\bПМ\b", torrent_title):
                    matched_pm.append(full_url)

            # Приоритет: сначала ДБ, если нет — ПМ
            if matched_db:
                return matched_db[0]
            if matched_pm:
                return matched_pm[0]

        except requests.RequestException as e:
            print(f'[Kinozal] Ошибка при поиске "{title}": {e}')

        return None
