from flask_jwt_extended import get_jwt_identity, jwt_required, create_access_token, create_refresh_token, get_jwt, \
    verify_jwt_in_request, decode_token

from ext_requests.user_db import mongo_get_user_by_name


class Role:
    ADMIN = "Admin"
    APP_Provider = "Application_Provider"
    INF_Provider = "Infrastructure_Provider"


not_authorized = {"message": "You have not enough permissions!"}, 403


def user_has_role(user, role):
    return next(
        filter(lambda role_: role_["name"] == role, user['roles']), None)


def require_role(required_role):
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = get_jwt_auth_identity()
            users = mongo_get_user_by_name(current_user)
            if users and user_has_role(users, required_role):
                return func(*args, **kwargs)
            else:
                return not_authorized

        return wrapper

    return decorator


def identity_is_username():
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = get_jwt_auth_identity()
            if current_user == kwargs['username']:
                return func(*args, **kwargs)
            else:
                return not_authorized

        return wrapper

    return decorator


def has_access_to_user(username):
    user = get_jwt_auth_identity()
    return username == user


def jwt_auth_required():
    def wrapper(fn):
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as e:
                print(e)
                return {"message": "Missing authentication token"}, 401
            claims = get_jwt()
            if not ('file_access_token' in claims and claims['file_access_token']):
                return fn(*args, **kwargs)
            else:
                return {"message": "Only access token allowed"}, 401

        return decorator

    return wrapper


def get_jwt_auth_identity():
    return get_jwt_identity()


def get_jwt_auth_claims():
    return get_jwt()


def refresh_token_required():
    return jwt_required(refresh=True)


def create_jwt_auth_access_token(identity, additional_claims):
    return create_access_token(identity=identity, additional_claims=additional_claims)


def create_jwt_auth_refresh_token(identity):
    return create_refresh_token(identity=identity)


def create_jwt_pairing_key_cluster(identity, expiration, claims):
    return create_access_token(identity=identity, expires_delta=expiration, additional_claims=claims)


def create_jwt_secret_key_cluster(identity, expiration, claims):
    return create_access_token(identity=identity, expires_delta=expiration, additional_claims=claims)


def check_jwt_token_validity(token):
    return decode_token(encoded_token=token, allow_expired=False)
