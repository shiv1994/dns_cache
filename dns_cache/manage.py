#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    env_type = os.environ.get('env', "local")
    if env_type == "local":
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dns_cache.settings_dev')
    elif env_type == "production":
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dns_cache.settings_prod')
    else:
        print("Invalid configuration ...")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
