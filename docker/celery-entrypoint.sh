#!/bin/bash

celery worker --app=superset.tasks.celery_app:app -Ofair