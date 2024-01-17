# simcont
Simcont API

Backend part of Simcont project.
Simcont project is platform for learn English using approach when you learn only need vocabulary.  <br>
The platform provide upload your vocabulary, and understand witch lemmas in this vocabulary the most using. <br>

## Deploy for developer

1. Copy project from Git 
2. Install and activate environment
```commandline
python3 -m venv venv
source venv/bin/activate
```
3. Install  end fill .env file.
4. Install Postgres in docker
5. Start docker container using docker compose up
6. Make migrations.
7. Start project 
```commandline
python3 manage.py runserver
```
8.Start Celery 
```commandline
celery -A simcont worker -l INFO
```
