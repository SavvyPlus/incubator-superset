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
import requests

from flask import session, redirect
from mixpanel import Mixpanel
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
import logging as log

mp = Mixpanel('8b85dcbb1c5f693a3b045b24fca1e787')
mp_prefix = os.getenv('SUPERSET_ENV')

free_credit_in_dollar = os.getenv('FREE_CREDIT_DOLLAR')
sg = SendGridAPIClient(os.environ['SG_API_KEY'])
sg_headers = {'authorization': 'Bearer ' + os.environ['SG_API_KEY']}
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


def is_in_sg(email):
    # First check the 50 most recent changed contacts
    response1 = sg.client.marketing.lists._('823624d1-c51e-4193-8542-3904b7586c29?contact_sample=true').get()
    contact_sample = json.loads(response1.body.decode('utf-8'))['contact_sample']
    for contact in contact_sample:
        if email == contact['email']:
            return contact['id']

    # If we do not find any record, we then use query to search the whole sg db
    response = sg.client.marketing.contacts.search.post(request_body={
        "query": "email LIKE '" + g.user.email + "' AND CONTAINS(list_ids, '823624d1-c51e-4193-8542-3904b7586c29')"
    })
    res = json.loads(response.body.decode("utf-8"))
    if not res['result']:
        return -1
    else:
        return res['result'][0]['id']


def update_sg_info(email_changed=False, names_changed=False, old_email=None, new_user=None):
    if email_changed:
        # If the user has been in SG already, delete it from contacts and marketing
        # suppression group
        contact_id = is_in_sg(old_email)
        if contact_id != -1:
            delete_contact(contact_id)
            delete_user_from_marketing_suppression(old_email)

        add_or_update_contact(new_user.email, new_user.first_name, new_user.last_name)
    else:
        if names_changed:
            contact_id = is_in_sg(new_user.email)
            if contact_id != -1:
                add_or_update_contact(new_user.email, new_user.first_name, new_user.last_name)

            # user_in_marketing_suppression = user_in_marketing_suppression(form.email.data)
            # subscription_status = (user_in_sg and not user_in_marketing_suppression)
            # if form.subscription.data != subscription_status:
            #     if form.subscription.data:
            #         if user_in_marketing_suppression(form.email.data):
            #             delete_user_from_marketing_suppression(form.email.data)
            #         else:
            #             add_or_update_contact(form.email.data, form.first_name.data, form.last_name.data)
            #     else:
            #         add_user_to_marketing_suppression(form.email.data)


def add_or_update_contact(email, first_name, last_name):
    _ = sg.client.marketing.contacts.put(request_body={
        "list_ids": [
            "823624d1-c51e-4193-8542-3904b7586c29"
        ],
        "contacts": [
            {
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            }
        ]
    })


def add_user_to_marketing_suppression(email):
    url = "https://api.sendgrid.com/v3/asm/groups/14067/suppressions"
    payload = "{\"recipient_emails\":[\"" + email + "\"]}"
    _ = requests.request("POST", url, data=payload, headers=sg_headers)


def delete_user_from_marketing_suppression(email):
    url = "https://api.sendgrid.com/v3/asm/groups/14067/suppressions/" + email
    _ = requests.request("DELETE", url, headers=sg_headers)


def user_in_marketing_suppression(email):
    url = "https://api.sendgrid.com/v3/asm/groups/14067/suppressions/search"
    payload = '{"recipient_emails":["' + email + '"]}'
    response = requests.request("POST", url, data=payload, headers=sg_headers)
    if json.loads(response.text):
        return True
    else:
        return False


def delete_contact(contact_id):
    sg.client.marketing.contacts.delete(query_params={"ids": contact_id})


def user_in_gs(email):
    url = "https://api.sendgrid.com/v3/asm/suppressions/global/" + email
    response = requests.request("GET", url, headers=sg_headers)
    if json.loads(response.text):
        return True
    else:
        return False


def add_to_gs(email):
    url = "https://api.sendgrid.com/v3/asm/suppressions/global"
    payload = "{\"recipient_emails\":[\"" + email + "\"]}"
    _ = requests.request("POST", url, data=payload, headers=self.headers)


def delete_gs(email):
    url = "https://api.sendgrid.com/v3/asm/suppressions/global/" + email
    _ = requests.request("DELETE", url, headers=self.headers)
