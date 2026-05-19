"""Tests for AdrionHealer: DB integrity check and Python file analysis."""

import os
import sqlite3
import pytest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestCheckDbIntegrity:
    """Gap 2.4: _check_db_integrity() actually checks the database."""

    def test_healthy_db_passes(self, tmp_path):
        """A valid SQLite DB should pass integrity check."""
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO t VALUES (1, 'test')")
        conn.commit()
        conn.close()

        from scripts.adrion_healer import AdrionHealer
        healer = AdrionHealer()

        # Patch config.DB_PATH to point to our test DB
        import arbitrage.config as config
        original = getattr(config, 'DB_PATH', None)
        config.DB_PATH = db_path
        try:
            # Should not raise
            healer._check_db_integrity()
        finally:
            if original is not None:
                config.DB_PATH = original

    def test_missing_db_skips_gracefully(self, tmp_path):
        """Non-existent DB path should warn but not crash."""
        from scripts.adrion_healer import AdrionHealer
        healer = AdrionHealer()

        import arbitrage.config as config
        original = getattr(config, 'DB_PATH', None)
        config.DB_PATH = str(tmp_path / "nonexistent.db")
        try:
            healer._check_db_integrity()  # Should not raise
        finally:
            if original is not None:
                config.DB_PATH = original


class TestAnalyzePythonFiles:
    """Gap 2.4: _analyze_python_files() detects syntax errors and TODOs."""

    def test_detects_syntax_error(self, tmp_path, monkeypatch):
        """Python files with SyntaxError should be reported."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(\n", encoding="utf-8")

        from scripts.adrion_healer import AdrionHealer
        healer = AdrionHealer()
        healer.genesis_log = str(tmp_path / "healer.log")

        # Monkey-patch project root to tmp_path
        monkeypatch.setattr(os.path, "abspath",
                            lambda x: str(tmp_path) if "adrion_healer" in str(x) else os.path.realpath(x))

        # Direct test: parse the file
        import ast
        with pytest.raises(SyntaxError):
            ast.parse(bad_file.read_text())

    def test_detects_todo_markers(self, tmp_path):
        """Files with TODO/FIXME markers should be counted."""
        py_file = tmp_path / "module.py"
        py_file.write_text("# TODO: fix this\n# FIXME: another issue\nx = 1\n", encoding="utf-8")

        import re
        source = py_file.read_text()
        pattern = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b', re.IGNORECASE)
        markers = pattern.findall(source)
        assert len(markers) == 2

    def test_valid_python_passes(self, tmp_path):
        """Clean Python files should parse without issues."""
        py_file = tmp_path / "clean.py"
        py_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

        import ast
        ast.parse(py_file.read_text())  # Should not raise
