"""Skill system — Delta's coding mastery.

Setiap skill adalah folder di ``delta/skills/<name>/`` berisi:

* ``skill.json`` — metadata (name, description, category, tags, version)

* ``skill.md``   — instruksi yang disuntikkan ke konteks sistem LLM

Skill yang aktif di-persist ke ``config.active_skills`` dan isinya

digabung ke system context di ``_process_with_llm``.

"""

import json

import os

import re

from dataclasses import dataclass, field

from typing import Dict, List, Optional

SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

DEFAULT_SKILLS_DIR = os.path.join(

    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills"

)

# Skill coding yang aktif secara default (campuran skill andalan).

DEFAULT_ACTIVE: List[str] = [

    "ui-ux-pro-max",

    "clean-architect",

    "testing-guru",

    "security-sentinel",

]

SKILL_HEADER = (

    "## ACTIVE SKILLS — master this set of disciplines\n"

    "You are a world-class engineer. Apply every active skill below to ALL "

    "code you write, review, or explain. Skills are not optional and are not "

    "suggestions. When skills overlap, satisfy all of them. When a task "

    "conflicts with a skill rule, follow the skill rule."

)

@dataclass

class Skill:

    name: str

    description: str = ""

    category: str = "Coding"

    tags: List[str] = field(default_factory=list)

    version: str = "1.0.0"

    content: str = ""

    dir: str = ""

class SkillManager:

    """Menemukan, mengaktifkan, dan merakit instruksi skill."""

    def __init__(

        self,

        config,

        skills_dir: Optional[str] = None,

        user_skills_dir: Optional[str] = None,

    ):

        self.config = config

        self.skills_dir = skills_dir or DEFAULT_SKILLS_DIR

        self.user_skills_dir = user_skills_dir or (

            os.path.join(config.data_dir, "skills") if config else None

        )

        self._cache: Dict[str, Skill] = {}

        self._load()

        active = config.get("active_skills") if config else None

        if not active:

            if config:

                config.set("active_skills", list(DEFAULT_ACTIVE))

                config.save()

            self._active: List[str] = list(DEFAULT_ACTIVE)

        else:

            self._active = [

                a for a in active if self.get_skill(a) is not None

            ]

    # ------------------------------------------------------------------ load

    def _load(self) -> None:

        self._cache = {}

        for base in (self.skills_dir, self.user_skills_dir):

            if not base or not os.path.isdir(base):

                continue

            for entry in sorted(os.listdir(base)):

                skill_path = os.path.join(base, entry)

                meta_path = os.path.join(skill_path, "skill.json")

                content_path = os.path.join(skill_path, "skill.md")

                if not os.path.isdir(skill_path) or not os.path.isfile(meta_path):

                    continue

                if not SAFE_NAME.match(entry):

                    continue

                try:

                    with open(meta_path, "r", encoding="utf-8") as f:

                        meta = json.load(f)

                except (json.JSONDecodeError, IOError):

                    continue

                content = ""

                if os.path.isfile(content_path):

                    with open(content_path, "r", encoding="utf-8") as f:

                        content = f.read().strip()

                self._cache[entry] = Skill(

                    name=entry,

                    description=str(meta.get("description", "")).strip(),

                    category=str(meta.get("category", "Coding")).strip(),

                    tags=[str(t) for t in meta.get("tags", [])],

                    version=str(meta.get("version", "1.0.0")),

                    content=content,

                    dir=skill_path,

                )

    def list_skills(self) -> List[Skill]:

        """Semua skill yang tersedia (terurut nama)."""

        return [self._cache[k] for k in sorted(self._cache)]

    def get_skill(self, name: str) -> Optional[Skill]:

        """Skill by name, atau None jika tidak ditemukan."""

        return self._cache.get(name)

    # -------------------------------------------------------------- activate

    def active_names(self) -> List[str]:

        return list(self._active)

    def active_skills(self) -> List[Skill]:

        return [self._cache[n] for n in self._active if n in self._cache]

    def is_active(self, name: str) -> bool:

        return name in self._active

    def _persist(self) -> None:

        if self.config:

            self.config.set("active_skills", list(self._active))

            self.config.save()

    def activate(self, name: str) -> bool:

        """Aktifkan skill. Return True jika berhasil."""

        if name not in self._cache:

            return False

        if name not in self._active:

            self._active.append(name)

            self._persist()

        return True

    def deactivate(self, name: str) -> bool:

        """Nonaktifkan skill. Return True jika berhasil."""

        if name not in self._cache:

            return False

        if name in self._active:

            self._active.remove(name)

            self._persist()

        return True

    def set_active(self, names: List[str]) -> None:

        self._active = [n for n in names if n in self._cache]

        self._persist()

    # ------------------------------------------------------------- context

    def build_context(self) -> str:

        """Instruksi semua skill aktif, siap disuntikkan ke system context."""

        active = self.active_skills()

        if not active:

            return ""

        blocks = [SKILL_HEADER]

        for skill in active:

            if not skill.content:

                continue

            blocks.append(f"### Skill: {skill.name}")

            blocks.append(skill.content)

        return "\n\n".join(blocks) + "\n"

    # -------------------------------------------------------------- search

    def find(self, query: str) -> List[Skill]:

        """Cari skill berdasarkan nama, deskripsi, atau tag."""

        q = query.lower()

        hits = []

        for skill in self.list_skills():

            haystack = " ".join(

                [skill.name, skill.description, skill.category, " ".join(skill.tags)]

            ).lower()

            if q in haystack:

                hits.append(skill)

        return hits