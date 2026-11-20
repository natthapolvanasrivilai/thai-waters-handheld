"""Coverage for valid routing, stale/missing skills, and bad local links."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_repo_skills import validate


class RepositorySkills(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.route = '[Sample](.agents/skills/sample/SKILL.md)'
        self.write('AGENTS.md', self.route)
        self.skill = '.agents/skills/sample/SKILL.md'
        self.body = '---\nname: sample\ndescription: Sample work.\n---\n[Detail](references/detail.md)\n'
        self.write(self.skill, self.body)
        self.write('.agents/skills/sample/references/detail.md',
                   '[Repository](../../../../AGENTS.md#anchor) [External](https://example.com/absent)')

    def write(self, path, content):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')

    def test_valid(self):
        self.assertEqual(validate(self.root), [])

    def test_route_drift(self):
        self.write('AGENTS.md', '[Stale](.agents/skills/old/SKILL.md)')
        errors = validate(self.root)
        self.assertTrue(any('missing route' in e for e in errors))
        self.assertTrue(any('stale route' in e for e in errors))

    def test_duplicate_route(self):
        self.write('AGENTS.md', self.route + '\n' + self.route)
        self.assertTrue(any('duplicate route' in e for e in validate(self.root)))

    def test_bad_name_or_empty_description(self):
        self.write(self.skill, self.body.replace('name: sample', 'name: renamed'))
        self.assertTrue(any('mismatched skill name' in e for e in validate(self.root)))
        self.write(self.skill, self.body.replace('Sample work.', ''))
        self.assertTrue(any('invalid name/description frontmatter' in e for e in validate(self.root)))

    def test_reject_malformed_or_non_text_frontmatter(self):
        invalid = ['"unclosed', '[Unexpected, sequence]', '{mapping: value}', 'null',
                   '~', 'false', '42', '1.2e3', '.Inf', '0x42', '2026-11-20', '12:34:56',
                   '|', '&anchor', '*alias', json.dumps('blank\nline'), json.dumps(chr(0xD800)),
                   '"quoted" trailing', '"   "', 'bare: with colon', 'plain # comment']
        for value in invalid:
            with self.subTest(value=value):
                self.write(self.skill, self.body.replace('Sample work.', value))
                self.assertTrue(any('invalid name/description frontmatter' in e
                                    for e in validate(self.root)), value)
        for line in ('not yaml: [', 'metadata: {}', 'description: duplicated'):
            with self.subTest(line=line):
                self.write(self.skill, self.body.replace('name: sample', 'name: sample\n' + line))
                self.assertTrue(any('invalid name/description frontmatter' in e
                                    for e in validate(self.root)))

    def test_json_quoted_strings(self):
        self.write(self.skill, self.body.replace('name: sample', 'name: "sample"')
                   .replace('Sample work.', json.dumps('Scope: "example" #checked')))
        self.assertEqual(validate(self.root), [])

    def test_missing_or_outside_link(self):
        self.write(self.skill, self.body + '[Missing](lost.md) [Outside](../../../../outside)')
        errors = validate(self.root)
        self.assertTrue(any('missing local link' in e for e in errors))
        self.assertTrue(any('escapes repository' in e for e in errors))

    def test_skill_symlink_does_not_escape(self):
        p = self.root / self.skill
        p.unlink()
        try:
            p.symlink_to(self.root.parent / 'skill-outside-repository.md')
        except OSError:
            self.skipTest('symlinks unavailable')
        self.assertTrue(any('document may not be symlinked' in e for e in validate(self.root)))

    def test_symlinked_skill_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as path:
            target = Path(path)
            (target / 'SKILL.md').write_text(self.body.replace('name: sample', 'name: foreign'))
            alias = self.root / '.agents/skills/foreign'
            try:
                alias.symlink_to(target, target_is_directory=True)
            except OSError:
                self.skipTest('symlinks unavailable')
            self.write('AGENTS.md', self.route + '\n[Foreign](.agents/skills/foreign/SKILL.md)')
            self.assertTrue(any('foreign/SKILL.md: document may not be symlinked' in e
                                for e in validate(self.root)))

    def test_ignores_example_markdown_in_code(self):
        self.write(self.skill, self.body + '~~~markdown\n[Example](not-real.md)\n~~~\n')
        self.assertEqual(validate(self.root), [])


if __name__ == '__main__':
    unittest.main()
