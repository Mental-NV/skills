#!/usr/bin/env python3
"""Validate skill metadata, repository-local links and offline tool tests."""
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]


def validate(root):
    errors = []
    skills = sorted((root / 'skills').iterdir())
    if not skills:
        errors.append('No skills found.')
    for skill in skills:
        entry = skill / 'SKILL.md'
        if not skill.is_dir() or not entry.is_file():
            errors.append(f'{skill.name}: missing SKILL.md.')
            continue
        match = re.match(r'\A---\n(.*?)\n---(?:\n|$)', entry.read_text(), re.S)
        try:
            metadata = yaml.safe_load(match[1]) if match else None
        except yaml.YAMLError:
            metadata = None
        if not isinstance(metadata, dict):
            errors.append(f'{entry.relative_to(root)}: invalid YAML frontmatter.')
            continue
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill.name) or len(skill.name) > 64:
            errors.append(f'{skill.name}: invalid skill name.')
        if metadata.get('name') != skill.name:
            errors.append(f'{entry.relative_to(root)}: name must match directory.')
        description = metadata.get('description')
        if not isinstance(description, str) or not description.strip():
            errors.append(f'{entry.relative_to(root)}: missing description.')
    documents = [root / 'README.md', root / 'CONTRIBUTING.md', *sorted((root / 'skills').rglob('*.md'))]
    for document in documents:
        text = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', document.read_text(), flags=re.M | re.S)
        for link in re.findall(r'(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)', text):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root) or not target.exists():
                errors.append(f'{document.relative_to(root)}: invalid local link {link}')
    return errors


def main():
    errors = validate(ROOT)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Skill metadata and local documentation links passed.', flush=True)
    for directory in [ROOT / 'scripts', *sorted((ROOT / 'skills').glob('*/scripts'))]:
        if any(directory.glob('test_*.py')):
            subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(directory),
                            '-p', 'test_*.py', '-v'], check=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
