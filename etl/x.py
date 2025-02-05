from PyPDF2 import PdfReader
import os, re, io
import pandas as pd
import boto3
from botocore.client import Config
import requests
from requests_ntlm import HttpNtlmAuth
import json
import base64
import uuid
import gs_auth
from requests_gssapi import HTTPSPNEGOAuth
from datetime import datetime
import calendar
import time

# Function to convert time format
def convert_to_long_type(t, time_format):
    '''
    For lastUpdated_d, the format is long type.
    Example of time_format = '%Y-%m-%d' OR '%Y-%m-%dT%H:%M:%S'
    '''
    date_l = calendar.timegm(time.strptime(t, time_format))
    return date_l

# In case, we want to have nativeId = DRO_{docName}_todayTimestamp
today = datetime.now().strftime(format='%Y-%m-%dT%H:%M:%S')
today_l = convert_to_long_type(t=today, time_format='%Y-%m-%dT%H:%M:%S')

metadata_fields = [
    {
        'title': 'FIRMWIDE STANDARD Global Cloud Governance',
        'sourceName_s': 'TR-Advisory',
        'sourceDomain_s': 'Internal',
        'sourceOriginDivision_s': 'Technology Risk',
        'fileFormat_s': 'pdf',
        'category_s': 'Standard',
        'lastUpdated_d': convert_to_long_type(t='2021-08-10', time_format='%Y-%m-%d'),
        'keywords_s': ['standard', 'global', 'cloud', 'governance', 'cloud infrastructure', 'IaaS', 'PaaS', 'SaaS'],
        'securityFramework_s': [],
        'securityControl_s': [],
        'reviewCadence_s': '',
        'useCase_s': 'Q&A'
    },
    {
        'title': 'Firmwide Policy on Privacy: Protection of Personal Data',
        'sourceName_s': 'TR-Advisory',
        'sourceDomain_s': 'Internal',
        'sourceOriginDivision_s': 'Technology Risk',
        'fileFormat_s': 'pdf',
        'category_s': 'Standard',
        'lastUpdated_d': convert_to_long_type(t='2023-03-01', time_format='%Y-%m-%d'),
        'keywords_s': ['Privacy', 'Policy', 'Personal data security', 'Unauthorized Disclosures', 'Personal Data Usage'],
        'securityFramework_s': [],
        'securityControl_s': [],
        'reviewCadence_s': '',
        'useCase_s': 'Q&A'
    },
    {
        'title': 'FIRMWIDE STANDARD ON IDENTITY MANAGEMENT FOR INTERNAL APPLICATIONS',
        'sourceName_s': 'TR-Advisory',
        'sourceDomain_s': 'Internal',
        'sourceOriginDivision_s': 'Technology Risk',
        'fileFormat_s': 'pdf',
        'category_s': 'Policy',
        'lastUpdated_d': convert_to_long_type(t='2023-11-23', time_format='%Y-%m-%d'),
        'keywords_s': ['Identity Management', 'Internal Applications', 'Assets', 'Identity', 'Controls'],
        'securityFramework_s': [],
        'securityControl_s': [],
        'reviewCadence_s': '',
        'useCase_s': 'Q&A'
    },
    {
        'title': 'Client Security Statement',
        'sourceName_s': 'TR-AWM',
        'sourceDomain_s': 'Internal',
        'sourceOriginDivision_s': 'Technology Risk',
        'fileFormat_s': 'pdf',
        'category_s': 'Report',
        'lastUpdated_d': convert_to_long_type(t='2023-01-05', time_format='%Y-%m-%d'),
        'keywords_s': ['best practices', 'governance', 'audit', 'asset management', 'training', 'Identity and Access Management'],
        'securityFramework_s': [],
        'securityControl_s': [],
        'reviewCadence_s': 'annual',
        'useCase_s': 'Q&A'
    }
]

# Fetch PDF documents from SharePoint
USER_NAME = "dev_pranalytics_sys"
PASSWORD = "xY~&u6!kwHgC02;1)JDFpKP$]@[D:0@.ob.nd;i#Q4y[1Roa"

