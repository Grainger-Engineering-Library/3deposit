import os
import json
import requests
import vimeo
from flask import Flask, request, jsonify

'''
Flask app that takes in 360 video file, JSON data, and credentials 
and publishes to Vimeo. 

'''

app = Flask(__name__)

@app.route('/vimeo', methods=['POST', 'GET'])
def post_to_vimeo():
    post_data = json.loads(request.form.get('data'))
    if post_data:
        auth = post_data.get('auth')
        if auth:
            access_token = auth.get('access_token')
            client_id = auth.get('client_id')
            client_secret = auth.get('client_secret')
        else:
            return jsonify({'err': 'No auth provided'})

        # construct request
        client = vimeo.VimeoClient(
            token=access_token,
            key=client_id,
            secret=client_secret
        )

    if request.method == 'POST':
        try:
            # unpack payload
            metadata = post_data.get('metadata')
            if metadata:
                name = metadata.get('name')
                description = metadata.get('description')
                filename = metadata.get('filename')
                projection = metadata.get('projection')
                stereo_format = metadata.get('stereo_format')
            else:
                return jsonify({'err': 'No post data'})

            file = request.files.get('file')
            if file and filename:
                file.save(filename)

                uri = client.upload(filename, data={
                    'name': name,
                    'description': description
                })

                os.remove(filename)
                return response = client.get(uri + '?fields=link').json()
            else:
                return jsonify({'err': 'No file provided'})
        except Exception as err:
            return jsonify({'err': err})

    if request.method == 'GET':
        try:
            # unpack payload
            post_data = json.loads(request.form.get('data'))
            if post_data:
                auth = post_data.get('auth')
                if auth:
                    access_token = auth.get('access_token')
                    client_id = auth.get('client_id')
                    client_secret = auth.get('client_secret')
                else:
                    return jsonify({'err': 'No auth provided'})
                metadata = post_data.get('metadata')
                if metadata:
                    name = metadata.get('name')
                    description = metadata.get('description')
                    filename = metadata.get('filename')
                    projection = metadata.get('projection')
                    stereo_format = metadata.get('stereo_format')
                else:
                    return jsonify({'err': 'No post data'})
            file = request.files.get('file')
            if file and filename:
                file.save(filename)
                # construct request
                client = vimeo.VimeoClient(
                    token=access_token,
                    key=client_id,
                    secret=client_secret
                )
                uri = client.upload(filename, data={
                    'name': name,
                    'description': description
                })
                os.remove(filename)
                return response = client.get(uri + '?fields=link').json()
            else:
                return jsonify({'err': 'No file provided'})
        except Exception as err:
            return jsonify({'err': err})

if __name__ == '__main__':
    app.run(debug=True)
