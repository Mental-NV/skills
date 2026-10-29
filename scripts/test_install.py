from pathlib import Path
import tempfile
import unittest

from install import install


class InstallationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.destination = self.root / 'library'
        for name in ('first', 'second'):
            directory = self.root / 'skills' / name
            directory.mkdir(parents=True)
            (directory / 'SKILL.md').write_text('# Original\n')

    def test_links_are_idempotent_and_reflect_source_edits(self):
        self.assertEqual(install(self.destination, ['first'], self.root), 1)
        self.assertEqual(install(self.destination, ['first'], self.root), 0)
        (self.root / 'skills/first/SKILL.md').write_text('# Updated\n')
        self.assertEqual((self.destination / 'first/SKILL.md').read_text(), '# Updated\n')

    def test_all_conflicts_are_checked_before_creating_links(self):
        self.destination.mkdir()
        conflict = self.destination / 'second'
        conflict.write_text('preserve')
        with self.assertRaises(ValueError):
            install(self.destination, ['first', 'second'], self.root)
        self.assertFalse((self.destination / 'first').exists())
        self.assertEqual(conflict.read_text(), 'preserve')

    def test_broken_or_different_symlinks_are_preserved(self):
        self.destination.mkdir()
        target = self.destination / 'first'
        target.symlink_to(self.root / 'missing')
        with self.assertRaises(ValueError):
            install(self.destination, ['first'], self.root)
        self.assertEqual(target.readlink(), self.root / 'missing')

    def test_missing_skills_do_not_create_destination(self):
        with self.assertRaises(ValueError):
            install(self.destination, ['absent'], self.root)
        self.assertFalse(self.destination.exists())

    def test_path_traversal_and_non_names_are_rejected(self):
        for name in ('../first', '/first', '', 'first/second'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                install(self.destination, [name], self.root)
        self.assertFalse(self.destination.exists())


if __name__ == '__main__':
    unittest.main()
