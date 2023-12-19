from DuplicateRemover import DuplicateRemover
from ImmichHandler import ImmichHandler
import sys 
import progressbar
import os
import json
import cv2
import numpy as np
from PIL import Image
from pillow_heif import register_heif_opener
import argparse

register_heif_opener()

def format_image(text):
    image = np.array(Image.open(text))

    image = image[:, :, ::-1].copy()

    h = int((660/image.shape[1])*image.shape[0])
    w = 640

    # font 
    font = cv2.FONT_HERSHEY_SIMPLEX 
    # org 
    org = (5, 30) 
    # fontScale 
    fontScale = 1
    # Blue color in BGR 
    color = (255, 0, 0) 
    thickness = 1
    
    image = cv2.resize(image, (w,h))
    image = cv2.putText(image, text,  org, font, fontScale, color, thickness, cv2.LINE_AA)
    return image

def main() -> int:

    already_done = {}

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='Immich duplicates detector')

    # Add three boolean arguments
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose')
    parser.add_argument('-d', '--dry-run', action='store_true', help="Only create the result file, don't run the deletion process")
    parser.add_argument('-l', '--delete-only', action='store_true', help='Only run the deletion process, from a already existing result file')
    parser.add_argument('-r', '--restart', action='store_true', help='Clear hashes cache')
    parser.add_argument('-s', '--similarity', type=int, help='Allowed similarity in %', default=95)

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the boolean arguments
    verbose = args.verbose
    enable_delete = not args.dry_run
    enable_detections = not args.delete_only
    restart = args.restart
    similarity = args.similarity

    temp_dir = "temporary_images"
    if not os.path.exists(temp_dir):
        # Create the directory
        os.makedirs(temp_dir)

    print("Parameters:")
    print(args)

    # exit(0)
    # try:
    #     with open("results.json", "r") as out_file:
    #         already_done = json.load(out_file)
    # except:
    #     print("No previous results to load")

    #api = ImmichHandler("https://miaoutch.ddns.net/api", "UNOtlJYWmQHGAxq2AQ0CIY0qnlUAubjSZdlSZ6xAZM")
    api = ImmichHandler("http://192.168.50.214:2283/api", "UNOtlJYWmQHGAxq2AQ0CIY0qnlUAubjSZdlSZ6xAZM", verbose=verbose)

    # dn = DuplicateNameDetector()
    dr = DuplicateRemover(similarity=similarity, restart=restart, verbose=verbose)

    if enable_detections:
        counter = 0
        response_code, assets = api.getAllAssets()
        # assets = api.getAllAssetLocal()
        bar = progressbar.ProgressBar(maxval=len(assets), widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.FormatLabel('Processed: %(value)d / ' + str(len(assets)) + ' lines (in: %(elapsed)s)')])
        bar.start()
        for asset in assets:
            counter = counter + 1
            bar.update(counter)
            id = asset["id"]
            filename = asset['originalFileName']

            if id in dr.getWorkingList():
                continue

            if verbose:
                print("Processing ID", id)


            status, response_code, image_path = api.downloadById(id, "./" + temp_dir + "/" + filename )
 
            res = False
            if status is not True:
                if verbose:
                    print(status, response_code, image_path, id, filename)
            else:
                res, compared_id = dr.find_duplicates_for_image(image_path, id)
                if res is False:
                    try:
                        os.remove(image_path)
                    except:
                        if verbose:
                            print("Unable to delete the image", image_path)
                else:
                    already_done[id] = compared_id
                    with open("results.json", "w") as out_file:
                        json.dump(already_done, out_file, indent=4)

        bar.finish()
        print("Results saved to results.json")

    if enable_delete:
        cv2.namedWindow("1")        # Create a named window
        cv2.moveWindow("1", 0,0)  # Move it to (0,0)
        cv2.namedWindow("2")        # Create a named window
        cv2.moveWindow("2", 640,0)  # Move it to (0,0)
        bar = progressbar.ProgressBar(maxval=len(already_done), widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
        bar.start()
        counter = 0
        for elem in already_done:
            counter = counter + 1
            bar.update(counter)
            status, response_code, image_path_1 = api.downloadById(elem, "./temporary_images/image1" )

            if status == False:
                continue

            status2, response_code, image_path_2 = api.downloadById(already_done[elem], "./temporary_images/image2" )
            
            if status2 == False:
                continue

            im1 = format_image(image_path_1)
            im2 = format_image(image_path_2)

            cv2.imshow("1", im1)
            cv2.imshow("2", im2)
            id_to_delete = -1
            while True:
                key = cv2.waitKey(0)
                if key == ord('s') or key == ord('S'):
                    exit(0)
                elif key == ord('1') or key == ord('&'):
                    id_to_delete = [elem]
                    break
                elif key == ord('2') or key == ord('é'):
                    id_to_delete = [already_done[elem]]
                    break
                elif key == ord('3') or key == ord('"'):
                    id_to_delete = [already_done[elem],elem]
                    break
                elif key == 27:  # Press Esc key to exit
                    break
            if id_to_delete != -1:
                api.deleteAsset(id_to_delete)
            cv2.destroyAllWindows()
        bar.finish()

    # Find Similar Images
    return 0

if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit