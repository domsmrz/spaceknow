import requests

AUTH_URL = 'https://spaceknow.auth0.com/oauth/ro'
_token = None


def get_token(username: str, password: str):
    global _token
    if _token is None:
        _token = _request_token(username, password)
    return _token


def _request_token(username: str, password: str):
    data = {
        'client_id': 'hmWJcfhRouDOaJK2L8asREMlMrv3jFE1',
        'username': username,
        'password': password,
        'connection': 'Username-Password-Authentication',
        'grant_type': 'password',
        'scope': 'openid'
    }
    response = requests.post(AUTH_URL, data=data)
    return response.json()['id_token']
