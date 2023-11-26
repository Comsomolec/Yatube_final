# YaTube
## Описание
Социальная сеть блогеров. Учебный проект.

Сообщество для публикаций. Блог с возможностью публикации постов, подпиской на группы и авторов, а также комментированием постов.

## Стек
- Python
- django
- pillow
- pytest
- requests

## Запуск проекта в dev-режиме
Инструкция ориентирована на операционную систему windows и утилиту git bash.
Для прочих инструментов используйте аналоги команд для вашего окружения.

* Клонируйте репозиторий и перейдите в него в командной строке:
```
git clone <HTTPS or SSH>
```
```
cd Yatube
```
* Установите и активируйте виртуальное окружение
```
python -m venv venv
```
```
source venv/Scripts/activate
```
* Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
```
* В папке с файлом manage.py выполните миграции:
```
python manage.py migrate
```
* В папке с файлом manage.py запустите сервер, выполнив команду:
```
python manage.py runserver
```
## Краткое описание функциональности:
Залогиненные пользователи могут:
Просматривать, публиковать, удалять и редактировать свои публикации;
Просматривать информацию о сообществах;
Просматривать и публиковать комментарии от своего имени к публикациям других пользователей (включая самого себя), удалять и редактировать свои комментарии;
Подписываться на других пользователей и просматривать свои подписки.
Примечание: Доступ ко всем операциям записи, обновления и удаления доступны только после аутентификации и получения токена.

Анонимные пользователи могут:
Просматривать публикации;
Просматривать информацию о сообществах;
Просматривать комментарии;

Набор доступных эндпоинтов :
posts/ - Отображение постов и публикаций (GET, POST);
posts/{id} - Получение, изменение, удаление поста с соответствующим id (GET, PUT, PATCH, DELETE);
posts/{post_id}/comments/ - Получение комментариев к посту с соответствующим post_id и публикация новых комментариев(GET, POST);
posts/{post_id}/comments/{id} - Получение, изменение, удаление комментария с соответствующим id к посту с соответствующим post_id (GET, PUT, PATCH, DELETE);
posts/groups/ - Получение описания зарегестрированных сообществ (GET);
posts/groups/{id}/ - Получение описания сообщества с соответствующим id (GET);
posts/follow/ - Получение информации о подписках текущего пользователя, создание новой подписки на пользователя (GET, POST).
