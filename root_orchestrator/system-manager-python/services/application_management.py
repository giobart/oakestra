import traceback

from ext_requests.apps_db import *
from services.service_management import delete_service, create_services_of_app


def register_app(applications, userid):
    for application in applications['applications']:
        if mongo_find_app_by_name_and_namespace(
                application.get('application_name'), application.get('application_namespace')
        ):
            return {'message': 'An application with the same name and namespace exists already'}, 409
        if not valid_app_requirements(application):
            return {'message': 'Application name or namespace are not in the valid format'}, 422

        if "action" in application:
            del application['action']
        if "_id" in application:
            del application['_id']
        application['userId'] = userid
        microservices = application.get('microservices')
        application['microservices'] = []
        app_id = mongo_add_application(application)

    return mongo_get_applications_of_user(userid), 200


def update_app(appid, userid, fields):
    # TODO: fields validation before update
    return mongo_update_application(appid, userid, fields)


def delete_app(appid, userid):
    application = get_user_app(userid, appid)
    for service_id in application.get('microservices'):
        delete_service(userid, service_id)
    return mongo_delete_application(appid, userid)


def users_apps(userid):
    return mongo_get_applications_of_user(userid)


def all_apps():
    return mongo_get_all_applications()


def get_user_app(userid, appid):
    return mongo_find_app_by_id(appid, userid)


def valid_app_requirements(app):
    if len(app['application_name']) > 10 or len(app['application_name']) < 1:
        return False
    if len(app['application_namespace']) > 10 or len(app['application_namespace']) < 1:
        return False
    return True
