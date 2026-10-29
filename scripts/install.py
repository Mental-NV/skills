#!/usr/bin/env python3
"""Link selected skills into an explicit destination without replacing files."""
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def install(destination, names, root=ROOT):
    destination = Path(destination).expanduser().resolve()
    operations = []
    for name in dict.fromkeys(names):
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            raise ValueError('Invalid skill name: ' + name)
        source = (root / 'skills' / name).resolve()
        if not source.is_relative_to(root / 'skills') or not (source / 'SKILL.md').is_file():
            raise ValueError('Skill not found: ' + name)
        target = destination / name
        if target.is_symlink() and target.resolve() == source:
            continue
        if target.exists() or target.is_symlink():
            raise ValueError('Destination exists; refusing to replace: ' + str(target))
        operations.append((source, target))
    destination.mkdir(parents=True, exist_ok=True)
    for source, target in operations:
        target.symlink_to(source, target_is_directory=True)
        print(f'{target} -> {source}')
    return len(operations)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('skills', nargs='+', help='Names of skills to link.')
    args = parser.parse_args()
    try:
        count = install(args.destination, args.skills)
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f'Created {count} link(s). Existing matching links are unchanged.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
