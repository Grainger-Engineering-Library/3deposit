import requests
import json
from uuid import uuid4

url = "https://3deposit.library.illinois.edu/api/form/upload"
DEPOSIT_ID = str(uuid4())

querystring = {"resumableChunkNumber": "1", "resumableTotalChunks": "1", "deposit_id": DEPOSIT_ID}

f = open('a-frame.zip', 'rb')
files = {'file': f}

response = requests.request("POST", url, files=files, params=querystring, verify=False)

print(response.text)
url = "https://3deposit.library.illinois.edu/api/form/submit"
payload_dict = { 
    'media_type': 'vr',
    'id': DEPOSIT_ID,
    'form': [
        {
            'id': 'object_title',
            'value': 'VR Scene'
        },
        {
            'id': 'media_type',
            'value': 'vr'
        },
        {
            'id': 'description',
            'value': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'
        }
    ]
}

payload = json.dumps(payload_dict)

response = requests.request("POST", url, data=payload, verify=False)

print(response.text)
