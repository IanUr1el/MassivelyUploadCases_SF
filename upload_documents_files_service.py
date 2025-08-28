from simple_salesforce import Salesforce
import requests
import pandas as pd
import os
from dotenv import load_dotenv
import numpy as np
import base64
import re

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
    ruta = 'C://Users//MCB-0164//Documents//Programas//SubirCancelaciones//Archivos//Documentos a Subir'
    folios_mapeados = getId_Folios(sf, folios)
    if folios_mapeados:
        print("Mapeo de folios a IDs:")
        print(folios_mapeados)
        archivos = [f for f in os.listdir(ruta) if os.path.isfile(os.path.join(ruta, f))]
        print(f"Archivos encontrados en la ruta: {archivos}")
        for filename in archivos:
            file_path = os.path.join(ruta, filename)
            expresion = re.search(r'(\d{8})', filename)
            if expresion: 
                 folio = expresion.group(1)
                 folio_id = folios_mapeados.get(folio)
                 if folio_id:
                     subir_pdfs(sf, file_path, folio_id)
                 else:
                     print(f"No se encontró ID para el folio {folio}. Archivo {filename} no subido.")
            else:
                print(f"No se encontró un folio válido en el nombre del archivo {filename}. Archivo no subido.")
    else:
        print("No se encontraron folios mapeados.")

else:
    print("Error al obtener el token:", resp.status_code)
    print(resp.text)