Приложение для скачивания страничек сайтов

| Действие | Метод | URL | Описание |
|----------|-------|-----|----------|
| Create | POST | /api/v1.0/ | Добавить сайт для загрузки .etc url=https://wwww.example.com|
| Read | GET | /api/v1.0/*<string:id>* | Показать статус загруженно/незагруженно получить ссылку на закачку zip сайта |
| Read | GET | /api/v1.0/download/*<string:id>* | Скачать файл zip с именем id |

Запуск сервера.
```sh
$ export FLASK_APP=site_app
$ flask run
```
