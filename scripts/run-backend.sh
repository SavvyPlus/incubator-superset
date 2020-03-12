sudo systemctl enable redis-server.service

cd ~/incubator-superset
. ~/incubator-superset/venv/bin/activate
export SMTP_USERNAME=$1
export SMTP_PASSWORD=$2
export STRIPE_SK=$3
export STRIPE_PK=$4

celery worker --app=superset.sql_lab:celery_app --pool=gevent -Ofair & gunicorn --bind  0.0.0.0:8088 --workers $((2 * $(getconf _NPROCESSORS_ONLN) + 1))  --timeout 60 --limit-request-line 0 --limit-request-field_size 0 superset:app --log-level info --log-file logs.txt --capture-output