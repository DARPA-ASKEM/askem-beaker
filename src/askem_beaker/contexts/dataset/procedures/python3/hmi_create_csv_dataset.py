import os
import requests
import tempfile

from json import JSONDecodeError

with tempfile.TemporaryFile() as temp_csv_file:
    {{ var_name|default("df") }}.to_csv(temp_csv_file, index=True, header=True)
    temp_csv_file.seek(0)
    # Set the HMI_SERVER endpoint
    hmi_server = "{{dataservice_url}}"

    # Define the id and filename dynamically
    id = "{{id}}"
    filename = "{{filename}}"

    # Prepare the request payload
    payload = {'id': id, 'filename': filename}
    files = {'file': temp_csv_file}

    # Set the headers with the content type
    # headers = {}

    # Make the HTTP PUT request to upload the file bytes
    url = f'{hmi_server}/datasets/{id}/upload-csv'
    response = requests.put(url, data=payload, files=files, auth=("{{username}}", "{{password}}"))

    # Check the response status code
    if response.status_code < 300:
        try:
            message = response.json()
        except JSONDecodeError:
            message = f'File uploaded successfully with status code {response.status_code}.'
    else:
        message = f'File upload failed with status code {response.status_code}.'
        if response.text:
            message += f' Response message: {response.text}'

    message
