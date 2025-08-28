from simple_salesforce import Salesforce
import requests
import pandas as pd
import os
from dotenv import load_dotenv
import numpy as np
import base64

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

    def subir_pdfs(sf_instance, file_path, record_id):
        try:
            with open(file_path, 'rb') as f:
                pdf_content = f.read()
                encoded_content = base64.b64encode(pdf_content).decode('utf-8')
            file_name = os.path.basename(file_path)
            content_version_payload = {
                'PathOnClient': file_name,
                'Title': file_name,
                'VersionData': encoded_content
            }

            print(f"Subiendo archivo: {file_name}...")
            cv_response = sf_instance.ContentVersion.create(content_version_payload)

            cv_id = cv_response['id']

            query_result = sf_instance.query(f"SELECT ContentDocumentId FROM ContentVersion WHERE Id = '{cv_id}'")
            content_document_id = query_result['records'][0]['ContentDocumentId']

            content_document_link_payload = {
                'ContentDocumentId': content_document_id,
                'LinkedEntityId': record_id,
                'ShareType': 'V'
            }

            sf_instance.ContentDocumentLink.create(content_document_link_payload)
            print(f"Archivo {file_name} vinculado al folio {record_id} con éxito.\n")

        except Exception as e:
            print(f"Error al procesar el archivo {file_path}: {e}")

    def getId_Folios(sf_instance, folios_list):
        try:
            folios_str = ", ".join(f"'{f}'" for f in folios_list)
            query = f"SELECT Id, CaseNumber FROM Case WHERE CaseNumber IN ({folios_str})"
            records = sf_instance.query_all(query)
            folio_id_map = {record['CaseNumber']: record['Id'] for record in records.get('records', [])}
            return folio_id_map
        except Exception as e:
            print("Error al exportar registros: {e}")
            return None    

    folios = {
        '00036536',
        '00036280',
        '00036136',
        '00036132',
        '00036116',
        '00035332'
    }

    '''
    folio = '500WR00000aG4j0YAC'
    #pdf_files = [
        'C://Users//MCB-0164//Documents//Programas//SubirCancelaciones//Plan_De_Trabajo_Conexion_SF_Canvas.pdf',
        'C://Users//MCB-0164//Documents//Programas//SubirCancelaciones//prueba2.pdf'
    ]
    '''
    ruta = 'C://Users//MCB-0164//Documents//Programas//SubirCancelaciones//Archivos'
    archivo1 = 'archivo1'
    archivo2 = 'archivo2'
    folios_mapeados = getId_Folios(sf, folios)
    if folios_mapeados:
        print("Mapeo de folios a IDs:")
        print(folios_mapeados)
        for folio in folios:
            folio_id = folios_mapeados.get(folio)

            if folio_id:
                ruta_carpeta = os.path.join(ruta, folio)

                if os.path.exists(ruta_carpeta):
                    print(f"Procesando archivos de la carpeta {folio}")

                    for filename in os.listdir(ruta_carpeta):
                        file_path = os.path.join(ruta_carpeta, filename)

                        if os.path.isfile(file_path):
                            subir_pdfs(sf, file_path, folio_id)
                else:
                    print(f"No se encontro la carpeta con el folio: {folio}")
            else:
                print(f"No hay Id del folio {folio} en SF")
    else:
        print("No se pudo obtener el mapeo de folios.")

        '''
    for file_path in pdf_files:
        if os.path.exists(file_path):
            subir_pdfs(sf, file_path, folio)
        else:
            print(f"Advertencia: El archivo no existe en la ruta {file_path}")'''

else:
    print("Error al obtener el token:", resp.status_code)
    print(resp.text)