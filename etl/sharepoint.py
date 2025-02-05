"""
Module: sharepoint.py
Description: Provides the SharePointClient class to interact with SharePoint, handling file downloads,
folder path retrieval, and NTLM authentication.
"""
import re
import requests
from requests_ntlm import HttpNtlmAuth
from etl import config
from etl.utils import Utils

logger = Utils.get_logger("sharepoint")

class SharePointClient:
    def __init__(self, username=None, password=None, base_url=None, verify_cert=None):
        try:
            self.username = username if username is not None else config["user_name"]
            self.password = password if password is not None else config["password"]
            self.base_url = base_url if base_url is not None else config["sharepoint_base_url"]
            self.verify_cert = verify_cert if verify_cert is not None else config["verify_cert"]
            self.pdf_url = config["sharepoint_pdf_url"]
        except Exception as e:
            logger.error("Error initializing SharePointClient: {}".format(e))
            raise

    def get_sharepoint_folder_path(self):
        """
        Fetch the SharePoint PDF folder details and deduce the base folder path.
        """
        try:
            response = requests.get(
                self.pdf_url,
                auth=HttpNtlmAuth(self.username, self.password),
                headers={
                    'accept': "application/json;odata=verbose",
                    'content-type': "application/json; odata=verbose"
                },
                verify=self.verify_cert
            )
            response.raise_for_status()
            json_response = response.json()
            all_files = [x['ServerRelativeUrl'] for x in json_response['d']['results']]
            full_path = max(all_files)
            full_path = "%2F".join(full_path.split('/')[:-1])
            full_path = re.sub(r'\\s', '%20', full_path)
            logger.info("Determined SharePoint folder path: {}".format(full_path))
            return full_path
        except Exception as e:
            logger.error("Error fetching SharePoint folder path: {}".format(e))
            raise

    def download_pdf(self, file_name, folder_path):
        """
        Download a PDF file from SharePoint given its file name and folder path.
        Returns the PDF content in bytes.
        """
        try:
            url = f"{self.base_url}/_api/web/GetFolderByServerRelativeUrl('{folder_path}')/Files('{file_name}')/$value"
            response = requests.get(
                url,
                auth=HttpNtlmAuth(self.username, self.password),
                headers={
                    'accept': "application/json;odata=verbose",
                    'content-type': "application/json; odata=verbose"
                },
                verify=self.verify_cert
            )
            response.raise_for_status()
            logger.info("Downloaded file {} from SharePoint.".format(file_name))
            return response.content
        except Exception as e:
            logger.error("Error downloading file {} from SharePoint: {}".format(file_name, e))
            raise 