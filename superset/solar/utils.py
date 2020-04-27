# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
# pylint: disable=C,R,W
import os
import json
import re

from flask import session, redirect
from mixpanel import Mixpanel
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
import logging as log

mp = Mixpanel('8b85dcbb1c5f693a3b045b24fca1e787')
mp_prefix = os.getenv('SUPERSET_ENV')

free_credit_in_dollar = os.getenv('FREE_CREDIT_DOLLAR')
sendgrid_email_sender = ('no-reply@solarbi.com.au', 'SolarBI')


def post_request(url, params):
    import requests
    return requests.post(url, data=json.dumps(params))


def set_session_team(id, name):
    session['team_id'] = id
    session['team_name'] = name


def get_session_team(securitymanager, user_id):
    try:
        return session['team_id'], session['team_name']
    except Exception as e:
        team = securitymanager.find_team(user_id=user_id)
        if team:
            set_session_team(team.id, team.team_name)
            return team.id, team.team_name
        else:
            # No team found, return None
            # Need more handling on this
            return None


def log_to_mp(user, team_name, action, metadata):
    metadata['Team'] = team_name
    metadata['Source'] = mp_prefix
    if user:
        mp.track(user.username, action, metadata)
    else:
        mp.track('', action, metadata)


def create_mp_team(team):
    mp.group_set('Team', team.team_name, {
        '$name': team.team_name
    })


def update_mp_user(user):
    mp.people_set(user.username, {
        '$first_name': user.first_name,
        '$last_name': user.last_name,
        '$email': user.email
    })


def update_mp_team(team, metadata):
    mp.group_set('Team', team.team_name, metadata)


def mp_add_user_to_team(user, team):
    mp.people_append(user.username, {
        'Team': team.team_name
    })


