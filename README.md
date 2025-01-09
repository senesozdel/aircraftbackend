# Frontend Uygulamasına Gitmek için : https://github.com/senesozdel/aircraftui


1) git clone ile projeyi klonlayınız.
2) proje dizininde .env dosyasında gerekli bilgileri giriniz. ( db_name, username, password gibi) settings.py dosyasında nasıl kullanıldığını görebilirsiniz.
3) docker-compose build ile docker imajını oluşturunuz.
4) docker-compose up ile konteynırları çalıştırınız.
5) docker-compose exec web python manage.py makemigrations komutu ile ilk migrasyonunuzu oluşturunuz.
6) docker-compose exec web python manage.py migrate   komutu ile oluşturulan migrasyonu işleyiniz.
7)  docker-compose run web python manage.py loaddata initial_data ile fixtures dosyasının altındaki initial.data içerisindeki verileri db ye kaydediniz.
8)  5050 portundan pgadmin arayüzüne erişebilirsiniz
9)  8000/swagger portundan backend arayüzüne erişebilirsiniz

# Docker Services 
![dockerdesktop](https://github.com/user-attachments/assets/0a9b7616-673d-44f4-ade1-097964c8c898)
# Db Diagram
![db_diagram](https://github.com/user-attachments/assets/52b99672-aaac-4251-b3ec-aebd433266a7)
# Swagger UI
![swagger](https://github.com/user-attachments/assets/01ee144f-1900-48af-9a26-8898c5b95f57)
