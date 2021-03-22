from datetime import datetime, timedelta
import json
import requests
from time import sleep
from typing import Any, Dict

AUTH_URL = 'https://spaceknow.auth0.com/oauth/ro'
BASE_URL = 'https://api.spaceknow.com'


class FailedTask(RuntimeError):
    pass


class RequestError(RuntimeError):
    pass


class LongTaskRecord:
    def __init__(self, url: str, next_try: datetime):
        self.url = url
        self.next_try = next_try

    def __iter__(self):
        yield self.url
        yield self.next_try

    url: str
    next_try: datetime


class SpaceKnowApi:
    def __init__(self, username: str, password: str):
        self._auth_token = self._request_token(username, password)
        self._long_tasks: Dict[str, LongTaskRecord] = dict()

    @staticmethod
    def _request_token(username: str, password: str) -> str:
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

    def _post(self, url: str, data: Any) -> Dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._auth_token}",
        }
        response = requests.post(f'{BASE_URL}{url}', headers=headers, data=json.dumps(data))
        response_json = response.json()
        if not response.ok:
            raise RequestError(f'{response_json["error"]}: {response_json.get("errorMessage", None)}')
        return response_json

    def get(self, url: str) -> Any:
        return requests.get(f'{BASE_URL}{url}').content

    def initiate(self, url: str, data: Any) -> str:
        response_json = self._post(f'{url}/initiate', data=data)
        next_try = datetime.now() + timedelta(seconds=int(response_json['nextTry']))
        pipeline_id = response_json['pipelineId']
        self._long_tasks[pipeline_id] = LongTaskRecord(url, next_try)
        return pipeline_id

    def retrieve(self, pipeline_id: str) -> Dict:
        status = None
        url = None
        data = None

        while status != 'RESOLVED':
            record = self._long_tasks[pipeline_id]
            url, next_try = record
            now = datetime.now()
            if now < next_try:
                sleep((next_try - now).total_seconds())

            data = {'pipelineId': pipeline_id}
            response_json = self._post('/tasking/get-status', data)
            status = response_json['status']
            if status == 'FAILED':
                raise FailedTask
            if status != 'RESOLVED':
                record.next_try = datetime.now() + timedelta(seconds=int(response_json['nextTry']))

        return self._post(f'{url}/retrieve', data)
