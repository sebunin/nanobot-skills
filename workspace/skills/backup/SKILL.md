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

| Тип      | Что включает                                         | Можно в GitHub |
|----------|------------------------------------------------------|----------------|
| `full`   | Всё: config, workspace, cron, sessions, history      | ❌ Нет         |
| `public` | workspace (без sessions) + cron. Без config/history  | ✅ Да          |
| `skills` | workspace/skills/                                    | ✅ Да          |
| `memory` | workspace/memory/                                    | ✅ Да          |
| `cron`   | cron/jobs.json                                       | ✅ Да          |
| `config` | config.json (только локально!)                       | ❌ Нет         |

---

## ⚠️ Правила безопасности для GitHub

**Перед любым push агент обязан выполнить проверку через `check_secrets.py`:**

```bash
python skills/backup/check_secrets.py
```

Скрипт ищет потенциальные секреты (API ключи, токены, пароли) в папках:
- `workspace/skills/`
- `workspace/memory/`
- `cron/`

**Особенность:** Строки, содержащие примеры (слова `YOUR_`, `example`, `sample`, `TEST`), автоматически игнорируются. Это позволяет не срабатывать на документации, где ключи указаны как шаблоны.

Если результат содержит `СТОП!` — **немедленно остановиться и предупредить пользователя**. Push не выполнять.

**Никогда не включать в GitHub:**
- `config.json` — содержит API-ключи
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

## Бэкап навыков в GitHub

Навык — это папка в `workspace/skills/`, содержащая `SKILL.md` и вспомогательные файлы.

**Инструмент:** GitHub CLI (`gh`). Клонирование репозитория не требуется — файлы загружаются напрямую через GitHub API.

---

### Шаг 1 — Проверить наличие и авторизацию gh

```
gh auth status
```

Если команда вернула ошибку — **остановиться** и сообщить пользователю:

> `gh` не найден или не авторизован. Установи GitHub CLI: https://cli.github.com  
> Затем выполни: `gh auth login`

Продолжать только если `gh auth status` завершился успешно.

---

### Шаг 2 — Определить репозиторий

Агент проверяет память (MEMORY.md) на наличие строки вида:
```
GITHUB_SKILLS_REPO: owner/repo-name
```

Если запись есть — использовать её. Если нет — выполнить:

```
gh repo list --limit 20 --json name,nameWithOwner --jq ".[] | .nameWithOwner"
```

Показать список пользователю, попросить выбрать репозиторий для навыков.  
После выбора — записать в MEMORY.md:
```
GITHUB_SKILLS_REPO: owner/repo-name
```

---

### Шаг 3 — Проверка секретов

Выполнить команду из раздела «Правила безопасности» выше.  
Если вывод содержит `СТОП!` — остановиться. Дальнейшие шаги не выполнять.

---

### Шаг 4 — Загрузить файлы навыков в репозиторий

Для каждого файла: читаем содержимое, получаем текущий SHA (если файл уже есть в репо), загружаем через `gh api`.  
Загружаются только файлы, содержимое которых изменилось.

```python
python3 -c "
import pathlib, subprocess, json, base64, sys

REPO       = sys.argv[1]   # owner/repo-name
skills_dir = pathlib.Path.home() / '.nanobot' / 'workspace' / 'skills'
PREFIX     = 'workspace/skills'   # путь внутри репозитория
changed    = []
skipped    = []

def gh_api(method, path, data=None):
    cmd = ['gh', 'api', path, '--method', method, '--silent']
    if data:
        cmd += ['--input', '-']
        r = subprocess.run(cmd, input=json.dumps(data),
                           capture_output=True, text=True, encoding='utf-8')
    else:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return r

def get_file_sha(repo_path):
    r = subprocess.run(
        ['gh', 'api', f'repos/{REPO}/contents/{repo_path}'],
        capture_output=True, text=True, encoding='utf-8'
    )
    if r.returncode == 0:
        return json.loads(r.stdout).get('sha')
    return None

def get_remote_content(repo_path):
    r = subprocess.run(
        ['gh', 'api', f'repos/{REPO}/contents/{repo_path}'],
        capture_output=True, text=True, encoding='utf-8'
    )
    if r.returncode == 0:
        b64 = json.loads(r.stdout).get('content', '').replace('\\n', '')
        try:
            return base64.b64decode(b64)
        except Exception:
            return None
    return None

for skill_dir in sorted(skills_dir.iterdir()):
    if not skill_dir.is_dir():
        continue
    for f in skill_dir.rglob('*'):
        if not f.is_file():
            continue
        rel       = f.relative_to(skills_dir)
        repo_path = PREFIX + '/' + str(rel).replace('\\\\', '/')
        local_bytes = f.read_bytes()

        # Сравниваем с версией в репо
        remote_bytes = get_remote_content(repo_path)
        if remote_bytes == local_bytes:
            skipped.append(repo_path)
            continue

        sha  = get_file_sha(repo_path)
        body = {
            'message': f'skills: update {rel}',
            'content': base64.b64encode(local_bytes).decode(),
        }
        if sha:
            body['sha'] = sha

        r = gh_api('PUT', f'repos/{REPO}/contents/{repo_path}', body)
        if r.returncode == 0:
            changed.append(repo_path)
            print('Загружен:', repo_path)
        else:
            print('ОШИБКА:', repo_path, r.stderr)

print(f'Готово. Обновлено: {len(changed)}, без изменений: {len(skipped)}')
" OWNER/REPO
```

