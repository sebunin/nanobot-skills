# nanobot-skills

Навыки для AI-ассистента nanobot.

## 📦 Содержимое

- `clawdhub/` — поиск и установка скиллов из ClawHub
- `gog/` — интеграция с Google Workspace (Gmail, Calendar, Drive)
- `openmeteo/` — точный прогноз погоды через Open-Meteo API
- `summarize/` — суммаризация текста/видео/подкастов
- `weather/` — погода через wttr.in (fallback)

## 🚀 Установка

Скопируйте папку нужного скилла в:
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

<!-- NANOBOT_SKILLS_START -->
<!-- Updated: 07.04.2026 00:22 -->
| Skill | Description |
|-------|-------------|
| `backup` | Резервное копирование конфигурации, рабочего пространства, навыков, памяти и крон-заданий Nanobot |
| `blogwatcher` | Monitor blogs and RSS/Atom feeds for updates using the blogwatcher CLI |
| `clawdhub` | Use the ClawdHub CLI to search, install, update, and publish agent skills from clawdhub |
| `github` | "GitHub operations via `gh` CLI: issues, PRs, CI runs, code review, API queries |
| `gog` | Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, and Docs |
| `instagram-cli` | instagram |
| `openai-whisper` | Local speech-to-text with the Whisper CLI (no API key) |
| `openmeteo` | Получение точного прогноза погоды через Open-Meteo API (без ключа) |
| `songsee` | Generate spectrograms and feature-panel visualizations from audio with the songsee CLI |
| `summarize` | Summarize or extract text/transcripts from URLs, podcasts, and local files (great fallback for “transcribe this YouTube/video”) |
| `trello` | Manage Trello boards, lists, and cards via the Trello REST API |
| `twittertrends` | Search and analyze trending topics on X (Twitter) |
| `weather` | "Get current weather and forecasts via wttr |
| `xtrends` | Search and analyze trending topics on X (Twitter) |
| `youtube-summarize` | Summarize YouTube videos by extracting transcripts and captions |
| `youtube-thumbnail-grabber` | Download YouTube video thumbnails in various resolutions |
| `youtube-video-downloader` | Download YouTube videos in various formats and qualities |
<!-- NANOBOT_SKILLS_END -->
