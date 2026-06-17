import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.graph.services import GraphService
from apps.skills.models import Skill

DATA_DIR = settings.BASE_DIR / "data"
SKILLS_CSV = DATA_DIR / "skills.csv"
DEPS_CSV = DATA_DIR / "dependencies.csv"

VALID_LEVELS = {"beginner", "intermediate", "advanced", "expert"}


def _read_skills(path: Path) -> list[dict]:
    """Читает CSV-файл с навыками и возвращает список строк в виде словарей."""
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class Command(BaseCommand):
    """Команда управления для первоначальной загрузки навыков и зависимостей из CSV-файлов
    в базу данных (модель Skill) и граф навыков (GraphService). Идемпотентна: повторный
    запуск не создаёт дубликаты навыков благодаря get_or_create.
    """

    help = "Загружает навыки и зависимости из backend/data/*.csv в БД и граф"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skills",
            type=Path,
            default=SKILLS_CSV,
            help="Путь к CSV-файлу с навыками (default: backend/data/skills.csv)",
        )
        parser.add_argument(
            "--deps",
            type=Path,
            default=DEPS_CSV,
            help="Путь к CSV-файлу с зависимостями (default: backend/data/dependencies.csv)",
        )

    def handle(self, *args, **options):
        """Выполняет загрузку: сначала создаёт навыки из skills CSV, затем добавляет
        зависимости из deps CSV в граф через GraphService. Некорректные строки пропускаются
        с выводом предупреждения в stderr.
        """
        skills_path: Path = options["skills"]
        deps_path: Path = options["deps"]

        if not skills_path.exists():
            self.stderr.write(self.style.ERROR(f"Файл не найден: {skills_path}"))
            return
        if not deps_path.exists():
            self.stderr.write(self.style.ERROR(f"Файл не найден: {deps_path}"))
            return

        # --- Навыки ---
        self.stdout.write(f"Читаю навыки из {skills_path} ...")
        rows = _read_skills(skills_path)
        created_count = 0
        skipped = 0

        for row in rows:
            name = row.get("name", "").strip()
            level = row.get("level", "beginner").strip()
            description = row.get("description", "").strip()
            tags_raw = row.get("tags", "").strip()
            is_verified = row.get("is_verified", "false").strip().lower() == "true"

            if not name:
                self.stderr.write(f"  Пропущена строка без name: {row}")
                skipped += 1
                continue
            if level not in VALID_LEVELS:
                self.stderr.write(
                    f'  Неверный уровень "{level}" для "{name}", установлен beginner'
                )
                level = "beginner"

            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

            _, created = Skill.objects.get_or_create(
                name=name,
                defaults={
                    "level": level,
                    "description": description,
                    "tags": tags,
                    "is_verified": is_verified,
                },
            )
            if created:
                created_count += 1

        total = len(rows) - skipped
        self.stdout.write(
            f"  Навыков: создано {created_count}, уже существовало {total - created_count}"
            + (f", пропущено {skipped}" if skipped else "")
        )

        # --- Зависимости ---
        self.stdout.write(f"Читаю зависимости из {deps_path} ...")
        graph = GraphService()
        dep_created = 0
        dep_skipped = 0

        with open(deps_path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                skill_name = row.get("skill", "").strip()
                depends_on = row.get("depends_on", "").strip()
                if not skill_name or not depends_on:
                    continue
                try:
                    graph.add_dependency(skill_name, depends_on)
                    dep_created += 1
                except Exception as e:
                    self.stderr.write(
                        f"  Пропущено ({skill_name} -> {depends_on}): {e}"
                    )
                    dep_skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово! Навыков: {total}, зависимостей добавлено: {dep_created}"
                + (f", пропущено: {dep_skipped}" if dep_skipped else "")
                + "."
            )
        )
