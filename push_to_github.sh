#!/usr/bin/env bash
set -e
cd /home/kvezik/antigravity-bot-hub

echo "=== Проверка авторизации GitHub ==="
if ! gh auth status &>/dev/null; then
    echo "Требуется вход в GitHub CLI. Запускаем авторизацию..."
    gh auth login -h github.com -p https -w
fi

echo "=== Создание и отправка репозитория на GitHub ==="
if ! git remote | grep -q origin; then
    gh repo create antigravity-bot-hub --public --source=. --remote=origin --push
else
    git push -u origin main
fi

echo "✔ Репозиторий успешно опубликован на GitHub!"
echo "Ссылка: https://github.com/kvezik/antigravity-bot-hub"