def get_athena_query(lat, lng, start_date, end_date, data_type, resolution):
    start_year, start_month, start_day = start_date.split('-')
    end_year, end_month, end_day = end_date.split('-')
    select_str = ""
    group_str = ""
    order_str = ""
    if data_type != 'both':
        if resolution == 'hourly':
            select_str = "SELECT year, month, day, hour, radiationtype, radiation"
            group_str = "GROUP BY year, month, day, hour, radiationtype, radiation"
            order_str = "ORDER BY year ASC, month ASC, day ASC, hour ASC"
        elif resolution == 'daily':
            select_str = \
                "SELECT year, month, day, radiationtype, avg(radiation) AS radiation"
            group_str = "GROUP BY year, month, day, radiationtype"
            order_str = "ORDER BY year ASC, month ASC, day ASC"
        elif resolution == 'weekly':
            select_str = \
                "SELECT CAST(date_trunc('week', r_date) AS date) AS Monday_of_week, " + \
                "radiationtype, avg(radiation) AS week_avg_radiation FROM " + \
                "(SELECT cast(date AS timestamp) AS r_date, year, month, day, " + \
                "radiationtype, radiation"
            group_str = "GROUP BY  date, year, month, day, radiationtype, radiation"
            order_str = "ORDER BY  date) GROUP BY date_trunc('week', r_date), " + \
                        "radiationtype ORDER BY 1"
        elif resolution == 'monthly':
            select_str = "SELECT year, month, radiationtype, avg(radiation) AS radiation"
            group_str = "GROUP BY year, month, radiationtype"
            order_str = "ORDER BY year ASC, month ASC"
        elif resolution == 'annual':
            select_str = "SELECT year, radiationtype, avg(radiation) AS radiation"
            group_str = "GROUP BY year, radiationtype"
            order_str = "ORDER BY year ASC"
    else:
        if resolution == 'hourly':
            select_str = "SELECT DNI.year, DNI.month, DNI.day, DNI.hour, avg(DNI.radiation) AS dni_radiation, " \
                         "avg(GHI.radiation) AS ghi_radiation"
            group_str = "GROUP BY DNI.year, DNI.month, DNI.day, DNI.hour"
            order_str = "ORDER BY  DNI.year ASC, DNI.month ASC, DNI.day ASC, DNI.hour ASC"
        elif resolution == 'daily':
            select_str = "SELECT DNI.year, DNI.month, DNI.day, avg(DNI.radiation) AS dni_radiation, " \
                         "avg(GHI.radiation) AS ghi_radiation"
            group_str = "GROUP BY DNI.year, DNI.month, DNI.day"
            order_str = "ORDER BY  DNI.year ASC, DNI.month ASC, DNI.day ASC"
        elif resolution == 'weekly':
            select_str = \
                "SELECT CAST(date_trunc('week', r_date) AS date) AS Monday_of_week, " + \
                "avg(dni_radiation) AS week_avg_dni, avg(ghi_radiation) AS week_avg_ghi FROM " + \
                "(SELECT cast(DNI.date AS timestamp) AS r_date, DNI.year, DNI.month, DNI.day, " + \
                "avg(DNI.radiation) AS dni_radiation, avg(GHI.radiation) AS ghi_radiation"
            group_str = "GROUP BY  DNI.date, DNI.year, DNI.month, DNI.day ORDER BY  DNI.date) GROUP BY " \
                        "date_trunc('week', r_date) "
            order_str = "ORDER BY  1"
        elif resolution == 'monthly':
            select_str = "SELECT DNI.year, DNI.month, avg(DNI.radiation) AS dni_radiation, " \
                         "avg(GHI.radiation) AS ghi_radiation"
            group_str = "GROUP BY DNI.year, DNI.month"
            order_str = "ORDER BY  DNI.year ASC, DNI.month ASC"
        elif resolution == 'annual':
            select_str = "SELECT DNI.year, avg(DNI.radiation) AS dni_radiation, avg(GHI.radiation) AS ghi_radiation"
            group_str = "GROUP BY DNI.year"
            order_str = "ORDER BY DNI.year ASC"

    if data_type != 'both':
        athena_query = select_str \
                       + " FROM \"solar_radiation_hill\".\"lat_partition_v2\"" \
                       + " WHERE (CAST(year AS BIGINT)*10000" \
                       + " + CAST(month AS BIGINT)*100 + day)" \
                       + " BETWEEN " + start_year + start_month + start_day \
                       + " AND " + end_year + end_month + end_day \
                       + " AND latitude = '" + lat + "' AND longitude = '" + lng \
                       + "' AND radiationtype = '" + data_type + "' AND radiation != -999 " \
                       + group_str + " " + order_str
    else:
        athena_query = select_str \
                       + " FROM \"solar_radiation_hill\".\"lat_partition_v2\" AS GHI" \
                       + " INNER JOIN \"solar_radiation_hill\".\"lat_partition_v2\" AS DNI" \
                       + " ON (CAST(DNI.year AS BIGINT)*10000 + CAST(DNI.month AS BIGINT)*100 + DNI.day)" \
                       + " BETWEEN " + start_year + start_month + start_day + " AND " + end_year + end_month + end_day \
                       + " AND (CAST(GHI.year AS BIGINT)*10000 + CAST(GHI.month AS BIGINT)*100 + GHI.day) " \
                       + " BETWEEN " + start_year + start_month + start_day + " AND " + end_year + end_month + end_day \
                       + " AND DNI.latitude = '" + lat + "' AND DNI.longitude = '" + lng + "' AND GHI.latitude = '" \
                       + lat + "' AND GHI.longitude = '" + lng + "' AND DNI.radiation != -999 " \
                       + " AND GHI.radiation != -999" + " AND GHI.year = DNI.year AND GHI.month = DNI.month" \
                       + " AND GHI.day = DNI.day AND GHI.hour = DNI.hour" \
                       + " WHERE DNI.radiationtype = 'dni' AND GHI.radiationtype = 'ghi' " \
                       + group_str + " " + order_str

    return athena_query


def send_sendgrid_email(user, message_data, template_id):
    message = Mail(
        from_email=sendgrid_email_sender,
        to_emails=user.email,
    )
    message.dynamic_template_data = message_data
    message.template_id = template_id
    try:
        sendgrid_client = SendGridAPIClient(os.environ['SG_API_KEY'])
        _ = sendgrid_client.send(message)
        return True
    except Exception as e:
        log.error('Send email exception: {0}'.format(str(e)))
        return False
