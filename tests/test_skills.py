# tests/test_skills.py
"""Tests for the Delta skill system (SkillManager)."""
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from delta.core.config import DeltaConfig
from delta.modules.skills import (
    SkillManager,
    DEFAULT_SKILLS_DIR,
    DEFAULT_ACTIVE,
    SKILL_HEADER,
    SAFE_NAME,
)

class _FakeConfig:
    """Config stub that satisfies SkillManager's read/write needs."""

    def __init__(self):
        self.data_dir = tempfile.mkdtemp(prefix="delta_test_")
        self.active_skills = []
        self._store = {}

    def get(self, key, default=None):
        return self._store.get(key, default)

    def set(self, key, value):
        self._store[key] = value

    def save(self):
        pass

def _write_skill(base, name, description="desc", category="Coding", tags=None,
                 content="instructions", version="1.0.0", bad_name=False):
    """Helper: create a skill folder with skill.json + skill.md."""
    safe = name.replace("/", "_") if not bad_name else name
    sdir = os.path.join(base, safe)
    os.makedirs(sdir, exist_ok=True)
    meta = {
        "name": name,
        "description": description,
        "category": category,
        "tags": tags or [],
        "version": version,
    }
    with open(os.path.join(sdir, "skill.json"), "w") as f:
        json.dump(meta, f)
    with open(os.path.join(sdir, "skill.md"), "w") as f:
        f.write(content)
    return sdir

class TestSkillLoading(unittest.TestCase):
    """Loading from disk."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="delta_skills_")
        self.config = _FakeConfig()
        self.sm = SkillManager(self.config, skills_dir=self.tmp)

    def _populate(self):
        _write_skill(self.tmp, "ui-ux-pro-max", category="Frontend")
        _write_skill(self.tmp, "clean-architect", category="Architecture")
        _write_skill(self.tmp, "testing-guru", category="Engineering")

    def test_loads_all_skills(self):
        self._populate()
        sm = SkillManager(self.config, skills_dir=self.tmp)
        names = {s.name for s in sm.list_skills()}
        self.assertIn("ui-ux-pro-max", names)
        self.assertIn("clean-architect", names)
        self.assertIn("testing-guru", names)

    def test_skill_metadata(self):
        _write_skill(self.tmp, "frontend-master", category="Frontend",
                     tags=["html", "css"], version="1.2.3")
        sm = SkillManager(self.config, skills_dir=self.tmp)
        s = sm.get_skill("frontend-master")
        self.assertIsNotNone(s)
        self.assertEqual(s.category, "Frontend")
        self.assertEqual(s.tags, ["html", "css"])
        self.assertEqual(s.version, "1.2.3")

    def test_invalid_name_rejected(self):
        _write_skill(self.tmp, "Bad/Name Space", bad_name=True)
        sm = SkillManager(self.config, skills_dir=self.tmp)
        self.assertNotIn("Bad/Name Space", {s.name for s in sm.list_skills()})

    def test_safe_name_regex(self):
        self.assertIsNotNone(SAFE_NAME.match("ui-ux-pro-max"))
        self.assertIsNotNone(SAFE_NAME.match("v2"))
        self.assertIsNone(SAFE_NAME.match("Bad"))
        self.assertIsNone(SAFE_NAME.match("-bad"))
        self.assertIsNone(SAFE_NAME.match("bad name"))

    def test_malformed_json_skipped(self):
        sdir = _write_skill(self.tmp, "broken-json", content="instr")
        with open(os.path.join(sdir, "skill.json"), "w") as f:
            f.write("{ not valid json")
        sm = SkillManager(self.config, skills_dir=self.tmp)
        self.assertIsNone(sm.get_skill("broken-json"))

    def test_folder_without_json_skipped(self):
        sdir = os.path.join(self.tmp, "no-meta")
        os.makedirs(sdir)
        with open(os.path.join(sdir, "skill.md"), "w") as f:
            f.write("instr")
        sm = SkillManager(self.config, skills_dir=self.tmp)
        self.assertIsNone(sm.get_skill("no-meta"))

class TestSkillActivation(unittest.TestCase):
    """Activating, deactivating, persisting."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="delta_skills_")
        self.config = _FakeConfig()
        _write_skill(self.tmp, "clean-architect")
        _write_skill(self.tmp, "testing-guru")
        self.sm = SkillManager(self.config, skills_dir=self.tmp)

    def test_defaults_activated_when_none_configured(self):
        self.config.active_skills = []
        sm = SkillManager(self.config, skills_dir=self.tmp)
        # clean-architect + testing-guru are in DEFAULT_ACTIVE and exist here
        for name in ("clean-architect", "testing-guru"):
            if name in DEFAULT_ACTIVE:
                self.assertTrue(sm.is_active(name))
        self.assertGreaterEqual(len(sm.active_skills()), 1)

    def test_activate_unknown_returns_false(self):
        self.assertFalse(self.sm.activate("does-not-exist"))

    def test_activate_and_deactivate(self):
        self.assertTrue(self.sm.activate("testing-guru"))
        self.assertTrue(self.sm.is_active("testing-guru"))
        self.assertTrue(self.sm.deactivate("testing-guru"))
        self.assertFalse(self.sm.is_active("testing-guru"))

    def test_persist_called_on_activate(self):
        self.sm.activate("testing-guru")
        self.assertIn("testing-guru", self.config._store.get("active_skills", []))

    def test_set_active_keeps_only_known(self):
        self.sm.set_active(["clean-architect", "ghost-skill", "testing-guru"])
        names = set(self.sm.active_names())
        self.assertIn("clean-architect", names)
        self.assertIn("testing-guru", names)
        self.assertNotIn("ghost-skill", names)

