# dns_cache
Django project which keeps a cache of entered domain names and their associated DNS Records.

Note the following when developing locally:
- Ensure that your connection does not block DNS queries otherwise your queries will hang.
- Run the docker-compose file commenting out the django container and network.
- Run python3 manage.py qcluster and qmonitor.
- Run the django application.