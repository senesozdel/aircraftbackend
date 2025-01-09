# Frontend Uygulamasına Gitmek için : https://github.com/senesozdel/aircraftui


1) git clone ile projeyi klonlayınız.
2) proje dizininde .env dosyasında gerekli bilgileri giriniz. ( db_name, username, password gibi) settings.py dosyasında nasıl kullanıldığını görebilirsiniz.
3)  !!!! entrypoint.sh dosyasının satır sonu CRLF olabilir LF yapınız. VSCode kullanıcıları için sağ alt tabtan değiştiriniz.
4) docker-compose build ile docker imajını oluşturunuz.
5) docker-compose up ile konteynırları çalıştırınız.
6) docker-compose exec web python manage.py makemigrations komutu ile ilk migrasyonunuzu oluşturunuz.
7) docker-compose exec web python manage.py migrate   komutu ile oluşturulan migrasyonu işleyiniz.
8)  docker-compose run web python manage.py loaddata initial_data ile fixtures dosyasının altındaki initial.data içerisindeki verileri db ye kaydediniz.
9)  5050 portundan pgadmin arayüzüne erişebilirsiniz
10)  8000/swagger portundan backend arayüzüne erişebilirsiniz

# Docker Services 
![dockerdesktop](https://github.com/user-attachments/assets/0a9b7616-673d-44f4-ade1-097964c8c898)
# Db Diagram
![db_diagram](https://github.com/user-attachments/assets/52b99672-aaac-4251-b3ec-aebd433266a7)
# Swagger UI
![swagger](https://github.com/user-attachments/assets/01ee144f-1900-48af-9a26-8898c5b95f57)