class TestBuildContext(unittest.TestCase):
    """build_context() merges active skills into system prompt text."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="delta_skills_")
        self.config = _FakeConfig()
        _write_skill(self.tmp, "clean-architect", content="act-on-everything")
        _write_skill(self.tmp, "testing-guru", content="ship-tests")
        self.sm = SkillManager(self.config, skills_dir=self.tmp)
        self.sm.activate("clean-architect")
        self.sm.activate("testing-guru")

    def test_header_present(self):
        ctx = self.sm.build_context()
        self.assertIn(SKILL_HEADER, ctx)

    def test_all_active_contents_present(self):
        ctx = self.sm.build_context()
        self.assertIn("act-on-everything", ctx)
        self.assertIn("ship-tests", ctx)

    def test_inactive_content_absent(self):
        _write_skill(self.tmp, "frontend-master", content="frontend-only")
        cm = SkillManager(self.config, skills_dir=self.tmp)
        cm.activate("frontend-master")
        ctx = cm.build_context()
        self.assertIn("frontend-only", ctx)

    def test_empty_when_no_active(self):
        sm = SkillManager(self.config, skills_dir=self.tmp)
        sm.set_active([])
        self.assertEqual(sm.build_context(), "")

class TestSearch(unittest.TestCase):
    """find() searches name, description, category, and tags."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="delta_skills_")
        self.config = _FakeConfig()
        _write_skill(self.tmp, "clean-architect", description="SOLID design",
                     category="Architecture", tags=["architecture", "solid"])
        _write_skill(self.tmp, "performance-optimizer", description="speed & caching",
                     category="Engineering", tags=["performance", "caching"])
        self.sm = SkillManager(self.config, skills_dir=self.tmp)

    def test_search_by_tag(self):
        hits = self.sm.find("caching")
        names = {s.name for s in hits}
        self.assertIn("performance-optimizer", names)
        self.assertNotIn("clean-architect", names)

    def test_search_by_description(self):
        hits = self.sm.find("solid")
        self.assertTrue(all(s.name == "clean-architect" for s in hits))

    def test_search_case_insensitive(self):
        hits = self.sm.find("ARCHITECTURE")
        self.assertTrue(any(s.name == "clean-architect" for s in hits))

    def test_search_no_match(self):
        self.assertEqual(self.sm.find("nonexistentterm"), [])

class TestBundledSkills(unittest.TestCase):
    """The real shipped skills in delta/skills/ must be valid and loadable."""

    def test_bundled_dir_loads(self):
        sm = SkillManager(DeltaConfig(), skills_dir=DEFAULT_SKILLS_DIR)
        # Every shipped skill must parse (non-empty content required by design).
        for skill in sm.list_skills():
            self.assertTrue(skill.name)
            self.assertTrue(skill.content, f"Skill {skill.name} has empty content")

    def test_bundled_has_core_skills(self):
        sm = SkillManager(DeltaConfig(), skills_dir=DEFAULT_SKILLS_DIR)
        names = {s.name for s in sm.list_skills()}
        for core in ("ui-ux-pro-max", "clean-architect", "security-sentinel"):
            self.assertIn(core, names)

if __name__ == "__main__":
    unittest.main()