URL = "https://spe.web.sharepoint.gs.com/_api/web/GetFolderByServerRelativeUrl('%2FShared%20Documents%2FTRAI%2Fpdf')/Files/"
response = requests.get(
    URL,
    auth=HttpNtlmAuth(USER_NAME, PASSWORD),
    headers={
        'accept': "application/json;odata=verbose",
        'content-type': "application/json; odata=verbose"
    },
    verify="/etc/pki/tls/certs/gs-chains.pem"
)

decoded_response = response.content.decode("utf-8")
json_response = json.loads(decoded_response)

# Get all possible PDF files on SharePoint
all_files = [x['ServerRelativeUrl'] for x in json_response['d']['results']]
clean_files = [file.split('/')[-1].strip() for file in all_files]
full_path = max(all_files)
full_path = "%2F".join(full_path.split('/')[:-1])
full_path = re.sub(r'\\s', '%20', full_path)

# Iterate through all file names to create an input for Lex ingestion
poc_pdfs = [
    "FIRMWIDE STANDARD GLOBAL CLOUD GOVERNANCE_FINAL_10-Aug-2021_(v4.0).pdf",
    "FIRMWIDE POLICY ON PRIVACY_PROTECTION OF PERSONAL DATA_FINAL_01-Mar-2023_(v19.1).pdf",
    "FIRMWIDE STANDARD ON IDENTITY MANAGEMENT FOR INTERNAL APPLICATIONS_FINAL_23-Nov-2022_(v6.2).pdf",
    "Client Security Statement.pdf"
]

native_ids = [
    'DRO_firmwide_standard_0001',
    'DRO_firmwide_standard_0002',
    'DRO_firmwide_standard_0003',
    'DRO_QA_0001'
]

pdf = []
for idx, file in enumerate(poc_pdfs):
    URL = f"https://spe.web.sharepoint.gs.com/_api/web/GetFolderByServerRelativeUrl('{full_path}')/Files('{file}')/$value"
    output_response = requests.get(
        URL,
        auth=HttpNtlmAuth(USER_NAME, PASSWORD),
        headers={
            'accept': "application/json;odata=verbose",
            'content-type': "application/json; odata=verbose"
        },
        verify="/etc/pki/tls/certs/gs-chains.pem"
    )

    text = ""
    with io.BytesIO(output_response.content) as fh:
        pdf_input = PdfReader(fh)
        for page in pdf_input.pages:
            text += page.extract_text() + "\n"

    # Convert to base64 for Lex ingestion
    document = str(base64.b64encode(text.encode('utf-8')), 'utf-8')

    # Schema must follow Lex ingestion format
    fields_d = {
        'lastUpdated_d': metadata_fields[idx]['lastUpdated_d'],
        'title': metadata_fields[idx]['title'],
        'sourceName_s': metadata_fields[idx]['sourceName_s'],
        'sourceDomain_s': metadata_fields[idx]['sourceDomain_s'],
        'sourceOriginDivision_s': metadata_fields[idx]['sourceOriginDivision_s'],
        'fileFormat_s': metadata_fields[idx]['fileFormat_s']
    }
    
    with io.BytesIO(output_response.content) as fh:
        pdf_input = PdfReader(fh)
        for page in pdf_input.pages:
            text += page.extract_text() + "\n"

    # Convert to base64 for Lex ingestion
    document = str(base64.b64encode(text.encode('utf-8')), 'utf-8')

# Convert extracted text to base64 for Lex ingestion
document = str(base64.b64encode(text.encode('utf-8')), 'utf-8')

