#!/bin/sh

# Veritabanının hazır olmasını bekle
echo "Veritabanının hazır olması bekleniyor..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Veritabanı hazır!"

# Migrationları uygula
python manage.py migrate

# Fixture'ları yükle
python manage.py loaddata initial_data

# Django uygulamasını başlat
exec "$@"
