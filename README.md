# nanobot

Резервные копии файлов AI-ассистента nanobot.

## 📦 Содержимое


<!-- NANOBOT_SKILLS_START -->
<!-- Updated: 07.04.2026 01:46 -->
| Skill | Description |
|-------|-------------|
| `backup` | Резервное копирование конфигурации, рабочего пространства, навыков, памяти и крон-заданий Nanobot |
| `blogwatcher` | Отслеживание обновлений блогов и RSS/Atom-лент с помощью blogwatcher CLI |
| `clawdhub` | Поиск, установка, обновление и публикация навыков агента через ClawdHub CLI с clawdhub |
| `github` | Операции с GitHub через `gh` CLI: issues, PRs, запуски CI, code review, API запросы |
| `gog` | CLI для Google Workspace: Gmail, Calendar, Drive, Contacts, Sheets, Docs |
| `instagram` | CLI для взаимодействия с Instagram (просмотр постов, ленты, профилей) |
| `openai-whisper` | Локальное распознавание речи с помощью Whisper CLI (без API-ключа) |
| `openmeteo` | Получение точного прогноза погоды через Open-Meteo API (без ключа) |
| `songsee` | Генерация спектрограмм и визуализаций признаков из аудио с помощью songsee CLI |
| `summarize` | Summarize or extract text/transcripts from URLs, podcasts, and local files (great fallback for “transcribe this YouTube/video”) |
| `trello` | Управление досками, списками и карточками Trello через Trello REST API |
| `twittertrends` | Search and analyze trending topics on X (Twitter) |
| `weather` | Получение текущей погоды и прогнозов через wttr |
| `xtrends` | Search and analyze trending topics on X (Twitter) |
| `youtube-summarize` | Summarize YouTube videos by extracting transcripts and captions |
| `youtube-thumbnail-grabber` | Download YouTube video thumbnails in various resolutions |
| `youtube-video-downloader` | Download YouTube videos in various formats and qualities |
<!-- NANOBOT_SKILLS_END -->


## 🚀 Установка

Структура репозитория повторяет структуру Nanobot. Например, для восстановления навыков скопируйте папку нужного скилла в:
```
~/.nanobot/workspace/skills/
```

## 📖 Документация

Каждый скилл содержит файл `SKILL.md` с описанием и примерами использования.

## 🔧 Требования

- nanobot >= 0.1.0
- Для некоторых скиллов требуются внешние утилиты (curl, gh и т.д.)

## 📝 Лицензия

MIT
