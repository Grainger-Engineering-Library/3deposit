import json

import aiohttp_jinja2
from aiohttp import web, FormData
from aiohttp import request as new_request
from aiohttp_security import remember, forget, authorized_userid

import db
from forms import validate_login_form


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
async def form_data_from_request(request):
    fd = FormData()
    auth = json.dumps({'auth': {'auth_key': 'auth_value'}})
    data = json.dumps({'deposit_id': '12345'})
    fd.add_field('config', auth, content_type='application/json')
    fd.add_field('data', data, content_type='application/json')
    fd.add_field('files', open('test.txt', 'rb'), filename='test.txt')
    async with new_request.post(SERVICE_ENDPOINT, data=fd) as resp:
        return web.json_response({"res": await resp.json() })


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
            return web.json_response({ 'err': str(err) })

async def services_configs(request):
    if request.method == 'GET':
        try:
            req = await request.json()
            async with request.app['db'].acquire() as conn:
                service_config = await db.get_service_config(conn=conn, name=req.get('name'))
                if service_config:
                    return web.json_response({ 'service_config': service_config }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
                else:
                    return web.json_response({ 'err': 'No matching service', 'req': req }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
        except Exception as err:
            return web.json_response({ 'err': str(err), 'req': req }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
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
                    return web.json_response({ 'res': service })
        except Exception as err:
            return web.json_response({ 'err': str(err) })


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
            req = await request.json()
            async with request.app['db'].acquire() as conn:
                try:
                    await db.create_active_form(conn, req['content'], req['active'])
                    return web.json_response({ "succeeded": True, "msg": "New active form created" })
                except Exception as e:
                    return web.json_response({ "err": str(e) })
        except Exception as e:
            return web.json_response({ "err": str(e) })


async def deposit_form_upload(request):
    if request.method == 'POST':
        try:
            req = await request.read()
            return web.Response(text=str(req), headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
        except Exception as err:
            return web.json_response({ 'err': str(err) }, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))
    else:
        return web.Response(status=200, headers=({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'}))     

"""
Relay endpoint to make object storage calls
Endpoints are scoped for objects and buckets
"""

async def minio_buckets(request):

    SERVICE_NAME = 'minio'

    try:
        async with request.app['db'].acquire() as conn:
            service_config = await db.get_service_config(conn=conn, name=SERVICE_NAME)
            if service_config:
                endpoint = service_config.get('endpoint')
                config = service_config.get('config')
            else:
                return web.json_response({ 'err': 'could not retrieve config for service: {}'.format(SERVICE_NAME)})
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
            data = await request.json()
            payload = dict({'config': config, 'data': data})
            async with new_request(method='POST', url=endpoint, json=payload) as resp:
                resp_json = await resp.json()
                return web.json_response({ 'resp': resp_json })
        except Exception as err:
            return web.json_response({ 'origin': 'gateway', 'err': str(err) })




