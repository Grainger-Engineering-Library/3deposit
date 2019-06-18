import json
import logging
import os
import aiohttp_jinja2
from aiohttp import web, FormData, ClientSession
from aiohttp import request as new_request
from aiohttp_security import remember, forget, authorized_userid

import db
from forms import validate_login_form

import logging


def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)

"""
View endpoints for authorizing user

'index', 'login', and 'logout' validate user, store secure cookie
"""

@aiohttp_jinja2.template('index.html')
async def index(request):
    username = await authorized_userid(request)
    if not username:
        raise redirect(request.app.router, 'login')

    async with request.app['db'].acquire() as conn:
        current_user = await db.get_user_by_name(conn, username)

    return {'current_user': current_user}


@aiohttp_jinja2.template('login.html')
async def login(request):
    username = await authorized_userid(request)
    if username:
        raise redirect(request.app.router, 'index')

    if request.method == 'POST':
        form = await request.post()

        async with request.app['db'].acquire() as conn:
            error = await validate_login_form(conn, form)

            if error:
                return {'error': error}
            else:
                response = redirect(request.app.router, 'index')

                user = await db.get_user_by_name(conn, form['username'])
                await remember(request, response, user['username'])

                raise response

    return {}


async def logout(request):
    response = redirect(request.app.router, 'login')
    await forget(request, response)
    return response



"""
Helper function to relay form data with files
"""
# async def form_data_from_request(request):
#     fd = FormData()
#     auth = json.dumps({'auth': {'auth_key': 'auth_value'}})
#     data = json.dumps({'deposit_id': '12345'})
#     fd.add_field('config', auth, content_type='application/json')
#     fd.add_field('data', data, content_type='application/json')
#     fd.add_field('files', open('test.txt', 'rb'), filename='test.txt')
#     async with new_request.post(SERVICE_ENDPOINT, data=fd) as resp:
#         return web.json_response({"res": await resp.json() })


"""
Handlers for getting and setting services & service configs
"""

