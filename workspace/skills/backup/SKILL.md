---
name: backup
description: Резервное копирование конфигурации, рабочего пространства, навыков, памяти и крон-заданий Nanobot. Сохранение локально в архив или публикация в репозиторий GitHub (без секретов). Восстановление из резервной копии. При бэкапе навыков в GitHub — автоматическое обновление README.md со списком скиллов.
metadata: {"nanobot":{"emoji":"💾","requires":{"bins":["python3","git"],"env":[]}}}
---

# 💾 Nanobot — Скилл резервного копирования

## Структура данных Nanobot

```
~/.nanobot/
├── config.json                    # ⚠️ СЕКРЕТЫ: API-ключи и токены каналов
├── workspace/
│   ├── SOUL.md                    # Личность агента
│   ├── AGENTS.md                  # Инструкции агентов
│   ├── USER.md                    # Информация о пользователе
│   ├── TOOLS.md                   # Документация инструментов
│   ├── HEARTBEAT.md               # Задачи heartbeat
│   ├── memory/MEMORY.md           # Долгосрочная память
│   ├── skills/                    # Навыки — папки с SKILL.md внутри
│   │   └── имя_навыка/
│   │       └── SKILL.md
│   └── sessions/                  # Сессии переписки
├── cron/jobs.json                 # Крон-задания
└── history/cli_history            # История CLI
```

**Windows:** `C:\Users\Сергей\.nanobot\`  
**WSL2:** `~/.nanobot/` или `/mnt/c/Users/Сергей/.nanobot/`

---

## Что и куда архивировать

| Тип      | Что включает                                               | Можно в GitHub |
|----------|------------------------------------------------------------|----------------|
| `full`   | Всё: config, workspace, cron, sessions, history            | ❌ Нет         |
| `public` | workspace/skills + workspace/USER.md + workspace/projects + cron | ✅ Да    |
| `skills` | workspace/skills/                                          | ✅ Да          |
| `memory` | workspace/memory/                                          | ✅ Да          |
| `cron`   | cron/                                                      | ✅ Да          |
| `config` | config.json (только локально!)                             | ❌ Нет         |

---

## ⚠️ Правила безопасности для GitHub

**Автоматическая санитизация секретов:**
Перед загрузкой любого файла в GitHub скрипт `backup_skills_to_github.py` автоматически проверяет его содержимое и заменяет реальные секреты (API-ключи, токены, пароли) на `***`. Это позволяет безопасно публиковать файлы в репозиторий без риска утечки чувствительных данных.

**Что заменяется:**
- Значения после `=` или `:` в строках, содержащих ключевые слова: `api_key`, `token`, `password`, `secret`, `claw_`, `sk-`, `xoxb-`, `xapp-`
- Только реальные секреты (длинные строки с высокой энтропией)
- Примеры и документация (содержащие `YOUR_`, `example`, `sample`, `TEST`) пропускаются

**Пример:**
```json
// До загрузки:
{"api_key": "07b38f744be2478b30fbd79a78ee5c9d", "token": "ATTA..."}

// После загрузки в GitHub:
{"api_key": "***", "token": "***"}
```

**Никогда не включать в GitHub:**
- `config.json` — содержит API-ключи (исключён из BACKUP_SOURCES)
- `workspace/sessions/` — личная переписка
- `history/cli_history` — история команд

---

## Локальное резервное копирование

Агент выполняет команды через `exec`. Все команды работают на Windows и WSL2 одинаково — используют Python и `pathlib.Path.home()`, который корректно обрабатывает кириллику в пути.

Папка бэкапов по умолчанию: `~/nanobot-backups/`

### Полный бэкап (`full`) — включает всё

```python
python3 -c "
import pathlib, tarfile, datetime
src = pathlib.Path.home() / '.nanobot'
dst = pathlib.Path.home() / 'nanobot-backups'
if not src.exists():
    print('ОШИБКА: директория ~/.nanobot не найдена')
    exit(1)
