#!/bin/bash

echo "🚀 Установка зависимостей..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

echo "📦 Клонирование проекта..."
git clone https://github.com/teasec4/telegram-china-bot-.git china-goods-bot
cd china-goods-bot

echo "🎯 Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Установка python-зависимостей..."
pip install -r requirements.txt

echo "🛠 Настройка переменных окружения..."
cat <<EOF > .env
BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_admin_chat_id
EOF

echo "🔧 Создание systemd сервиса..."
sudo tee /etc/systemd/system/china-goods-bot.service > /dev/null <<EOF
[Unit]
Description=China Goods Telegram Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Перезапуск systemd и запуск бота..."
sudo systemctl daemon-reload
sudo systemctl enable china-goods-bot.service
sudo systemctl start china-goods-bot.service

echo "✅ Готово! Статус бота:"
sudo systemctl status china-goods-bot.service