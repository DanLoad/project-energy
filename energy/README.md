# Сервер для мониторинга электроэнергии
## Настраиваем Django
Обновляем систему:


| $ | sudo apt update |
|---|:-------------|
| $ | sudo apt install -y python3-pip python3-dev python3-venv mc |

Клонируем репозиторий:

| $ | cd /home |
|---|:-------------|
| $ | sudo git clone https://github.com/DanLoad/project-energy.git |

Даем права:

| $ | sudo chown eng project-energy/ |
|---|:-------------|
| $ | sudo chown -R eng project-energy/ |
| $ | chown eng:eng -R project-energy/ |

Обновляем pip:

| $ | pip3 install --upgrade pip |
|---|:-------------|

Устанавливаем виртуальную среду и активируем:

| $ | cd /home/project-energy |
|---|:-------------|
| $ | python3 -m venv venv |
| $ | source venv/bin/activate |

Устанавливаем пакеты:

| $ | pip install --upgrade pip |
|---|:-------------|
| $ | pip install django djangorestframework redis django-celery-beat gunicorn |
| $ | pip install -U "celery[redis]" |

Проводим миграцию:

| $ | cd /home/project-energy/energy |
|---|:-------------|
| $ | python manage.py migrate --run-syncdb |

Запускаем сервер:

| $ | python manage.py runserver |
|---|:-------------|

## Запускаем Dunicorn через Supervisor

Запускаем сервер через Dunicorn

| $ | gunicorn --bind 0.0.0.0:8000 energy.wsgi:application |
|---|:-------------|

Устанавливаем Nginx и Supervisor:

| $ | sudo apt-get install nginx supervisor |
|---|:-------------|

Создаем файл конфигурации Dunicorn в Supervisor:

| $ | sudo nano /etc/supervisor/conf.d/gunicorn.conf |
|---|:-------------|

Вставить:
```python
[program:gunicorn]
directory = /home/project-energy/energy
command = /home/project-energy/venv/bin/gunicorn --workers 3 --bind unix:/home/project-energy/energy/app.sock energy.wsgi:application
autostart = true
autorestart = true
stderr_logfile = /var/log/gunicorn/error.log
stdout_logfile = /var/log/gunicorn/outs.log
[group:guni]
programs:gunicorn
```

Создаем лог файлы для Dunicorn:

| $ | sudo mkdir /var/log/gunicorn |
|---|:-------------|
| $ | sudo touch /var/log/gunicorn/outs.log |
| $ | sudo touch /var/log/gunicorn/error.log |

Обновляем и перезагружаем Supervisor:

| $ | sudo supervisorctl reread |
|---|:-------------|
| $ | sudo supervisorctl update |
| $ | sudo supervisorctl status |

Настройка Nginx:

Открываем файл:

| $ | sudo nano /etc/nginx/sites-available/default |
|---|:-------------|

Вставляем:
```python
server {
        listen 80 default_server;
        listen [::]:80 default_server;

        server_name 0.0.0.0 energy.local;

        location / {
                include proxy_params;
                proxy_pass http://unix:/home/project-energy/energy/app.sock;
        }

        location /static/ {
                autoindex on;
                alias /home/project-energy/energy/static/;
        }
}
```

Перезагружаем Nginx:

| $ | sudo systemctl reload nginx |
|---|:-------------|

## Веб интерфейс Supervisor

| $ | sudo nano /etc/supervisor/supervisord.conf |
|---|:-------------|

```python
[inet_http_server]
port=0.0.0.0:9001
username=admin  ;
password=123456  ;
```

| $ | sudo service supervisor restart |
|---|:-------------|

## Установка и настройка Redis server, Celery, Celery Beat

Установка Redis server:

| $ | sudo apt-get install redis-server |
|---|:-------------|

Создаем celery пользователя и группу:

| $ | sudo groupadd celery |
|---|:-------------|
| $ | sudo useradd -g celery celery |

Настройка Celery worker:

| $ | sudo nano /etc/supervisor/conf.d/celery_worker.conf |
|---|:-------------|

Вставить:
```python
; ==========================
;  celery worker supervisor
; ==========================

; the name of your supervisord program
[program:celery-worker]

; Set full path to celery program if using virtualenv
command=/home/project-energy/venv/bin/celery -A energy worker --loglevel=INFO

; The directory to your Django project
directory=/home/project-energy/energy

; If supervisord is run as the root user, switch users to this UNIX user account
; before doing any processing.
user=celery

; Supervisor will start as many instances of this program as named by numprocs
numprocs=1

; Put process stdout output in this file
stdout_logfile=/var/log/celery/celery_worker_out.log

; Put process stderr output in this file
stderr_logfile=/var/log/celery/celery_worker_err.log

; If true, this program will start automatically when supervisord is started
autostart=true

; May be one of false, unexpected, or true. If false, the process will never
; be autorestarted. If unexpected, the process will be restart when the program
; exits with an exit code that is not one of the exit codes associated with this
; process’ configuration (see exitcodes). If true, the process will be
; unconditionally restarted when it exits, without regard to its exit code.
autorestart=true

; The total number of seconds which the program needs to stay running after
; a startup to consider the start successful.
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; When resorting to send SIGKILL to the program to terminate it
; send SIGKILL to its whole process group instead,
; taking care of its children as well.
killasgroup=true

; if your broker is supervised, set its priority higher
; so it starts first
priority=998
```

Настройка Celery beat:

| $ | sudo nano /etc/supervisor/conf.d/celery_beat.conf |
|---|:-------------|

Вставить:
```python
; ========================
;  celery beat supervisor
; ========================

; the name of your supervisord program
[program:celery-beat]

; Set full path to celery program if using virtualenv
command=/home/project-energy/venv/bin/celerybeat -A energy --loglevel=INFO
command=/home/project-energy/venv/bin/celery -A energy beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
; The directory to your Django project
directory=/home/project-energy/energy

; If supervisord is run as the root user, switch users to this UNIX user account
; before doing any processing.
user=celery

; Supervisor will start as many instances of this program as named by numprocs
numprocs=1

; Put process stdout output in this file
stdout_logfile=/var/log/celery/celery_beat_out.log

; Put process stderr output in this file
stderr_logfile=/var/log/celery/celery_beat_err.log

; If true, this program will start automatically when supervisord is started
autostart=true

; May be one of false, unexpected, or true. If false, the process will never
; be autorestarted. If unexpected, the process will be restart when the program
; exits with an exit code that is not one of the exit codes associated with this
; process’ configuration (see exitcodes). If true, the process will be
; unconditionally restarted when it exits, without regard to its exit code.
autorestart=true

; The total number of seconds which the program needs to stay running after
; a startup to consider the start successful.
startsecs=10
stopwaitsecs = 60

; if your broker is supervised, set its priority higher
; so it starts first
priority=999
```
Перезагрузка сервисов:

| $ | sudo service nginx restart |
|---|:-------------|
| $ | sudo service supervisor restart |
