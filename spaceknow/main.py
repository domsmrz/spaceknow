import requests
import json
from spaceknow import spaceknow_api

BASE_URL = 'https://api.spaceknow.com/'
USERNAME = ''
PASSWORD = ''

AIRPORT = [
    [153.1036689, -27.3925325],
    [153.1064317, -27.3880647],
    [153.1085719, -27.3894936],
    [153.1066033, -27.3912989],
    [153.1052997, -27.3933661],
    [153.1036689, -27.3925325],
]

input_data = {
    'provider': 'gbdx',
    'dataset': 'idaho-pansharpened',
    'startDatetime': '2018-01-01 00:00:00',
    'endDatetime': '2018-02-01 00:00:00',
    'extent': {
        'type': 'GeometryCollection',
        'geometries': [
            {
                'type': 'Polygon',
                'coordinates': [AIRPORT],
            },
        ],
    },
}

api = spaceknow_api.SpaceKnowApi(USERNAME, PASSWORD)
pid = api.initiate('/imagery/search', data=input_data)
data = api.retrieve(pid)
# response = requests.post(f'{BASE_URL}imagery/search/initiate', headers=headers, data=json.dumps(data))
