from PIL import Image
import imagehash
import os
import numpy as np
from pillow_heif import register_heif_opener # for HEIC file
import json

class ImmichImage:
    def __init__(self, id: str):
        self.id = id

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    temp_path: str
    computed_hash: str
    id: str

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ImmichImage):
            return obj.toJson()
        return super().default(obj)

class DuplicateRemover:
    def __init__(self,hash_size = 20, similarity = 95, restart=True, verbose=False):
        self.immich_images_list = {}
        self.hash_size = hash_size
        self.threshold = 1 - similarity/100
        self.diff_limit = int(self.threshold*(self.hash_size**2))
        self.verbose = verbose
        
        if verbose:
            print('Diff limit will be', self.diff_limit)
        
        register_heif_opener()
        if not restart:
            self.reload_previous_hashes()

    def getWorkingList(self):
        return self.immich_images_list

    def reload_previous_hashes(self):
        try:
            f = open('data.json')
            data = json.load(f)
        except:
            print("Unable to load the saved file data.json.")
        try:
            for elem in data:
                ii = ImmichImage(elem)
                jelem = json.loads(data[elem])
                ii.computed_hash =jelem['computed_hash']
                ii.temp_path =jelem['temp_path']
                self.immich_images_list[elem] = ii
            print('Loading:', len( self.immich_images_list), 'retrieved')
        except:
            print("Unable to get the right data from the saved file data.json.")

    def find_duplicates_for_image(self, path: str, id: str) -> bool:
        dupl = False
        compared_id = -1
        ii = ImmichImage(id)

        try:
            with Image.open(path) as img:
                ii.temp_path = path
                this_hash = imagehash.phash(img, self.hash_size)
        except:
            print("Image loading error.")
            return dupl, -1

        ii.computed_hash = str(this_hash)

        if len(self.immich_images_list) > 0:

            # Define the lambda function for processing each element
            process_elem = lambda elem: (
                elem,
                imagehash.hex_to_hash(self.immich_images_list[elem].computed_hash) - this_hash
            )

            # Use map() to process each element in parallel
            result = map(process_elem, self.immich_images_list)

            use_next = False

            if use_next:
                # Find the first element that satisfies the condition
                found_elem = next((elem for elem, diff in list(result) if diff <= self.diff_limit), None)

                if found_elem is not None:
                    # print(found_elem)
                    # print("Duplicate {} found for Image {}!".format(path, self.immich_images_list[found_elem].temp_path))
                    # print(hs, '-- VS --', this_hash)
                    dupl = True
                    compared_id = found_elem
            
            else:
                # old fashion method
                for elem, diff in result:
                    if diff <= self.diff_limit:
                        print("Duplicate diff {} {} found for Image {}!".format(diff, path, self.immich_images_list[elem].temp_path))
                        # print(hs, '-- VS --', this_hash)
                        dupl = True
                        compared_id = elem
                        break

        self.immich_images_list[id] = ii

        with open("data.json", "w") as out_file:
            json.dump(self.immich_images_list, out_file, cls=MyEncoder, indent=4)

        return dupl, compared_id
