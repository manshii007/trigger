## Trigger Backend With Docker Compose and Machine

Featuring:

- Docker v1.12.2
- Docker Compose v1.7.2 
- Docker Machine 
- Python 3.5
- Django
- Django Rest Framework
- FFMPEG
- nginx
- Postgresql
- Redis
- Rabbitmq
- And some other Awesome Programs

## Resources

Starting Blog post -> https://realpython.com/blog/python/django-development-with-docker-compose-and-machine/

### OS X / Windows Instructions

1. Start new machine - `docker-machine create -d virtualbox dev;`
1. Initialize the env varibles to use the new docker-machine - `eval $(docker-machine env dev)`
1. Build images with specific dockerfile - `docker-compose -f <compose file> build`
1. Start services in detach mode - `docker-compose -f <compose file> up -d`
1. Enter bash in web service - `docker-compose -f <compose file> run --rm web bash`
1. Create migrations - `python manage.py makemigrations`
1. Apply migrations - `python manage.py migrate`
1. Exit the bash - `exit`
1. Grab IP - `docker-machine ip dev` - and view in your browser

## Deployment Steps

```console
git clone https://github.com/tessact/trigger-docker
cd trigger-docker
cd web/
git clone https://github.com/tessact/tools
cd ~/trigger-docker/ && git pull origin {branch}
sudo docker-compose -f {compose.yml} build
sudo docker-compose -f {compose.yml} up -d
sudo docker exec -it web_ffmped-id python3 manage.py migrate
sudo docker exec -it web_ffmped-id python3 manage.py createsuperuser
```

## Bashrc alias
```sh
alias shell='cd ~/trigger-docker/ && sudo docker-compose -f {compose.yml} run --rm web_ffmpeg python3 manage.py shell'
alias migrate='cd ~/trigger-docker/ && sudo docker-compose -f {compose.yml} run --rm web_ffmpeg python3 manage.py migrate'
alias logs='cd ~/trigger-docker/ && sudo docker-compose -f {compose.yml} logs --tail=20 web_ffmpeg'
alias flogs='cd ~/trigger-docker/ && sudo docker-compose -f {compose.yml} logs --tail 100 -f web_ffmpeg'
alias down='cd ~/trigger-docker/ && sudo docker-compose -f {compose.yml} down'
alias reload='cd ~/trigger-docker/ && git pull origin {branch} &&
sudo docker-compose -f {compose.yml} build && sudo docker-compose -f {compose.yml} up -d --scale web_ffmpeg=3 && sudo  ./docker-clean.sh'
alias trigger-down='cd ~/trigger-docker/ && docker-compose -f {compose.yml} down'
```
