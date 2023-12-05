import configparser
import os
import time
from datetime import datetime, timedelta
from multiprocessing import Pool
from PIL import Image
from PIL.ExifTags import TAGS
from typing import Dict, List, Tuple, Union

def check_if_reversed_time(datetime1: str, datetime2: str) -> bool:
    """Returns True if datetime2 is older than datetime1"""
    if datetime1 is not None and datetime2 is not None:
        if datetime1 > datetime2:
            return True
        else:
            return False
    else:
        return None


def create_image_pairs(image_path_list: List[str], spam: bool=False) -> Tuple[List[str], List[Tuple[str]]]:
    """
    Returns list of pictures that were not paired and list of tuples with images paired together for stiching.
    """
    datetime_list = []
    for image_path in image_path_list:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data:
                datetime = get_image_timestamp(exif_data)
            else:
                datetime = None
            datetime_list.append(datetime)

    image_pair_list = []
    omited_list = []
    is_paired = []
    for index1, datetime1 in enumerate(datetime_list[:-1]):
        if not datetime1:
            omited_list.append(image_path_list[index1])
            continue
        if index1 in is_paired:
            continue
        for index2, datetime2 in enumerate(datetime_list[index1+1:], start=index1+1):
            if (not datetime2) or (index2 in is_paired):
                continue
            if index2 > index1 and within_15_minutes(datetime1, datetime2):
                image_pair_list.append((image_path_list[index1], image_path_list[index2]))
                is_paired.extend([index1, index2])
                break
        else:
            omited_list.append(image_path_list[index1])

    if spam:
        print("Found", len(image_pair_list), "pairs")
        print("Pictures omited:", len(omited_list))

    return omited_list, image_pair_list


def create_new_image(image1: Image, image2: Image, output_folder_path: str=None, custom_name: str=None, image_file_format: str=".png", print_enabled: bool=False):
    """
    Creates new image by stiching passed images. Image name, extention are cuntomizable
    By default image will be named by its origin datetime and it will be ".png" file
    """
    is_reversed = sort_by_time(image1, image2)
    if is_reversed:
        new_image = stich_screenshots(image2, image1)
    else:
        new_image = stich_screenshots(image1, image2)

    datetime1 = image1._getexif().get(36867)
    datetime2 = image2._getexif().get(36867)
    if datetime1 and datetime2:
        avg_datetime = get_average_datetime(datetime1, datetime2)

    if custom_name:
        filename = f"{custom_name}{image_file_format}"
    elif avg_datetime:
        filename = f"{avg_datetime}{image_file_format}"
    else:
        filename = f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}{image_file_format}"

    if output_folder_path:
        full_path = os.path.join(output_folder_path, filename)
    else:
        full_path = filename

    # new_image.save(full_path)
    new_image.close()

    if print_enabled:
        print(f"Image {filename} created")


def display_files_in_folder(folder_path: str):
    """ Displays all the files in a given folder """
    if not os.path.exists(folder_path):
        print(f"The folder '{folder_path}' does not exist.")
        return

    # Get the list of files in the folder
    files = os.listdir(folder_path)

    # Display the list of files
    print(f"Files in the folder '{folder_path}':")
    for file in files:
        file_path = os.path.join(folder_path, file)
        print(file_path)


def filter_images_in_folder(folder_path: str) -> List[str]:
    """ Returns list of all the files with specific extensions in passed folder"""
    image_extensions = ['.png', '.jpg', '.jpeg']
    image_path_list = []
    files = os.listdir(folder_path)
    for file in files:
        _, extension = os.path.splitext(file)
        if extension.lower() in image_extensions:
            image_path_list.append(os.path.join(folder_path, file)) 
    return image_path_list


def get_readable_exif_data(image: Image) -> Union[Dict[str, Union[str, int, bytes]], None]:
    """
    Extracts and returns human-readable Exif data from the given image.
    """
    exif_data = image._getexif()
    if exif_data:
        exif_data = {TAGS[key]: exif_data[key] for key in exif_data.keys() \
            if key in TAGS and TAGS[key] != "MakerNote"}
        return exif_data
    else:
        print("No EXIF data found.")
        return None


def find_overlap(image1: Image, image2: Image) -> Tuple[int]:
    """
    Compares pixels in passed images to calculate offsets in y-axis at which pictures starts to overlap.
    If no match is found returns (0, 0)
    """
    overlap_searched_area_height = image2.height*0.75
    overlap_threshold = (min(image1.width, image2.width), 400)

    bottom_strip = image1.crop((0, image1.height*0.5, image1.width, image1.height))
    top_strip = image2.crop((0, 0, image2.width, overlap_searched_area_height))

    # Room for readability improvement
    for y_bot in range(bottom_strip.height-overlap_threshold[1], -1, -10):
        for y_top in range(bottom_strip.height-overlap_threshold[1], -1, -1):
            pixel1 = bottom_strip.getpixel((150, y_bot))
            pixel2 = top_strip.getpixel((150, y_top))
            if pixel1 != pixel2:
                continue
            flag = False
            for x in range(0, overlap_threshold[0], 25):
                for y in range(0, overlap_threshold[1], 25):
                    pixel3 = bottom_strip.getpixel((x, y+y_bot))
                    pixel4 = top_strip.getpixel((x, y+y_top))
                    if pixel3 != pixel4:
                        flag = True
                        break
                if flag:
                    break
            else:
                return (bottom_strip.height-y_bot, y_top)
    return (0, 0)


