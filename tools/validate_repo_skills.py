"""Validate the repo's skill index, skill declarations and local Markdown links."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

LINK = re.compile(r'(?<!\\)\[[^]\n]+\]\(([^()\s]+)\)')
KEY = re.compile(r'^([a-z][a-z0-9_-]*):[ \t]*(.*)$')
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
ROUTE = re.compile(r'^\.agents/skills/[^/]+/SKILL\.md$')


def text_scalar(raw):
    """Accept plain strings or JSON double-quoted strings, never YAML objects."""
    raw = raw.strip()
    if not raw:
        raise ValueError('empty scalar')
    if raw.startswith('"'):
        value = json.loads(raw)
    else:
        if (raw[0] in "\"'[]{}&*!|>%@\x60?#:," or raw == '-' or raw.startswith('- ')
                or re.search(r':(?:\s|$)|(?:^|\s)#', raw)
                or re.fullmatch(r'(?i:~|null|true|false|yes|no|on|off|y|n|[+-]?\.(?:inf|nan))', raw)
                or re.fullmatch(r'[+-]?(?:[0-9][0-9_]*(?:\.[0-9_]*)?|\.[0-9_]+)(?:[eE][+-]?[0-9_]+)?', raw)
                or re.fullmatch(r'(?i:[+-]?0(?:x[0-9a-f_]+|o[0-7_]+|b[01_]+))', raw)
                or re.match(r'^\d{4}-\d{1,2}-\d{1,2}(?:$|[Tt ])', raw)
                or re.fullmatch(r'[+-]?[0-9_]+(?::[0-5]?[0-9])+(?:\.[0-9_]*)?', raw)):
            raise ValueError('only plain text or JSON double-quoted strings are allowed')
        value = raw
    if not isinstance(value, str) or not value.strip() or any(
            ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF
            or c in '\u2028\u2029' for c in value):
        raise ValueError('metadata must be a non-empty single-line string')
    return value


def read_frontmatter(content):
    """Pocket Reel supports exactly single-line name and description; no YAML extras."""
    lines = content.splitlines()
    if not lines or lines[0] != '---' or '---' not in lines[1:]:
        return None
    data = {}
    try:
        for line in lines[1:lines.index('---', 1)]:
            m = KEY.fullmatch(line)
            if not m or m[1] not in {'name', 'description'} or m[1] in data:
                return None
            data[m[1]] = text_scalar(m[2])
    except ValueError:
        return None
    return data if data.keys() == {'name', 'description'} else None


def direct_path(path):
    """Reject symlinks (including in parents), dangling paths and loops for documents."""
    try:
        return path.resolve() == path
    except (OSError, RuntimeError):
        return False


def links(content):
    # Markdown code fences and inline code document examples, not live links.
    content = re.sub(r'(?ms)^(\x60{3,}|~{3,}).*?^\1\s*$', '', content)
    content = re.sub(r'\x60[^\x60\n]+\x60', '', content)
    return LINK.findall(content)


def resolve_link(root, current, raw):
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return 'malformed link'
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    if parsed.path.startswith('/'):
        return 'absolute path is not a repository link'
    try:
        path = (current.parent / unquote(parsed.path)).resolve()
    except (OSError, RuntimeError):
        return 'cannot resolve local link'
    if not path.is_relative_to(root):
        return 'escapes repository'
    if not path.exists():
        return 'missing local link'
    return None


def validate(root):
    root = root.resolve()
    agents = root / 'AGENTS.md'
    index = root / '.agents/skills'
    if not agents.is_file() or not index.is_dir():
        return ['Missing AGENTS.md or .agents/skills directory']
    if not (direct_path(agents) and direct_path(index)):
        return ['Skill index or AGENTS.md may not be symlinked']
    issues = []
    policy = agents.read_text(encoding='utf-8')
    routes = Counter(raw for raw in links(policy) if ROUTE.fullmatch(raw))
    skills = {f.relative_to(root).as_posix(): f for f in sorted(index.glob('*/SKILL.md'))}
    if not skills:
        issues.append('No skill entrypoints found')
    for raw, count in sorted(routes.items()):
        if count != 1:
            issues.append(f'AGENTS.md: duplicate route {raw}')
        if raw not in skills:
            issues.append(f'AGENTS.md: stale route {raw}')
    for raw, p in skills.items():
        if raw not in routes:
            issues.append(f'AGENTS.md: missing route {raw}')
        if not direct_path(p):
            issues.append(f'{raw}: document may not be symlinked')
            continue
        data = read_frontmatter(p.read_text(encoding='utf-8'))
        if data is None:
            issues.append(f'{raw}: unsupported or invalid name/description frontmatter')
        elif not SLUG.fullmatch(data['name']) or data['name'] != p.parent.name:
            issues.append(f'{raw}: invalid or mismatched skill name')
    for p in [agents, *sorted(index.rglob('*.md'))]:
        if not direct_path(p):
            issues.append(f'{p.relative_to(root)}: document may not be symlinked')
            continue
        for raw in links(p.read_text(encoding='utf-8')):
            if problem := resolve_link(root, p, raw):
                issues.append(f'{p.relative_to(root)}: {problem}: {raw}')
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, nargs='?', default=Path.cwd())
    issues = validate(parser.parse_args().root)
    if issues:
        print('\n'.join(issues))
        return 1
    print('Repository skill routing and local links verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
