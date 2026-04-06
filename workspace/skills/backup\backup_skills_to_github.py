#!/usr/bin/env python3
"""
Бэкап навыков в GitHub с автоматическим обновлением README.md.
Требует: gh CLI с настроенной авторизацией.
"""
import pathlib, subprocess, json, base64, re, datetime, sys

REPO = 'sebunin/nanobot-skills'  # можно переопределить через env
skills_dir = pathlib.Path.home() / '.nanobot' / 'workspace' / 'skills'
PREFIX = 'workspace/skills'
README_PATH = 'README.md'
MARKER_START = '<!-- NANOBOT_SKILLS_START -->'
MARKER_END = '<!-- NANOBOT_SKILLS_END -->'

def run(cmd, input=None):
    # input должен быть bytes если capture_output=True и text=False
    if input is not None and isinstance(input, str):
        input = input.encode('utf-8')
    r = subprocess.run(cmd, capture_output=True, input=input)
    # Декодируем вывод, игнорируя ошибки
    stdout = r.stdout.decode('utf-8', errors='ignore') if r.stdout else ''
    stderr = r.stderr.decode('utf-8', errors='ignore') if r.stderr else ''
    return type('Result', (), {'returncode': r.returncode, 'stdout': stdout, 'stderr': stderr})

def check_secrets():
    """Запускает check_secrets.py и возвращает (ok, output)"""
    script = pathlib.Path(__file__).parent / 'check_secrets.py'
    if not script.exists():
        return True, 'check_secrets.py не найден'
    r = run([sys.executable, str(script)])
    output = (r.stdout or '') + (r.stderr or '')
    return r.returncode == 0, output

def gh_api(method, path, data=None, silent=False):
    cmd = ['gh', 'api', path, '--method', method]
    if silent:
        cmd.append('--silent')
    if data:
        cmd += ['--input', '-']
        r = run(cmd, input=json.dumps(data))
    else:
        r = run(cmd)
    return r

def get_file_sha(repo_path):
    r = gh_api('GET', f'repos/{REPO}/contents/{repo_path}', silent=True)
    if r.returncode == 0:
        try:
            return json.loads(r.stdout).get('sha')
        except:
            return None
    return None

def get_remote_content(repo_path):
    r = gh_api('GET', f'repos/{REPO}/contents/{repo_path}', silent=True)
    if r.returncode == 0:
        b64 = json.loads(r.stdout).get('content', '').replace('\\n', '')
        try:
            return base64.b64decode(b64)
        except:
            return None
    return None

def upload_skills():
    changed = []
    skipped = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        for f in skill_dir.rglob('*'):
            if not f.is_file():
                continue
            rel = f.relative_to(skills_dir)
            repo_path = PREFIX + '/' + str(rel).replace('\\\\', '/')
            local_bytes = f.read_bytes()
            remote_bytes = get_remote_content(repo_path)
            if remote_bytes == local_bytes:
                skipped.append(repo_path)
                continue
            sha = get_file_sha(repo_path)
            body = {
                'message': f'skills: update {rel}',
                'content': base64.b64encode(local_bytes).decode(),
            }
            if sha:
                body['sha'] = sha
            r = gh_api('PUT', f'repos/{REPO}/contents/{repo_path}', body, silent=False)
            if r.returncode == 0:
                changed.append(repo_path)
            else:
                print(f'ОШИБКА загрузки {repo_path}: {r.stderr.strip()}')
    print(f'Загрузка завершена. Обновлено: {len(changed)}, без изменений: {len(skipped)}')
    return changed, skipped

def update_readme():
    # Собираем таблицу навыков
    def skill_info(d):
        md = d / 'SKILL.md'
        desc = '—'
        if md.exists():
            txt = md.read_text(encoding='utf-8', errors='ignore')
            m = re.search(r'^description:\\s*(.+)$', txt, re.M)
            if m:
                desc = m.group(1).strip().split('.')[0]
        return d.name, desc

    skills = [skill_info(d) for d in sorted(skills_dir.iterdir()) if d.is_dir()]
    now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    rows = ['| Skill | Description |', '|-------|-------------|'] + [f'| `{n}` | {d} |' for n, d in skills]
    table = f'<!-- Updated: {now} -->\n' + '\n'.join(rows)
    block = f'{MARKER_START}\n{table}\n{MARKER_END}'

    # Получаем текущий README
    r = gh_api('GET', f'repos/{REPO}/contents/{README_PATH}', silent=True)
    if r.returncode == 0:
        data = json.loads(r.stdout)
        sha = data['sha']
        b64 = data['content'].replace('\\n', '')
        content = base64.b64decode(b64).decode('utf-8', errors='ignore')
    else:
        sha = None
        content = f'# Nanobot Skills\n\n{MARKER_START}\n{MARKER_END}\n'

    # Заменяем блок
    if MARKER_START in content and MARKER_END in content:
        before = content[:content.index(MARKER_START)]
        after = content[content.index(MARKER_END) + len(MARKER_END):]
        new_content = before + block + after
    else:
        new_content = content.rstrip() + '\n\n' + block + '\n'

    body = {
        'message': f'docs: update skills table ({len(skills)} skills)',
        'content': base64.b64encode(new_content.encode('utf-8')).decode(),
    }
    if sha:
        body['sha'] = sha

    r = gh_api('PUT', f'repos/{REPO}/contents/{README_PATH}', body, silent=False)
    if r.returncode == 0:
        print(f'README.md обновлён: {len(skills)} навыков')
        return True
    else:
        print('ОШИБКА обновления README:', r.stderr.strip())
        return False

def main():
    print('=== Бэкап навыков в GitHub ===')
    # 1. Проверка секретов
    ok, out = check_secrets()
    print(out)
    if not ok or 'СТОП!' in out:
        print('Обнаружены потенциальные секреты. Прерываю.')
        sys.exit(1)

    # 2. Загрузка файлов
    print('Загрузка файлов...')
    upload_skills()

    # 3. Обновление README
    print('Обновление README.md...')
    if update_readme():
        print('✅ Бэкап завершён успешно.')
    else:
        print('⚠️ Бэкап завершён с ошибками при обновлении README.')

if __name__ == '__main__':
    main()