def get_average_datetime(datetime1: str, datetime2: str) -> str:
    """
    Returns midpoints between 2 datetimes.
    """
    dt1 = datetime.strptime(datetime1, "%Y:%m:%d %H:%M:%S")
    dt2 = datetime.strptime(datetime2, "%Y:%m:%d %H:%M:%S")

    time_difference = dt2 - dt1
    midpoint = dt1 + time_difference / 2
    return midpoint.strftime('%Y-%m-%d-%H%M%S')


def get_image_timestamp(exif_data: Dict) -> Union[str, None]:
    """
    Returns a DatetimeOrigin from exif.
    If none if found returns None
    """
    return exif_data.get(36867)


def list_to_txt(input_list: List[str], output_file: str):
    """ Writes paths of files that were not paired into a file """
    with open(output_file, 'w') as file:
        for item in input_list:
            file.write(str(item) + '\n')


def print_readable_exif_data(image_path: str):
    '''
    Print human readable exif data of a given image file to a console.
    '''
    with Image.open(image_path) as img:
        exif_data = get_readable_exif_data(img)
        if exif_data:
            for key in exif_data.keys():
                print(f"{key}: {exif_data[key]}")
        else:
            print("No exif data found\n")


def process_image_pair(arg_tupple: Tuple[Tuple[str], str]):
    """ Unpacking args after multiproceesing """
    image_pair, output_folder_path = arg_tupple
    with Image.open(image_pair[0]) as image1, Image.open(image_pair[1]) as image2:
        create_new_image(image1, image2, output_folder_path=output_folder_path, print_enabled=True)


def sort_by_time(image1: Image, image2: Image) -> bool:
    "Returns True if image2 has older dated than image1"
    exif_data1 = image1._getexif()
    exif_data2 = image2._getexif()
    if not exif_data1 or not exif_data2:
        return False

    time1 = get_image_timestamp(exif_data1)
    time2 = get_image_timestamp(exif_data2)
    return check_if_reversed_time(time1, time2)


def stich_screenshots(image1: Image, image2: Image) -> Image:
    """
    Returns an image cretaed by stiching the 2 passed images.
    If it finds overlaping regions it will remove duplicate areas.
    """
    overlap = find_overlap(image1, image2)
    overlap_total = overlap[0] + overlap[1]

    new_width = max(image1.width, image2.width)
    new_height = image1.height + image2.height - overlap_total

    new_image = Image.new("RGB", (new_width, new_height), "white")
    new_image.paste(image1.crop((0, 0, image1.width, image1.height-overlap[0])), (0, 0))
    new_image.paste(image2.crop((0, overlap[1], image2.width, image2.height)), (0, image1.height-overlap[0]))
    return new_image


def update_timestamp(exif_data: Dict, datetime: str) -> Dict:
    """Returns exif data with updated DatetimeOriginal"""
    for tag, value in exif_data.items():
        if TAGS.get(tag) == 'DateTimeOriginal':
            exif_data[tag] = datetime
    return exif_data


def within_15_minutes(timestamp1: str, timestamp2: str) -> bool:
    """ Returns True if passed datetimes are within 15 of each other """
    time_format = "%Y:%m:%d %H:%M:%S"
    time1 = datetime.strptime(timestamp1, time_format)
    time2 = datetime.strptime(timestamp2, time_format)
    time_difference = abs(time1 - time2)
    return time_difference <= timedelta(minutes=15)


if __name__ == "__main__":
    start_time = time.perf_counter()

    conf = configparser.ConfigParser()
    conf.read('config.ini')
    input_folder_path = conf.get("Paths", "input_folder_path")
    output_folder_path = conf.get("Paths", "output_folder_path")
    print(f"Loading files from {input_folder_path}")

    # display_files_in_folder(rf"{input_folder_path}")
    images_path_list = filter_images_in_folder(rf"{input_folder_path}")
    print(f"Found {len(images_path_list)} images")
    omited, image_pair_list = create_image_pairs(images_path_list, spam=True)
    # list_to_txt(omited, f"{output_folder_path}\Omited_files.txt")

    print("Stiching images:")
    arg_list = [(path, output_folder_path) for path in image_pair_list]  # added late for multiprocessing compatibility
    with Pool() as pool:
        results = pool.imap_unordered(process_image_pair, arg_list)
        for _ in results:
            continue
    end_time = time.perf_counter()
    run_time = end_time - start_time
    print("Total time of completion:", run_time, "s total.")