async def services(request):
    if request.method == 'GET':
        try:
            async with request.app['db'].acquire() as conn:
                services = await db.get_services(conn)
                if services:
                    return web.json_response({ 'services': services }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
                else:
                    return web.json_response({ 'res': 'no services'}, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
        except Exception as err:
            return web.json_response({ 'err': str(err) }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))

async def services_configs(request):

    headers = {
        'ACCESS-CONTROL-ALLOW-ORIGIN': '*',
        'Access-Control-Allow-Headers': 'content-type'
    }
    if request.method == 'GET':
        try:
            req = request.query
            async with request.app['db'].acquire() as conn:
                service_config = await db.get_service_config(conn=conn, name=req.get('name'))
                if service_config:
                    return web.json_response({ 'service_config': service_config }, headers=headers)
                else:
                    return web.json_response({ 'err': 'No matching service', 'req': req }, headers=headers)
        except Exception as err:
            return web.json_response({ 'err': str(err), 'req': req }, headers=headers)
    if request.method == 'POST':
        """
        request.json():
        {
            "name": "minio",
            "endpoint": "http://minio-service:5000/bucket",
            "config": {
                "auth": {
                    "access_key": "AKIAIOSFODNN7GRAINGER",
                    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYGRAINGERKEY"
                }
            }
        }
        """
        try:
            req = await request.json()
            async with request.app['db'].acquire() as conn:
                service = await db.set_service_config(conn=conn, name=req.get('name'), endpoint=req.get('endpoint'), config=req.get('config'))
                if service:
                    return web.json_response({ 'res': service }, headers=headers)
                else:
                    return web.json_response({'req':str(req),'err':'Could not create service.'}, headers=headers)
        except Exception as err:
            return web.json_response({ 'err': str(err) }, headers=headers)

async def services_actions(request):
    if request.method == 'GET':
        try:
            async with request.app['db'].acquire() as conn:
                services = await db.get_action_services(conn)
                if services:
                    return web.json_response({ 'services': services }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
                else:
                    return web.json_response({ 'res': 'no action services'}, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
        except Exception as err:
            return web.json_response({ 'err': str(err) }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))


"""
Handlers for deposit form frontend
"""

async def deposit_form_active(request):
    if request.method == 'GET':
        async with request.app['db'].acquire() as conn:
            active_form = await db.get_active_form(conn)
        if active_form:
            return web.json_response({ 'active_form': active_form }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
        else:
            return web.json_response({ 'err': 'No active form' }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))

    if request.method == 'POST':
        try:
            # logging.debug(msg="Is JSON:".format(request.is_json))
            # logging.debug(msg=str)
            req = await request.json()
            async with request.app['db'].acquire() as conn:
                try:
                    await db.create_active_form(conn, req['content'], req['active'])
                    return web.json_response({ "succeeded": True, "msg": "New active form created" })
                except Exception as e:
                    return web.json_response({ "err": str(e) })
        except Exception as e:
            return web.json_response({ "err": str(e) })


async def deposit_upload(request):
    headers = dict({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'})
    if request.method == 'POST':
        try:
            logging.debug(msg='query: {}'.format(request.query))
            reader = await request.multipart()
            did = request.query['deposit_id']
            logging.debug('uploading {}'.format(str(did)))
            rcn = int(request.query['resumableChunkNumber'])
            rtc = int(request.query['resumableTotalChunks'])
            while True:
                part = await reader.next()
                if part is None:
                    break
                if part.name == 'file':
                    if rcn == 1:
                        with open('./data/{}'.format(did+'_partial'), 'wb') as f:
                            b = await part.read()
                            f.write(b)
                    elif rcn > 1:
                        with open('./data/{}'.format(did+'_partial'), 'ab') as f:
                            b = await part.read()
                            f.write(b)
                    if rcn == rtc:
                        os.rename('./data/{}'.format(did+'_partial'), './data/{}'.format(did))
            return web.Response(status=200, headers=headers)       
        except Exception as err:
            logging.debug(msg='err: {}'.format(str(err)))
            return web.json_response({ 'err': str(err) }, headers=headers)
    else:
        return web.Response(status=200, headers=headers)


"""
Trigger function to begin storage operation with buffered deposit file
"""

async def trigger_store(did):
    fd = FormData()
    deposit_id = dict({'deposit_id': did})
    with open('./data/{}'.format(did), 'rb') as f:
        fd.add_field('file', f, filename=did, content_type='application/octet-stream')
        async with ClientSession() as sess:
            async with sess.request(url='http://gateway:8080/store/objects', method='POST', data=fd, params=deposit_id) as resp:
                resp_json = await resp.json()
                logging.debug(msg=str(resp_json))
    os.remove('./data/{}'.format(did))

async def trigger_publish(did, metadata):
    deposit_id = dict({ 'deposit_id': did })
    fd = FormData()
    fd.add_field('data', metadata, content_type='application/json')
    with open('./data/{}'.format(did), 'rb') as f:
        fd.add_field('file', f, filename=did, content_type='application/octet-stream')
    if metadata.get('media_type') == 'model':
        async with new_request.post(url='http://gateway:8080/publish/models', data=fd, params=deposit_id) as resp:
            resp_json = await resp.json()
            logging.debug(msg=str(resp_json))
    elif metadata.get('media_type') == 'video':
        async with new_request.post(url='http://gateway:8080/publish/videos', data=fd, params=deposit_id) as resp:
            resp_json = await resp.json()
            logging.debug(msg=str(resp_json))
    elif metadata.get('media_type') == 'vr':
        async with new_request.post(url='http://gateway:8080/publish/vr', data=fd, params=deposit_id) as resp:
            resp_json = await resp.json()
            logging.debug(msg=str(resp_json))

"""
Helper function to return service configs for a given action
"""
async def get_service_config_by_action(request, action, media_type='default'):
    try:
        async with request.app['db'].acquire() as conn:
            action_service_name = await db.get_action_service_name(conn=conn, action=action, media_type=media_type)
        async with request.app['db'].acquire() as conn:
            service_config = await db.get_service_config(conn=conn, name=action_service_name)
            if service_config:
                return service_config
            else:
                return None
    except Exception as err:
        return web.json_response({ 'err': str(err) })


"""
Relay endpoint to make object storage calls
Endpoints are scoped for objects and buckets
"""

async def store_buckets(request):
    PATH = '/bucket'
    service_config = await get_service_config_by_action(request=request, action='store')
    config = service_config.get('config')
    endpoint = service_config.get('endpoint')
    if request.method == 'GET':
        try:
            data = request.query
            config.update({'bucket_name': data.get('bucket_name')})
            fd = FormData()
            fd.add_field('config', json.dumps(config), content_type='application/json')
            async with new_request(method='GET', url=endpoint+PATH, data=fd) as resp:
                try:
                    resp_json = await resp.json()
                except Exception as err:
                    return web.json_response({'err': str(err), 'resp': await resp.text()})
                return web.json_response({ 'resp': resp_json })
        except Exception as err:
            return web.json_response({ 'origin': 'gateway', 'err': str(err) })

    if request.method == 'POST':
        try:
            data = await request.json()
            payload = dict({'config': config, 'data': data})
            async with new_request(method='POST', url=endpoint+PATH, data=payload) as resp:
                resp_json = await resp.json()
                return web.json_response({ 'resp': resp_json })
        except Exception as err:
            return web.json_response({ 'origin': 'gateway', 'err': str(err) })


async def store_objects(request):
    PATH = '/object'
    service_config = await get_service_config_by_action(request=request, action='store', media_type='default')
    config = service_config.get('config')
    endpoint = service_config.get('endpoint')
    bucket_name = dict({'bucket_name': '3deposit'})
    config.update(bucket_name)

    if request.method == 'GET':
        try:
            data = request.query
            config.update({'bucket_name': data.get('bucket_name')})
            payload = dict({'config': config})
            async with new_request(method='GET', url=endpoint+PATH, json=payload) as resp:
                try:
                    resp_json = await resp.json()
                except Exception as err:
                    return web.json_response({'err': str(err), 'resp': await resp.text()})
                return web.json_response({ 'resp': resp_json, 'payload': payload })
        except Exception as err:
            return web.json_response({ 'origin': 'gateway', 'err': str(err) })

    if request.method == 'POST':
        try:
            q = dict(request.query)
            fd = FormData()
            reader = await request.multipart()
            while True:
                part = await reader.next()
                if part is None:
                    break
                if part.name == 'file':
                    fd.add_field(name='file', value=await part.read(), filename=q.get('deposit_id'), content_type='application/octet-stream')
                else:
                    continue
            fd.add_field('config', json.dumps(config), content_type='application/json')
            fd.add_field('data', json.dumps(q), content_type='application/json')
            async with new_request(method='POST', url=endpoint+PATH, data=fd) as resp:
                resp_json = await resp.json()
                return web.json_response({ 'resp': resp_json })
        except Exception as err:
            return web.json_response({ 'origin': 'gateway', 'err': str(err) })


"""
Relay endpoint to get/post to Model publication service
"""
async def publish_models(request):
    service_config = await get_service_config_by_action(request=request, action='publish', media_type='models')
    service_name = service_config.get('name')
    try:
        async with request.app['db'].acquire() as conn:
            service_config = await db.get_service_config(conn=conn, name=service_name)
            if service_config:
                endpoint = service_config.get('endpoint')
                config = service_config.get('config')
            else:
                return web.json_response({ 'err': 'could not retrieve config for service: {}'.format(service_name)})
    except Exception as err:
        return web.json_response({ 'err': str(err) })

    if request.method == 'GET':
        try:
            data = request.query
            config.update({'bucket_name': data.get('bucket_name')})
            payload = dict({'config': config})
            async with new_request(method='GET', url=endpoint, json=payload) as resp:
                try:
                    resp_json = await resp.json()
                except Exception as err:
                    return web.json_response({'err': str(err), 'resp': await resp.text()})
                return web.json_response({ 'resp': resp_json, 'payload': payload })
        except Exception as err:
            return web.json_response({ 'origin': 'gateway', 'err': str(err) })

    if request.method == 'POST':
        try:
            q = request.query
            fd = FormData()
            reader = await request.multipart()
            while True:
                part = await reader.next()
                if part is None:
                    break
                if part.name == 'data':
                    fd.add_field('data', await part.json(), content_type='application/json')
                if part.name == 'file':
                    fd.add_field(name='file', value=await part.read(), filename=q.get('deposit_id'), content_type='application/octet-stream')
                else:
                    continue
            fd.add_field('config', json.dumps(config), content_type='application/json')
            fd.add_field('data', json.dumps(q), content_type='application/json')
            async with new_request(method='POST', url=endpoint, data=fd) as resp:
                resp_json = await resp.json()
                return web.json_response({ 'resp': resp_json })
            data = await request.json()
            payload = dict({'config': config, 'data': data})
            async with new_request(method='POST', url=endpoint, json=payload) as resp:
                resp_json = await resp.json()
                return web.json_response({ 'resp': resp_json })
        except Exception as err:
            return web.json_response({ 'origin': 'gateway', 'err': str(err) })