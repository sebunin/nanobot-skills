import pathlib, re, sys

home = pathlib.Path.home()
nanobot = home / '.nanobot'
targets = [
    nanobot / 'workspace' / 'skills',
    nanobot / 'workspace' / 'memory',
    nanobot / 'cron'
]

# Паттерны для поиска строк с секретами
patterns = ['api.?key', 'token', 'password', 'secret', 'claw_', 'sk-', 'xoxb-', 'xapp-']
found = []

def extract_value(line):
    """Извлекает потенциальное значение секрета из строки."""
    # Ищем после = или :, возможно в кавычках
    # Примеры:
    #   API_KEY="value"
    #   token: value
    #   password = 'value'
    # Исключаем URL и пути: значение не должно содержать / или \ или :// или заканчиваться на .ext
    m = re.search(r'[:=]\s*([\'"]?)([a-zA-Z0-9_\-\.\+/=]{10,})\1\s*$', line)
    if m:
        val = m.group(2)
        if not re.search(r'[/\\]|://|\.(?:py|md|txt|json|yml|yaml|toml|ini|sh|bash|zsh|fish|ps1|psm1|psd1)$', val):
            return val
        return None
    # Без кавычек, но длинное значение
    m2 = re.search(r'[:=]\s*([a-zA-Z0-9_\-\.\+/=]{10,})\s*$', line)
    if m2:
        val = m2.group(1)
        if not re.search(r'[/\\]|://|\.(?:py|md|txt|json|yml|yaml|toml|ini|sh|bash|zsh|fish|ps1|psm1|psd1)$', val):
            return val
    return None

def looks_like_real_secret(value):
    """Определяет, похоже ли значение на реальный секрет."""
    if not value:
        return False
    # Должно содержать только разрешённые символы (base64-подобные)
    if not re.fullmatch(r'[a-zA-Z0-9_\-\.\+/=]+', value):
        return False
    # Не должно содержать явных индикаторов примеров
    example_indicators = ['YOUR_', 'your_', 'YOUR-', 'your-', 'example', 'sample', 'test', 'TEST', 'EXAMPLE', 'SAMPLE', 'placeholder', 'dummy', 'fake', 'xxx', '***', '...', 'replace', 'REPLACE', 'enter', 'ENTER', 'insert', 'INSERT', 'set_', 'SET_', 'config', 'CONFIG']
    value_lower = value.lower()
    if any(ind.lower() in value_lower for ind in example_indicators):
        return False
    # Не должно быть похоже на путь или URL
    if re.search(r'[/\\]|://', value):
        return False
    # Не должно заканчиваться на расширение файла (исключаем .py, .md, .txt, .json, .yml, .yaml, .sh, .ps1 и т.д.)
    if re.search(r'\.(py|md|txt|json|yml|yaml|sh|ps1|psm1|psd1|ini|toml|cfg|config)$', value, re.I):
        return False
    # Длина: обычно >= 10, но для токенов может быть меньше; оставим >= 10 для безопасности
    if len(value) < 10:
        return False
    return True

for t in targets:
    if not t.exists():
        continue
    for f in t.rglob('*'):
        if not f.is_file() or f.suffix in {'.pyc', '.png', '.jpg', '.jpeg', '.gif'}:
            continue
        # Исключаем сам скрипт проверки
        if f.name == 'check_secrets.py' and f.parent.name == 'backup':
            continue
        try:
            txt = f.read_text(encoding='utf-8', errors='ignore')
            secret_found = False
            for p in patterns:
                if secret_found:
                    break
                # Ищем все строки, где встречается паттерн
                for match in re.finditer(p, txt, re.I):
                    # Получаем строку, в которой найдено совпадение
                    line_start = txt.rfind('\n', 0, match.start()) + 1
                    line_end = txt.find('\n', match.start())
                    if line_end == -1:
                        line_end = len(txt)
                    line = txt[line_start:line_end].strip()
                    # Пытаемся извлечь значение
                    value = extract_value(line)
                    if value and looks_like_real_secret(value):
                        found.append(str(f) + ' [' + p + '] -> ' + value[:20] + '...')
                        secret_found = True
                        break  # выходим из внутреннего цикла, внешний прервётся по флагу
        except Exception:
            pass

if found:
    print('СТОП! Найдены потенциальные секреты:')
    for x in found:
        print(' -', x)
    sys.exit(1)
else:
    print('OK: секретов не обнаружено')
