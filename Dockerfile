# start from an official image
FROM python:3.6

# arbitrary location choice: you can change the directory
RUN mkdir -p /usr/djangoapp/code

WORKDIR /usr/djangoapp/code

COPY requirements.txt /usr/djangoapp/code

# install our dependencies
RUN pip install -r requirements.txt

# copy our project code
COPY . /usr/djangoapp/code/

# expose the port 8000
EXPOSE 8000

# CMD cp -r dns_cache/static djangoapps/dns_cache/staticfiles && gunicorn --chdir dns_cache --bind :8000 dns_cache.wsgi:application

CMD gunicorn --chdir dns_cache --bind :8000 dns_cache.wsgi:application


