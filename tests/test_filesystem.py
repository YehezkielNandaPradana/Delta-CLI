# tests/test_filesystem.py
"""Tests for the file system module (auto-approved operations)."""
import os
import tempfile
import unittest

from delta.modules.filesystem import FileSystemModule

from delta.ai.intent import FILLER_WORDS

class TestFileSystemModule(unittest.TestCase):
    """Test file/folder operations."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fs = FileSystemModule(cwd=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_mkdir(self):
        ok, msg = self.fs.mkdir("src")
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.isdir(os.path.join(self.tmp.name, "src")))

    def test_mkdir_parents(self):
        ok, msg = self.fs.mkdir("a/b/c", parents=True)
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.isdir(os.path.join(self.tmp.name, "a/b/c")))

    def test_write_and_read(self):
        ok, msg = self.fs.write("hello.txt", "Halo Dunia")
        self.assertTrue(ok, msg)
        ok, content = self.fs.read("hello.txt")
        self.assertTrue(ok)
        self.assertEqual(content, "Halo Dunia")

    def test_write_nested(self):
        ok, msg = self.fs.write("src/app.py", "print('hi')")
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp.name, "src/app.py")))

    def test_write_newline_escape(self):
        self.fs.write("code.py", "def f():\\n    return 1")
        ok, content = self.fs.read("code.py")
        self.assertTrue(ok)
        self.assertEqual(content, "def f():\n    return 1")

    def test_touch(self):
        ok, msg = self.fs.touch("empty.txt")
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp.name, "empty.txt")))
        self.assertEqual(os.path.getsize(os.path.join(self.tmp.name, "empty.txt")), 0)

    def test_edit(self):
        self.fs.write("note.txt", "alpha beta gamma")
        ok, msg = self.fs.edit("note.txt", "beta", "BETA")
        self.assertTrue(ok, msg)
        _, content = self.fs.read("note.txt")
        self.assertEqual(content, "alpha BETA gamma")

    def test_edit_missing_text(self):
        self.fs.write("note.txt", "alpha")
        ok, msg = self.fs.edit("note.txt", "zzz", "yyy")
        self.assertFalse(ok)

    def test_edit_missing_file(self):
        ok, msg = self.fs.edit("nope.txt", "a", "b")
        self.assertFalse(ok)

    def test_append(self):
        self.fs.write("log.txt", "line1")
        ok, msg = self.fs.append("log.txt", "line2")
        self.assertTrue(ok, msg)
        _, content = self.fs.read("log.txt")
        self.assertEqual(content, "line1\nline2")

    def test_read_missing_file(self):
        ok, content = self.fs.read("missing.txt")
        self.assertFalse(ok)

    def test_read_max_lines(self):
        self.fs.write("many.txt", "\n".join(f"line{i}" for i in range(10)))
        ok, content = self.fs.read("many.txt", max_lines=3)
        self.assertTrue(ok)
        self.assertIn("line2", content)
        self.assertIn("7 baris lagi", content)

    def test_cd_valid(self):
        self.fs.mkdir("proyek")
        ok, msg, new_cwd = self.fs.cd("proyek")
        self.assertTrue(ok, msg)
        self.assertEqual(os.path.abspath(new_cwd), os.path.join(self.tmp.name, "proyek"))

    def test_cd_invalid(self):
        ok, msg, new_cwd = self.fs.cd("tidak-ada")
        self.assertFalse(ok)
        self.assertEqual(new_cwd, self.tmp.name)

    def test_list_dir(self):
        self.fs.mkdir("sub")
        self.fs.write("a.txt", "x")
        ok, entries = self.fs.list_dir()
        self.assertTrue(ok)
        names = {e["name"] for e in entries}
        self.assertIn("sub", names)
        self.assertIn("a.txt", names)

    def test_tree(self):
        self.fs.mkdir("src", parents=True)
        self.fs.write("src/main.py", "pass")
        ok, body = self.fs.tree("", max_depth=2)
        self.assertTrue(ok)
        self.assertIn("src", body)
        self.assertIn("main.py", body)

    def test_dirinfo(self):
        self.fs.write("app.py", "x" * 100)
        self.fs.mkdir("data")
        ok, stats = self.fs.dirinfo()
        self.assertTrue(ok)
        self.assertEqual(stats["files"], 1)
        self.assertEqual(stats["dirs"], 1)
        self.assertIn(".py", stats["extensions"])
        self.assertEqual(stats["extensions"][".py"]["size"], 100)

    def test_filler_words(self):
        self.assertIn("buat", FILLER_WORDS)
        self.assertIn("bikin", FILLER_WORDS)
        self.assertIn("folder", FILLER_WORDS)

if __name__ == "__main__":
    unittest.main()
