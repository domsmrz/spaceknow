import argparse
import json
from spaceknow import spaceknow_api
from typing import Dict


DATASETS = [
    ('gbdx', ['idaho-pansharpened']),
]


def process_dataset(api: spaceknow_api.SpaceKnowApi, geometry: Dict, provider: str, dataset: str) -> None:
    extent = {
        'type': 'GeometryCollection',
        'geometries': [geometry],
    }
    input_data = {
        'provider': provider,
        'dataset': dataset,
        'startDatetime': '2018-01-01 00:00:00',
        'endDatetime': '2018-02-01 00:00:00',
        'extent': extent,
    }
    data = api.retrieve(api.initiate('/imagery/search', data=input_data))
    if data['cursor'] is not None:
        raise NotImplementedError("Cannot deal with paging yet")
    scene_ids = [x['sceneId'] for x in data['results']][:1]  # TODO: to make it faster
    imagery_pids, car_pids = (
        [api.initiate(f'/kraken/release/{map_type}/geojson', data={'sceneId': sid, 'extent': extent})
         for sid in scene_ids]
        for map_type in ('imagery', 'cars')
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-g', '--geometry', required=True)
    args = parser.parse_args()

    api = spaceknow_api.SpaceKnowApi(args.username, args.password)
    with open(args.geometry, 'r') as f:
        geometry = json.load(f)

    for provider, datasets in DATASETS:
        for dataset in datasets:
            process_dataset(api, geometry, provider, dataset)


if __name__ == '__main__':
    main()
