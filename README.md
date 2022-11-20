# aimharder-telegram-bot
docker build -t <repository>/<image_name>:<version> .

docker run --name aimharder-telegram-bot -p 5000:5000 --env-file .env <repository>/<image_name>:<version>