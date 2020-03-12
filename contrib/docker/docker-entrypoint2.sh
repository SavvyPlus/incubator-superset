#!/bin/bash
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
set -ex


export SMTP_USERNAME=$1
export SMTP_PASSWORD=$2
export STRIPE_SK=$3
export STRIPE_PK=$4

export MYSQL_USER=$5
export MYSQL_PASSWORD=$6
export MYSQL_HOST=$7
export MYSQL_PORT=$8
export MYSQL_DB=$9
export SG_API_KEY=${10}
export VERSION=${11}
export FREE_CREDIT_DOLLAR=${12}
export GENERATION_API=${13}
export REDIS_URL=${14}

celery worker --app=superset.sql_lab:celery_app --pool=gevent -Ofair &
gunicorn --bind  0.0.0.0:8088 \
    --workers $((2 * $(getconf _NPROCESSORS_ONLN) + 1)) \
    --timeout 60 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    superset:app

