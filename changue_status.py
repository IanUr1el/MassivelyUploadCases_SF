from simple_salesforce import Salesforce
import requests
import pandas as pd
import os
from dotenv import load_dotenv
import numpy as np
import base64
import re
import csv
from datetime import datetime

load_dotenv()
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
url = os.getenv('url')
data = {
'grant_type': 'client_credentials',
'client_id': CONSUMER_KEY,
'client_secret': CONSUMER_SECRET
}
resp = requests.post(url, data=data)
if resp.status_code == 200:
    auth_response = resp.json()
    access_token = auth_response['access_token']
    instance_url = auth_response['instance_url']
    print("Access Token:", access_token)
    print("Instance URL:", instance_url)

    sf = Salesforce(instance_url=instance_url, session_id=access_token)
    #print("Conexión OAuth2 exitosa.")
    ##sf.Case.get('00026090')['Status']
    #print("Status del caso 00036571:", sf.Case.get('500ct00000EyYtBAAV')['Status'])
    #print("Status del caso 00036568:", sf.Case.get('500ct00000EyBN7AAN')['Status'])
    #sf.Case.update('500ct00000EyBN7AAN', {'Status': 'NoDeberiaCambiar'})
    #print("Se actualizo: Status del caso 00036568:", sf.Case.get('500ct00000EyBN7AAN')['Status'])
    #sf.Case.update('500WR00000aULQYYA4', {'Status': 'Terminado'})
    #print("Se actualizo: Status del caso 00036536:", sf.Case.get('500WR00000aULQYYA4')['Status'])
    #sf.Case.update('00026090', {'Status': 'Cerrado'}) 
    print("Status del caso 00036136:", sf.Case.get('500WR00000aG4j0YAC')['Status'])
    sf.Case.update('500ct00000EyBN7AAN', {'Status': 'Asignado áreas internas'})
    sf.Case.update('500WR00000aULQYYA4', {'Status': 'Asignado'})
    sf.Case.update('500WR00000aG4j0YAC', {'Status': 'Creado'})
    sf.Case.update('500WR00000WJs90YAD', {'Status': 'Creado'})
    sf.Case.update('500WR00000WJg9RYAT', {'Status': 'Creado'})
    sf.Case.update('500WR00000WJnB0YAL', {'Status': 'Creado'})

    #print("Se actualizo: Status del caso 00036136:", sf.Case.get('500WR00000aG4j0YAC')['Status'])

else:
    print("Error al obtener el token:", resp.status_code)
    print(resp.text)