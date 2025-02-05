import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import time
from etl.config import config
from etl.utils import Utils
import gs_auth

logger = Utils.get_logger("FISValidator")

class FISValidator:
    """
    A singleton class responsible for validating files through the FIS API.

    This class implements the singleton design pattern to ensure that only one instance
    of the validator exists throughout the application lifecycle. It provides a method
    to upload files to the FIS API for validation and handles retries upon failure.

    Attributes:
        _instance (FISValidator): A private class attribute that holds the singleton instance.
    """

    _instance = None

    def __new__(cls):
        """
        Overrides the object creation process to ensure only one instance exists.

        Returns:
            FISValidator: The singleton instance of the FISValidator class.
        """
        if cls._instance is None:
            cls._instance = super(FISValidator, cls).__new__(cls)
        return cls._instance

    def upload_file(self, file_path):
        """
        Uploads a file to the FIS API for validation and returns the validation result.

        This method uploads a file specified by the file_path parameter to the FIS API for validation.
        It retries the upload process up to a maximum number of retries if the validation result is not
        'APPROPRIATE' or if a request error occurs.

        Args:
            file_path (str): The path to the file that needs to be validated.

        Returns:
            bool: Returns True if the file is validated as 'APPROPRIATE', False otherwise.
        """
        session = requests.Session()
        api_key = str(config['FIS']['FIS_api_key']).strip()
        session.headers.update({'api-key': api_key})
        session.cookies.set('GSSSO', gs_auth.get_gssso())

        max_retries = 2
        retries = 0
        retry_delay = 2

        submission_url = str(config['FIS']['submission_url']).strip()

        while retries < max_retries:
            multipart_data = MultipartEncoder(
                fields={
                    'fileToScan': ('filename.pdf', open(file_path, 'rb'), 'application/pdf')
                }
            )

            try:
                response = session.post(
                    submission_url,
                    data=multipart_data,
                    headers={'Content-Type': multipart_data.content_type},
                    verify=False,
                    timeout=10
                )

                if response.status_code == 200:
                    submission_response = response.json()
                    submission_id = submission_response['id']
                    logger.info(f"Submission ID: {submission_id}")

                    validation_url = f"{submission_url}/{submission_id}"

                    max_poll_time = 60  
                    poll_interval = 2   
                    start_time = time.time()
                    while True:
                        validation_response = session.get(
                            validation_url,
                            headers={'api-key': api_key},
                            timeout=10
                        )
                        if validation_response.status_code == 200:
                            validation_result = validation_response.json()

                            if validation_result['submission']['progress'] == "COMPLETE":
                                result = validation_result['submission']['results']['result']
                                logger.info(f"Results: {validation_result['submission']['results']}")

                                if result == "APPROPRIATE":
                                    return True
                                else:
                                    logger.warning("Result not APPROPRIATE. FIS validation failed.")
                                    return False
                            else:
                                if time.time() - start_time > max_poll_time:
                                    logger.error("Polling timed out waiting for a complete validation result.")
                                    return False
                                logger.info("Validation in progress. Waiting...")
                                time.sleep(poll_interval)
                        else:
                            logger.error("Error fetching validation result. Status Code: {}".format(validation_response.status_code))
                            return False

            except requests.exceptions.RequestException as e:
                logger.error(f"An error occurred: {e}")
                return False
            

            finally:
                retries += 1
                retry_delay *= 2

        return False
