import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создание суперпользователя из переменных окружения (для CI/деплоя без интерактивного ввода)"

    def handle(self, *args, **options):
        """
        Получает имя пользователя, email и пароль из переменных окружения
        (SUPERUSER_USERNAME, SUPERUSER_EMAIL, SUPERUSER_PASSWORD).
        Если переменные не заданы или пользователь с таким именем уже существует,
        выводит соответствующее сообщение и ничего не создаёт.
        """
        User = get_user_model()
        username = os.getenv("SUPERUSER_USERNAME")
        email = os.getenv("SUPERUSER_EMAIL")
        password = os.getenv("SUPERUSER_PASSWORD")

        if not username or not email or not password:
            self.stdout.write(
                self.style.ERROR(
                    "Не все переменные окружения заданы (SUPERUSER_USERNAME, SUPERUSER_EMAIL, SUPERUSER_PASSWORD)."
                )
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"Пользователь с именем {username} уже существует.")
            )
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Суперпользователь {username} успешно создан.")
            )
