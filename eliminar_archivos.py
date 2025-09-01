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
    print("Conexión OAuth2 exitosa.")

    def eliminar_archivos(sf_instance, ids_delete):
        try:
            result = sf_instance.bulk.ContentDocument.delete(ids_delete)
            for record in result:
                if record['success']:
                    print(f"Archivo con ID {record['id']} eliminado exitosamente.")
                else:
                    print(f"Error al eliminar archivo con ID {record['id']}: {record['errors']}")

            print("Eliminación de archivos completada. Se eliminaron los siguientes IDs: ", len(ids_delete))
        except Exception as e:
            print(f"Error al eliminar archivos: {e}")

    ids_a_eliminar = pd.read_csv('C://Users//MCB-0164//Documents//Programas//SubirDocumentos//EliminarArchivos//extract.csv')
    ids_a_eliminar_list = [{'Id': str(id)} for id in ids_a_eliminar['ContentDocumentId'].dropna() if len(str(id)) in [15, 18]]

    print(ids_a_eliminar_list)
    eliminar_archivos(sf, ids_a_eliminar_list)
else:
    print("Error al obtener el token:", resp.status_code)
    print(resp.text)