dst.mkdir(parents=True, exist_ok=True)
ts  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
out = dst / f'nanobot_full_{ts}.tar.gz'
with tarfile.open(out, 'w:gz') as tar:
    tar.add(src, arcname='.nanobot')
print('Создан:', out, f'({out.stat().st_size // 1024} КБ)')
"
```

### Публичный бэкап (`public`) — без секретов

```python
python3 -c "
import pathlib, tarfile, datetime
src  = pathlib.Path.home() / '.nanobot'
dst  = pathlib.Path.home() / 'nanobot-backups'
if not src.exists():
    print('ОШИБКА: директория ~/.nanobot не найдена')
    exit(1)
dst.mkdir(parents=True, exist_ok=True)
ts   = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
out  = dst / f'nanobot_public_{ts}.tar.gz'
SKIP = {'sessions', 'cli_history', 'config.json', 'history'}

def filt(ti):
    import pathlib as pl
    parts = pl.PurePosixPath(ti.name).parts
    return None if any(p in SKIP for p in parts) else ti

with tarfile.open(out, 'w:gz') as tar:
    for item in [src / 'workspace', src / 'cron']:
        if item.exists():
            tar.add(item, arcname='.nanobot/' + item.name, filter=filt)
print('Создан:', out, f'({out.stat().st_size // 1024} КБ)')
"
```

### Бэкап только навыков / памяти / крон

```python
# Навыки:
python3 -c "
import pathlib, tarfile, datetime
src = pathlib.Path.home() / '.nanobot' / 'workspace' / 'skills'
dst = pathlib.Path.home() / 'nanobot-backups'
dst.mkdir(parents=True, exist_ok=True)
out = dst / f'nanobot_skills_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.tar.gz'
with tarfile.open(out, 'w:gz') as tar:
    tar.add(src, arcname='.nanobot/workspace/skills')
print('Создан:', out)
"

# Память:
python3 -c "
import pathlib, tarfile, datetime
src = pathlib.Path.home() / '.nanobot' / 'workspace' / 'memory'
dst = pathlib.Path.home() / 'nanobot-backups'
dst.mkdir(parents=True, exist_ok=True)
out = dst / f'nanobot_memory_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.tar.gz'
with tarfile.open(out, 'w:gz') as tar:
    tar.add(src, arcname='.nanobot/workspace/memory')
print('Создан:', out)
"

# Крон:
python3 -c "
import pathlib, shutil, datetime
src = pathlib.Path.home() / '.nanobot' / 'cron' / 'jobs.json'
dst = pathlib.Path.home() / 'nanobot-backups'
dst.mkdir(parents=True, exist_ok=True)
out = dst / f'nanobot_cron_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'
shutil.copy2(src, out)
print('Создан:', out)
"
```

### Список существующих резервных копий

```python
python3 -c "
import pathlib
d = pathlib.Path.home() / 'nanobot-backups'
files = sorted(d.glob('nanobot_*'), reverse=True) if d.exists() else []
if not files:
    print('Резервных копий нет')
for f in files:
    print(f.name, f'({f.stat().st_size // 1024} КБ)')
