from views import (index, login, logout, 
                    active_deposit_form, upload_file,
                    minio_buckets, services_configs)


def setup_routes(app):

    """
    Frontend routes

    auth routes: manage authentication for dashboard views
    api routes:  serve resources from service endpoints
    """

    # auth routes
    app.router.add_get('/', index, name='index')
    app.router.add_get('/login', login, name='login')
    app.router.add_post('/login', login, name='login')
    app.router.add_get('/logout', logout, name='logout')

    # service config routes
    app.router.add_get('/services/configs', services_configs)
    app.router.add_post('/services/configs', services_configs)


    # deposit form routes
    app.router.add_get('/deposit_form/active', active_deposit_form)
    app.router.add_post('/deposit_form/active', active_deposit_form)
    app.router.add_view('/deposit_form/upload', upload_file)

    # object storage routes
    app.router.add_get('/minio/buckets', minio_buckets)
    app.router.add_post('/minio/buckets', minio_buckets)