Заменить `OWNER/REPO` на значение из шага 2.

---

### Шаг 5 — Обновить README.md в репозитории

Обновляется **только блок между маркерами** `<!-- NANOBOT_SKILLS_START -->` и `<!-- NANOBOT_SKILLS_END -->`.  
Остальное содержимое README.md остаётся нетронутым.

```python
python3 -c "
import pathlib, subprocess, json, base64, re, datetime, sys

REPO       = sys.argv[1]
skills_dir = pathlib.Path.home() / '.nanobot' / 'workspace' / 'skills'
REPO_PATH  = 'README.md'

MARKER_START = '<!-- NANOBOT_SKILLS_START -->'
MARKER_END   = '<!-- NANOBOT_SKILLS_END -->'
TEMPLATE     = '# Nanobot Skills\n\n<!-- NANOBOT_SKILLS_START -->\n<!-- NANOBOT_SKILLS_END -->\n\n## Install\nCopy skill folder to ~/.nanobot/workspace/skills/\n'

def skill_info(d):
    md   = d / 'SKILL.md'
    desc = '—'
    if md.exists():
        txt = md.read_text(encoding='utf-8', errors='ignore')
        m   = re.search(r'^description:\\s*(.+)$', txt, re.M)
        if m:
            desc = m.group(1).strip().split('.')[0]
    return d.name, desc

skills = [skill_info(d) for d in sorted(skills_dir.iterdir()) if d.is_dir()]
now    = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
rows   = ['| Skill | Description |', '|-------|-------------|']       + [f'| `{n}` | {d} |' for n, d in skills]
table  = f'<!-- Updated: {now} -->\n' + '\n'.join(rows)
block  = f'{MARKER_START}\n{table}\n{MARKER_END}'

# Получаем текущий README из репо
r = subprocess.run(
    ['gh', 'api', f'repos/{REPO}/contents/{REPO_PATH}'],
    capture_output=True, text=True, encoding='utf-8'
)

if r.returncode == 0:
    data = json.loads(r.stdout)
    sha  = data['sha']
    b64  = data['content'].replace('\\n', '')
    content = base64.b64decode(b64).decode('utf-8', errors='ignore')
else:
    sha     = None
    content = TEMPLATE
    print('README.md не найден, будет создан из шаблона')

if MARKER_START in content and MARKER_END in content:
    before  = content[:content.index(MARKER_START)]
    after   = content[content.index(MARKER_END) + len(MARKER_END):]
    content = before + block + after
else:
    content = content.rstrip() + '\n\n' + block + '\n'
    print('Маркеры не найдены — таблица добавлена в конец')

body = {
    'message': f'docs: update skills table ({len(skills)} skills)',
    'content': base64.b64encode(content.encode('utf-8')).decode(),
}
if sha:
    body['sha'] = sha

result = subprocess.run(
    ['gh', 'api', f'repos/{REPO}/contents/{REPO_PATH}',
     '--method', 'PUT', '--silent', '--input', '-'],
    input=json.dumps(body),
    capture_output=True, text=True, encoding='utf-8'
)

if result.returncode == 0:
    print(f'README.md обновлён: {len(skills)} навыков')
else:
    print('ОШИБКА обновления README:', result.stderr)
    exit(1)
" OWNER/REPO
```

Заменить `OWNER/REPO` на значение из шага 2.

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
| «Бэкап навыков в GitHub»        | Шаги 1–6 из раздела «Бэкап навыков в GitHub»                 |
| «Сохрани всё в GitHub»          | 🚨 Стоп: `config.json` содержит API-ключи, только локально   |
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
