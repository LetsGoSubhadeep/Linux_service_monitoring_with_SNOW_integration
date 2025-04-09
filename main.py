#!/usr/bin/env python3

import time
import logging
import requests
import json
import os
from creds import *
import traceback
import subprocess

####################################################
# Doing the basic logging configuration and format #
####################################################

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

#############
# Variables #
#############

ServerName = subprocess.check_output(["hostname"], shell=True,text=True)
headers = {
        "Accept": "Application/json",
        "Content-Type": "Application/json"
        }
inc_number = "0"
number = "1"
list_of_inc = []
list_of_sys_ids = []
get_sys_id = []
service_name = "chronyd"
###################################
# Defining the required functions #
###################################

def create_inc_snow():
    global get_sys_id
    payload = {"caller_id":"snow_integration_api.incident","short_description":"The service is not running on server: "+ServerName,"description":"This is a test incident made through Python Script & API call,this is the description","cmdb_ci":"Host-3","impact": "1","urgency": "2" ,"priority":"2"}
    send_reqs = requests.post(url, auth=(snow_userID,snow_passwd ), headers=headers, data=json.dumps(payload,indent=4))
    response_data = send_reqs.json()
    get_inc_no = response_data["result"]["number"]
    get_sys_id = response_data["result"]["sys_id"]
    return get_inc_no, get_sys_id


def resolve_exist_inc():
    resolve_inc_url = f"https://{snow_instance}.service-now.com/api/now/table/incident/{get_sys_id}"
    service_status = get_systemctl_service_status_output(service_name)
    line_separator = "\n ******************************************** \n"
    payload = {"incident_state":"7","close_code":"Resolved by caller","close_notes":"The issue has resolved","work_notes":"The service has started running again on server: "+ServerName+  " "+line_separator +service_status}
    send_resolve_reqs = requests.patch(resolve_inc_url, auth=(snow_userID,snow_passwd ), headers=headers, data=json.dumps(payload,indent=4))
    resolve_inc_no = send_resolve_reqs.json()["result"]["number"]
    return resolve_inc_no


def get_inc_details():
    response = requests.get(url3, auth=(snow_userID, snow_passwd), headers=headers)
    incidents = response.json()["result"]
    for incident in incidents:
        each_inc = incident["number"]
        sys_ids = incident["sys_id"]
        list_of_inc.append(each_inc)
        list_of_sys_ids.append(sys_ids)
    finding = inc_number in list_of_inc
    return finding, list_of_sys_ids


def format_exc_for_journald(ex, indent_lines=False):
    """
        Journald removes leading whitespace from every line, making it very
        hard to read python traceback messages. This tricks journald into
        not removing leading whitespace by adding a dot at the beginning of
        every line
    """

    result = ''
    for line in ex.splitlines():
        if indent_lines:
            result += ".    " + line + "\n"
        else:
            result += "." + line + "\n"
    return result.rstrip()


def check_service_status(service_name):
    try:
        result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output = True,
                text = True,
                check = True

                )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip() or e.stderror.strip()


def get_systemctl_service_status_output(service_name):
    result = subprocess.run(
            ["systemctl", "status", service_name], 
            text = True, 
            capture_output = True
            )
    return result.stdout

#################
# The main Code #
#################

try:

    while True:                                                                                                     # Created infinite loop to continuously getting the data from the server

        service_status = check_service_status(service_name)
        if service_status == "active":
            logging.info("service is running...")
            finding, list_of_sys_ids = get_inc_details()

            if get_sys_id in list_of_sys_ids:                                                                       # for checking is there already any incident present or not, if yes then it will auto_resolve
                exist_inc = resolve_exist_inc()
                logging.info(f"As the service again started running, resolved the existing incident : {exist_inc}")
                list_of_sys_ids = []

        else:
            finding, list_of_sys_ids = get_inc_details()                                                            # collecting the incidents raised at or after last 30 days

            if finding == False:                                                                                    # if there is no inc raised for this, then it will raise an inc
                inc_number, sys_id = create_inc_snow()
                logging.warning(f"Service is not running, incident raised in snow ITSM {inc_number}")               # Generating a warning log when the services are not running
            else:
                logging.info(f"Incident already exist {inc_number} in {list_of_inc}")                               # if inc already raised, it will not raise again
        list_of_inc = []
        time.sleep(120)                                                                                             # It will wait for 2mins, then gain loop will execute.
except Exception:
        logger.error(format_exc_for_journald(traceback.format_exc(), indent_lines=False))
