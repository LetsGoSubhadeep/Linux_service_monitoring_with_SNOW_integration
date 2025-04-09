import os

snow_instance = "dev277826"
hostname = os.getenv('HOSTNAME')
username = 'root'
url = f"https://{snow_instance}.service-now.com/api/now/table/incident"
url3 = f"https://{snow_instance}.service-now.com/api/now/table/incident?sysparm_query=incident_stateIN1,2,3^sys_created_on>=javascript:gs.beginningOfLast30Days()&sysparm_fields=sys_id%2Cnumber%2Cincident_state%2Csys_created_on"
snow_userID = "Python_integration"
snow_passwd = "password"

