import requests
import os
import json

class ImmichHandler:
    def __init__(self, base_url: str, api_token: str, verbose: bool = False):
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            'x-api-key': f'{self.api_token}',
            'Content-Type': 'application/json'
        }
        self.verbose = verbose
        if verbose: 
            print("Immich Handler initialized")

    def downloadById(self, id: str, path: str) -> bool:
        res = False
        filename = None
        endpoint = '/asset/download/' + id
        url = f'{self.base_url}{endpoint}'
        # print("Calling", url)

        response = requests.post(url, headers=self.headers)

        status_code = response.status_code
        # print(status_code)

        content_type = response.headers.get('content-type')
        filetype = content_type.split('/')[0]
        if filetype == "image":
            extension = content_type.split('/')[-1]
            filename = path + '.' + extension
            with open(filename, 'wb') as file:
                file.write(response.content)
                res = True

        # if status_code != 200:
        #     print("Unable to download  the image:", status_code)
        return res, status_code, filename

    def getAllAssetLocal(self):
        with open("library.json","r") as file:
            return json.load(file)

    def getAllAssets(self) -> dict:
        endpoint = '/asset'
        url = f'{self.base_url}{endpoint}'
        if self.verbose:
            print("Calling", url)

        response = requests.get(url, headers=self.headers)

        status_code = response.status_code
        if self.verbose:
            print(status_code)

        json_data = response.json()
        if self.verbose:
            print("Assets found:", len(json_data))

        return status_code, json_data

    def deleteAsset(self, ids: str):


        body = {
            "force": True,
            "ids": ids
        }

        endpoint = '/asset'
        url = f'{self.base_url}{endpoint}'
        # print("Calling", url, 'to delete asset', id)

        response = requests.delete(url, json=body, headers=self.headers)

        status_code = response.status_code
        # print('DELETION STATUS', status_code)

        return status_code
