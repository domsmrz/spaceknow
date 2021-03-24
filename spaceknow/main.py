import argparse
import json
import io
import PIL.Image
import PIL.ImageDraw
from typing import Dict
import requests
import math

from spaceknow import spaceknow_api


DATASETS = [
    ('gbdx', ['idaho-pansharpened', 'idaho-swir']),
    ('iceye', ['Spotlight_SLC'])
]


def draw_geometry(draw: PIL.ImageDraw, geometry: Dict, bands):
    if geometry['type'] != 'Polygon':
        raise NotImplementedError("Drawing non-polygon geometries is not implemented yet")

    selected_band = bands[0]  # FIXME: I not sure if taking the first band is the right way to go

    image_coordinates = [
        (
            math.floor((xc - selected_band['crsOriginX']) / selected_band['pixelSizeX']),
            math.floor((yc - selected_band['crsOriginY']) / selected_band['pixelSizeY']),
        )
        for xc, yc in geometry['coordinates'][0][:-1]
    ]
    draw.polygon(image_coordinates, fill="#ff0000")


def analyse(api: spaceknow_api.SpaceKnowApi, imagery_data, car_data, bands):
    if set(map(tuple, imagery_data['tiles'])) != set(map(tuple, car_data['tiles'])):
        raise RuntimeError("Non-matching set of tiles for imagery and car analysis")

    tiles = imagery_data['tiles']
    if len({z for z, _, _ in tiles}) != 1:
        raise RuntimeError("Distinct zoom levels in one scene")

    min_x = min(x for _, x, _ in tiles)
    min_y = min(y for _, _, y in tiles)
    max_x = max(x for _, x, _ in tiles)
    max_y = max(y for _, _, y in tiles)

    images = list()
    width, height = None, None
    total_cars = 0
    for z, x, y in tiles:
        image = PIL.Image.open(io.BytesIO(api.get(f'/kraken/grid/{imagery_data["mapId"]}/-/{z}/{x}/{y}/truecolor.png')))
        draw = PIL.ImageDraw.Draw(image)

        tile_car_data = json.loads(api.get(f'/kraken/grid/{car_data["mapId"]}/-/{z}/{x}/{y}/detections.geojson'))
        if tile_car_data['type'] != 'FeatureCollection':
            raise RuntimeError(f"Unknown data type {tile_car_data['type']!r}")

        total_cars += len(tile_car_data['features'])
        for single_car in tile_car_data['features']:
            draw_geometry(draw, single_car['geometry'], bands)

        images.append((image, x - min_x, y - min_y))
        width, height = image.width, image.height

    final_image = PIL.Image.new('RGBA', (width * (max_x - min_x + 1), height * (max_y - min_y + 1)))
    for image, x, y in images:
        final_image.paste(image, (x * width, y * height))

    return final_image, total_cars


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
    data_results = data['results']
    scene_ids = [x['sceneId'] for x in data_results]
    bands = [x['bands'] for x in data_results]
    imagery_pids, car_pids = (
        [api.initiate(f'/kraken/release/{map_type}/geojson', data={'sceneId': sid, 'extent': extent})
         for sid in scene_ids]
        for map_type in ('imagery', 'cars')
    )
    for i, (imagery_pid, car_pid, item_bands) in enumerate(zip(imagery_pids, car_pids, bands)):
        imagery_data = api.retrieve(imagery_pid)
        car_data = api.retrieve(car_pid)
        image, cars = analyse(api, imagery_data, car_data, item_bands)
        print(f"Number of cars in {provider}/{dataset}/{i} is {cars}")
        image.show()


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
