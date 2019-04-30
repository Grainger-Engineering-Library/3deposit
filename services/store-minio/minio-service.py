import os
import json
from flask import Flask, request, jsonify
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)


# ACCESS KEY AKIAIOSFODNN7GRAINGER
# SECRET KEY wJalrXUtnFEMI/K7MDENG/bPxRfiCYGRAINGERKEY

SERVER_ENDPOINT = 'minio-server:9000'
BUCKET_NAME = '3deposit'


app = Flask(__name__)

@app.route('/minio', methods=['GET', 'POST'])
def minio():
    if request.method == 'GET':
        # get keys from request args
        access_key = request.args.get('access_key')
        secret_key = request.args.get('secret_key')        

        # Initialize minioClient with an endpoint and keys.
        minioClient = Minio(SERVER_ENDPOINT,
                            access_key=access_key,
                            secret_key=secret_key,
                            secure=False)

        # get objects from bucket
        objects = minioClient.list_objects(BUCKET_NAME, recursive=True)
    # construct response object from objects iterable
    obj_json = {}
    for obj in objects:
        obj_json.update({"bucket": str(obj.bucket_name), "object": str(obj.object_name), "modified": str(obj.last_modified),
            "etag": str(obj.etag), "size": str(obj.size), "content_type": str(obj.content_type)})
    print(type(obj_json), obj_json)        
    return jsonify(obj_json)        

    if request.method == 'POST':
        # get data from request payload
        data = json.loads(request.form.get('data'))

        # extract metadata object & needed values
        metadata = data.get('metadata')
        deposit_id = metadata['deposit_id']

        # extract authentication credentials
        auth = data.get('auth')
        access_key = auth.get('access_key')
        secret_key = auth.get('secret_key')

        # extract file & temp save to disk
        file = request.files['file']
        file.save(deposit_id)

        # Initialize minioClient with an endpoint and keys.
        minioClient = Minio(SERVER_ENDPOINT,
                            access_key=access_key,
                            secret_key=secret_key,
                            secure=False)   

        try:
            minioClient.make_bucket(BUCKET_NAME)
        except ResponseError as err:
            return jsonify({"error": err})                    

        try:
            r = minioClient.fput_object(BUCKET_NAME, deposit_id, deposit_id)
            return jsonify({"etag": r})
            # cleanup temp file
            os.remove(deposit_id)
        except ResponseError as err:
            return jsonify({"error": err})


if __name__ == '__main__':
    app.run()
