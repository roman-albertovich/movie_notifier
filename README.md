# Movie Notifier Bot

Точка входа — `app.py`, функция `run_pipeline()`. При запуске приложение инициализирует SQLite, TMDb-клиент и Telegram-отправитель, получает цифровые релизы за последние 7 дней с рейтингом не ниже 5.0, затем обрабатывает каждый фильм.

Фильм пропускается, если его `tmdb_id` уже присутствует в таблице `processed_movies`. Новый фильм отправляется в Telegram. В базу он добавляется только после успешной отправки.

TMDb-клиент загружает справочник жанров при создании объекта. Если у фильма отсутствует русскоязычное описание, выполняется дополнительный запрос за английским описанием.

Telegram-отправитель использует `sendPhoto`, если у фильма есть постер, иначе `sendMessage`.

| Компонент | Ответственность |
|---|---|
| `app.py` | оркестрация: инициализация, цикл по фильмам, дедупликация, логирование |
| `config.py` | переменные окружения `TMDB_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| `tmdb.client` | запросы к TMDb, маппинг JSON → `Movie`, жанры, фоллбэк описания |
| `tmdb.models` | DTO `Movie` — общий контракт между клиентом и отправителем |
| `telegram_bot.sender` | формирование безопасного HTML-caption, `sendPhoto` / `sendMessage` |
| `database.db` | учёт обработанных фильмов (`processed_movies`, `tmdb_id UNIQUE`) |
| `search` | поиск раздач на Kinozal (отключён) |

Зависимости: внешние библиотеки — `requests`, `python-dotenv`, (`beautifulsoup4` для `search.py`, нет в `requirements.txt`).
```mermaid
sequenceDiagram
    autonumber
    actor Sch as Планировщик
    participant App as app.run_pipeline
    participant DB as Database
    participant TC as TMDBClient
    participant TMDB as TMDb API
    participant TS as TelegramSender
    participant TG as Telegram Bot API

    Sch->>App: запуск (python app.py)
    App->>DB: Database() → _init_db()
    DB-->>App: таблица processed_movies готова

    App->>TC: TMDBClient(api_key)
    TC->>TMDB: GET /genre/movie/list (ru-RU)
    TMDB-->>TC: genres (или ошибка → {})
    TC-->>App: клиент с genres_map

    App->>TS: TelegramSender(token, chat_id)

    App->>TC: get_digital_releases_last_7_days()
    TC->>TMDB: GET /discover/movie (фильтры)
    TMDB-->>TC: results[]
    loop для каждого результата
        opt overview пустой
            TC->>TMDB: GET /movie/{id} (en-US)
            TMDB-->>TC: overview
        end
    end
    TC-->>App: list[Movie]

    loop для каждого Movie
        App->>DB: is_movie_processed(tmdb_id)
        DB-->>App: bool
        alt уже обработан
            App->>App: лог [Skip]
        else новый фильм
            App->>TS: send_movie_notification(movie)
            TS->>TS: _build_caption() и проверка длины
            alt есть poster_path
                TS->>TG: POST sendPhoto
            else нет постера
                TS->>TG: POST sendMessage
            end
            TG-->>TS: {ok, description}
            TS-->>App: True / False
            opt success == True
                App->>DB: add_movie(tmdb_id, title)
            end
        end
    end
    App-->>Sch: процесс завершён
```