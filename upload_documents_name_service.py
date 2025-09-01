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

            return cv_id, content_document_id, file_name

        except Exception as e:
            print(f"Error al procesar el archivo {file_path}: {e}")
            return None, None, None

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

    def change_case_status(sf_instance, case_id, new_status):
        try:
            sf_instance.Case.update(case_id, {'Status': new_status})
            print(f"Estado del caso {case_id} actualizado a {new_status}.")
        except Exception as e:
            print(f"Error al actualizar el estado del caso {case_id}: {e}")    

    df_folios = pd.read_csv('C://Users//MCB-0164//Documents//Programas//SubirCancelaciones//Archivos//Folios_por_Subir_Prueba.csv', dtype={'CaseNumber': str})
    print(df_folios.dtypes)
    print(df_folios)

    folios = set(df_folios['CaseNumber'].dropna().astype(str))

    print(f"Folios a buscar: {folios}")
    ruta = 'C://Users//MCB-0164//Documents//Programas//SubirCancelaciones//Archivos//Documentos a Subir'
    nombres_archivos = {
        'NombreGenerico': 'NombreGenerico_',
        'OtroNombreGenerico': 'OtroNombreGenerico_',
        'Archivo1': 'Archivo1_'
        #'Archivo2': 'Archivo2_',
        #'CARTA DE ANTIGUEDAD': 'CARTA DE ANTIGUEDAD_'
    }
    archivos_count = len(nombres_archivos)
    print(f"Número de tipos de archivos a buscar por folio: {archivos_count}")
    folios_mapeados = getId_Folios(sf, folios)

    report_rows = []
    not_uploaded_rows = []
    case_status_map = {}

    for folio, folio_id in folios_mapeados.items():
        try:
            case_info = sf.Case.get(folio_id)
            case_status_map[folio] = case_info.get('Status', '')
        except Exception as e:
            case_status_map[folio] = ''
            print(f"Error al obtener el status inicial del caso {folio_id}: {e}")

    if folios_mapeados:
        print("Mapeo de folios a IDs:")
        print(folios_mapeados)
        for folio in folios:
            folio_id = folios_mapeados.get(folio)
            first_status = case_status_map.get(folio, '')

            if folio_id:
                print(f"Buscando: {folio}")

                for archivo_key, archivo_prefix in nombres_archivos.items():
                    ruta_carpeta = os.path.join(ruta, f"{archivo_prefix}{folio}.pdf")
                    file_path = os.path.join(ruta, ruta_carpeta)

                    if os.path.exists(file_path):
                        print(f"Procesando archivo: {file_path}")
                        cv_id, content_document_id, file_name = subir_pdfs(sf, file_path, folio_id)
                        if cv_id and content_document_id:
                            report_rows.append({
                                'Folio': folio,
                                'Clave_de_Archivo': archivo_key,
                                'FolioId': folio_id,
                                'ContentDocumentId': content_document_id,
                                'DocumentTitle':file_name,
                                'FechaCarga': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'StatusInicial': first_status,
                                'UpdatedStatus': ''
                            })
                    else:
                        print(f"No se encontro el archivo: {file_path}")
                        not_uploaded_rows.append({
                            'Folio': folio,
                            'Archivo No Cargado': archivo_key,
                            'FolioId': folio_id,
                            'ContentDocumentId': 'No subido',
                            'DocumentTitle': 'No subido',
                            'StatusInicial': first_status
                        })
            else:
                print(f"No hay Id del folio {folio} en SF")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f'Reporte_Folios_Documentos_{timestamp}.csv'
        with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['FolioId', 'Folio', 'Clave_de_Archivo', 'ContentDocumentId', 'DocumentTitle', 'FechaCarga', 'StatusInicial', 'UpdatedStatus']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in report_rows:
                writer.writerow(row)
        print(f"Reporte guardado en {report_path}")

        not_uploaded_path = f'Reporte_Folios_No_Cargados_{timestamp}.csv'
        with open(not_uploaded_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Folio', 'Archivo No Cargado', 'FolioId', 'ContentDocumentId', 'DocumentTitle', 'StatusInicial']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in not_uploaded_rows:
                writer.writerow(row)
        print(f"Reporte de archivos no cargados guardado en {not_uploaded_path}")
        df_report = pd.DataFrame(report_rows)
        print(df_report)
        folio_counts = df_report['Folio'].value_counts()
        print(folio_counts)

        for folio, count in folio_counts.items():
            if count == archivos_count:
                folio_id = df_report[df_report['Folio'] == folio]['FolioId'].iloc[0]
                try:
                    sf.Case.update(folio_id, {'Status': 'Terminado'})
                    df_report.loc[df_report['Folio'] == folio, 'UpdatedStatus'] = 'Terminado'
                    df_report.loc[df_report['Folio'] == folio, 'FechaActualizacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"El estado del caso {folio} ha sido actualizado a 'Terminado'.")
                except Exception as e:
                    df_report.loc[df_report['Folio'] == folio, 'UpdatedStatus'] = f'Error: {e}'
                    df_report.loc[df_report['Folio'] == folio, 'FechaActualizacion'] = 'No actualizado'
                    print(f"Error al actualizar el estado del caso {folio}: {e}")
            else:
                df_report.loc[df_report['Folio'] == folio, 'UpdatedStatus'] = f'No actualizado - Archivos faltantes: {archivos_count}-{count}'
                df_report.loc[df_report['Folio'] == folio, 'FechaActualizacion'] = 'No actualizado'
                print(f"El folio {folio} no tiene todos los archivos requeridos. Archivos encontrados: {count}, Archivos requeridos: {archivos_count}. No se actualizó el estado.")
        
        df_report = df_report.drop_duplicates(subset='Folio', keep='first')
        df_report = df_report.drop(columns=['Clave_de_Archivo', 'ContentDocumentId', 'DocumentTitle'])
        print(df_report)
        updated_report_path = f'Reporte_Folios_Status_Actualizado_{timestamp}.csv'
        df_report.to_csv(updated_report_path, index=False, encoding='utf-8')
        print(f"Reporte actualizado guardado en {updated_report_path}")

    else:
        print("No se pudo obtener el mapeo de folios.")

else:
    print("Error al obtener el token:", resp.status_code)
    print(resp.text)