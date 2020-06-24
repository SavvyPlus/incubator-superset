#!/bin/bash

export SUPERSET_MYSQL=${SUPERSET_MYSQL}
celery worker --app=superset.tasks.celery_app:app -Ofair