"
```

---

## Бэкап в GitHub

**Что копируется** (структура повторяет `.nanobot/workspace`):
```
workspace/skills/     → workspace/skills/
workspace/USER.md     → workspace/USER.md
workspace/projects/   → workspace/projects/
cron/                 → cron/
```

**Инструмент:** GitHub CLI (`gh`). Клонирование не требуется — файлы загружаются через API.  
**Скрипт:** `workspace/skills/backup/backup_skills_to_github.py`

---

### Шаг 1 — Проверить gh

```
gh auth status
```

Если ошибка — **остановиться**:
> Установи GitHub CLI: https://cli.github.com  
> Затем: `gh auth login`

---

### Шаг 2 — Определить репозиторий

Агент проверяет `MEMORY.md` на наличие:
```
GITHUB_SKILLS_REPO: owner/repo-name
```

Если нет — показать список:
```
gh repo list --limit 20 --json nameWithOwner --jq ".[].nameWithOwner"
```

Пользователь выбирает один раз. Агент сохраняет в `MEMORY.md`:
```
GITHUB_SKILLS_REPO: owner/repo-name
```

---

### Шаг 3 — Запустить скрипт

```
python3 ~/.nanobot/workspace/skills/backup/backup_skills_to_github.py owner/repo-name
```

Или через переменную окружения:
```
NANOBOT_GITHUB_REPO=owner/repo-name python3 ~/.nanobot/workspace/skills/backup/backup_skills_to_github.py
```

Скрипт сам выполняет:
1. Проверку авторизации `gh`
2. Проверку секретов через `check_secrets.py`
3. Загрузку изменившихся файлов (сравнение байт-в-байт, SHA берётся в том же запросе что и контент)
4. Обновление таблицы навыков в `README.md` между маркерами

---

### Структура README.md в репозитории

README.md обновляется **только между маркерами** — всё остальное остаётся нетронутым:
```
<!-- NANOBOT_SKILLS_START -->
...таблица навыков обновляется автоматически...
<!-- NANOBOT_SKILLS_END -->
```

Если маркеров нет — таблица добавляется в конец файла.  
Если README.md не существует — создаётся минимальный шаблон.

---

### Файлы навыка

| Файл | Назначение |
|------|-----------|
| `SKILL.md` | Инструкции для агента |
| `backup_skills_to_github.py` | Загрузка файлов в GitHub через gh API |
| `check_secrets.py` | Проверка на секреты перед публикацией |

---

### Требования к описаниям навыков

Все описания навыков в файле `SKILL.md` должны быть **на русском языке**. Это требование применяется при автоматическом обновлении таблицы навыков в `README.md` репозитория.

---

## Восстановление из архива

```python
python3 -c "
import pathlib, tarfile, shutil, datetime, sys

archive = pathlib.Path(sys.argv[1])
home    = pathlib.Path.home()
nanobot = home / '.nanobot'

if not archive.exists():
    print('ОШИБКА: архив не найден:', archive)
    exit(1)

# Сохраняем текущее состояние перед перезаписью
ts     = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup = home / f'.nanobot_pre_restore_{ts}'
if nanobot.exists():
    shutil.copytree(str(nanobot), str(backup))
    print('Текущий конфиг сохранён в:', backup)

with tarfile.open(archive, 'r:gz') as tar:
    tar.extractall(path=home)
print('Восстановление завершено из:', archive)
" ПУТЬ_К_АРХИВУ
```

---

## Как агент принимает решения при запросе бэкапа

Если пользователь не указал явно что и куда — **уточнить оба параметра перед действием**.

| Запрос пользователя             | Действие агента                                               |
|---------------------------------|---------------------------------------------------------------|
| «Полный бэкап»                  | Локальный архив `full`                                        |
| «Бэкап навыков в GitHub»        | Шаги 1–3 из раздела «Бэкап в GitHub»                         |
| «Сохрани всё в GitHub»          | 🚨 Стоп: `config.json` содержит API-ключи, только локально   |
| «Бэкап в GitHub»                | Шаги 1–3 из раздела «Бэкап в GitHub»                         |
| «Бэкап конфига в GitHub»        | 🚨 Стоп: `config.json` нельзя публиковать                    |
| «Бэкап крон» / «бэкап памяти»  | Уточнить: локально или GitHub?                                |
| «Покажи резервные копии»        | Список файлов из `~/nanobot-backups/`                         |
| «Восстанови из бэкапа»          | Список копий → уточнить какую → восстановить                  |

---

## Устранение проблем

**Проверить целостность архива:**
```python
python3 -c "
import tarfile, sys
try:
    with tarfile.open(sys.argv[1], 'r:gz') as t:
        print(f'OK: {len(t.getmembers())} файлов')
except Exception as e:
    print('Архив повреждён:', e)
" ПУТЬ_К_АРХИВУ
```

**git не настроен:**
```bash
git config --global user.email "ваш@email.com"
git config --global user.name "Ваше Имя"
```

**Кириллика в пути** — все команды используют `pathlib.Path.home()`, который работает корректно на Windows с любым именем пользователя.