# Schema must follow Lex ingestion format
fields = {
    'lastUpdated_d': metadata_fields[idx]['lastUpdated_d'],
    'title': metadata_fields[idx]['title'],
    'sourceName_s': metadata_fields[idx]['sourceName_s'],
    'sourceDomain_s': metadata_fields[idx]['sourceDomain_s'],
    'sourceOriginDivision_s': metadata_fields[idx]['sourceOriginDivision_s'],
    'fileFormat_s': metadata_fields[idx]['fileFormat_s'],
    'category_s': metadata_fields[idx]['category_s'],
    'keywords_s': metadata_fields[idx]['keywords_s'],
    'securityFramework_s': metadata_fields[idx]['securityFramework_s'],
    'securityControl_s': metadata_fields[idx]['securityControl_s'],
    'reviewCadence_s': metadata_fields[idx]['reviewCadence_s'],
    'useCase_s': metadata_fields[idx]['useCase_s']
}

# Setting nativeId with the format of "DRO_{title with hyphen}_LastUpdatedDate"
# IMPORTANT: Ensure this format is recorded for prompt engineering and investigation
json_output = [{
    "nativeId": native_ids[idx],
    "title": metadata_fields[idx]['title'],
    "fileExtension": metadata_fields[idx]['fileFormat_s'],
    "mediaType": "text/plain",
    "entitlements": ["public"],
    "data": document,
    "privacyLevel": "public",
    "fields": fields
}]

pdf.append(json_output)

# API request for ingestion
doc_ids = []
for idx, payload in enumerate(pdf):
    headers = {
        'Cookie': f'GSSSO={gs_auth.get_gssso()}',
        'x-api-key': f'GSSSO={gs_auth.get_gssso()}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    ingestion = {
        "url": "https://dev.genai.site.gs.com/ingestion/v1/tech_risk_ai/ingest",
        "payload": json.dumps(payload),
        "headers": headers
    }

    response = requests.request('POST', ingestion['url'], headers=ingestion['headers'], data=ingestion['payload'], verify=False)
    print(f"Response :: {response.text}")

    ingestion['documentId'] = response.json()["successDocs"][0]["documentId"]
    print(f"doc_id :: {ingestion['documentId']}")
    doc_ids.append(ingestion["documentId"])

#doc_ids = [
#    "tech_risk_ai_9caeca0d-b927-479d-85e7-efe9bf37d6e4",
#    "tech_risk_ai_82ff4fdd-fcf9-4828-b89c-25c6c78f7091",
#    "tech_risk_ai_75a8087f-f246-4b09-a10c-87fe2d5d792f",
#    "tech_risk_ai_35b65e20-6939-4ff9-94e0-533b7aa93754"
#]

for doc_id in doc_ids:
    status = {
        'url': f'https://dev.genai.site.gs.com/ingestion/v1/status/tech_risk_ai/{doc_id}',
        'headers': headers
    }

    response = requests.request('GET', status['url'], headers=status['headers'], verify=False)
    print(response.text)

query = "recovery from cyber attacks"
search = {
    'url': "https://dev.genai.site.gs.com/search/v1/search/query",
    'headers': headers,
    'payload': json.dumps({
        'query': query,
        'source': 'TEST',
        'size': 2,
        'page': 1,
        'schemaIds': ['tech_risk_ai'],
        'queryFilters': {},
        'rankingProfile': 'hybrid'
    })
}

response = requests.request('POST', search['url'], headers=search['headers'], data=search['payload'], verify=False)
print("Results:")
res = [(c['id'], c['fields']['title'], c['fields']['data']) for c in response.json()['data']['searchResults']]

for r in res:
    print(f"Title :: {r[1]}")
    print(f"ID :: {r[0]}")
    print(f"Text Summary :: " + (r[2][:150] + '...') if len(r[2]) > 75 else r[2])


headers = {
    'Cookie': f'GSSSO={gs_auth.get_gssso()}',
    'x-api-key': f'GSSSO={gs_auth.get_gssso()}',
    'Accept': 'text/plain',
    'Content-Type': 'text/plain'
}

response = requests.delete(
    "https://dev.genai.site.gs.com/ingestion/v1/tech_risk_ai/nativeId/DRO_three_little_pigs",
    headers=headers,
    verify=False
)

print(response.text)
