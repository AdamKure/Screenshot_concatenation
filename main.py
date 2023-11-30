import configparser
import os
import time
from datetime import datetime, timedelta
from PIL import Image
from PIL.ExifTags import TAGS

def print_readable_exif_data(image):
    exif_data = get_readable_exif_data(image)
    if exif_data:
        for key in exif_data.keys():
            print(f"{key}: {exif_data[key]}")
    else:
        print("No exif data found\n")


def get_readable_exif_data(image):
    exif_data = image._getexif()
    if exif_data is not None:
        # Convert the raw EXIF data to a more readable format
        exif_data = {TAGS[key]: exif_data[key] for key in exif_data.keys() if key in TAGS and TAGS[key] != "MakerNote"}
        return exif_data
    else:
        print("No EXIF data found.")
        return None


def find_overlap(img1, img2):
    # Determines the height of the compared are from both pictures
    overlap_area_height = img2.height*0.75

    # Set the number of pixels to compare for overlap (x, y)
    overlap_threshold = (min(img1.width, img2.width), 400)

    # Get the bottom strip of pixels from the first image
    bottom_strip = img1.crop((0, img1.height*0.5, img1.width, img1.height))

    # Get the top strip of pixels from the second image
    top_strip = img2.crop((0, 0, img2.width, overlap_area_height))

    # Compare the two strips pixel by pixel
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
                return (bottom_strip.height-y_bot, y_top)  # Return offset in y-axis
    return (0, 0)  # If no match is found, return 0


def stich_screenshots(img1, img2):    
    # Find the overlapping region
    overlap = find_overlap(img1, img2)
    overlap_total = overlap[0] + overlap[1]

    # Determine the size of the concatenated image
    new_width = max(img1.width, img2.width)
    new_height = img1.height + img2.height - overlap_total

    # Create a new image with the determined size and a white background
    new_img = Image.new("RGB", (new_width, new_height), "white")

    # Paste the first image at the top
    new_img.paste(img1.crop((0, 0, img1.width, img1.height-overlap[0])), (0, 0))

    # Paste the second image below the first one, excluding the overlapping region
    new_img.paste(img2.crop((0, overlap[1], img2.width, img2.height)), (0, img1.height-overlap[0]))

    return new_img


def get_average_datetime(datetime1, datetime2):
    # Convert strings to datetime objects
    dt1 = datetime.strptime(datetime1, "%Y:%m:%d %H:%M:%S")
    dt2 = datetime.strptime(datetime2, "%Y:%m:%d %H:%M:%S")

    # Calculate the difference between datetime objects
    time_difference = dt2 - dt1

    # Calculate the midpoint
    midpoint = dt1 + time_difference / 2

    # Format the result as a string
    avg_datetime_str = midpoint.strftime('%Y-%m-%d-%H%M%S')
    
    return avg_datetime_str


def get_image_timestamp(exif_data):
    if 36867 in exif_data:
        return exif_data[36867]  # DateTimeOriginal field
    else:
        return None


def check_if_reversed_time(datetime1, datetime2):
    # Check if they need to be switched
    if datetime1 is not None and datetime2 is not None:
        if datetime1 > datetime2:
            return True
        else:
            return False
    else:
        return None


def sort_by_time(img1, img2):
    # Get exif data from images
    exif_data1 = img1._getexif()
    exif_data2 = img2._getexif()

    if not exif_data1 or not exif_data2:
        return img1, img2

    # Get datetime from exif
    time1 = get_image_timestamp(exif_data1)
    time2 = get_image_timestamp(exif_data2)

    return check_if_reversed_time(time1, time2)


def update_timestamp(exif_data, datetime):
    for tag, value in exif_data.items():
        if TAGS.get(tag) == 'DateTimeOriginal':
            exif_data[tag] = datetime
    return exif_data


def create_new_image(image1, image2, output_folder_path=None, custom_name=None, image_file_format=".png", spam=False):
    # Get images in correct order
    is_reversed = sort_by_time(image1, image2)

    # Get concatenated image
    if is_reversed:
        new_image = stich_screenshots(image2, image1)
    else:
        new_image = stich_screenshots(image1, image2)

    # Get the date and time from the metadata
    datetime1 = image1._getexif()[36867]
    datetime2 = image2._getexif()[36867]

    # Calculate the average date and time
    if datetime1 and datetime2:
        avg_datetime = get_average_datetime(datetime1, datetime2)

    # Create name for new image
    if avg_datetime and not custom_name:
        filename = f"{avg_datetime}{image_file_format}"
    elif custom_name:
        filename = f"{custom_name}{image_file_format}"
    else:
        filename = f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}{image_file_format}"

    # Add folder path
    if output_folder_path:
        full_path = os.path.join(output_folder_path, filename)
    else:
        full_path = filename

    # Save the result
    new_image.save(full_path)

    # Free up memory (memory)
    image1.close()
    image2.close()
    new_image.close()

    if spam:
        print(f"Image {filename} created")


def display_files_in_folder(folder_path):
    # Check if the folder exists
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


def filter_images_in_folder(folder_path):
    image_extensions = ['.png', '.jpg', '.jpeg']
    image_path_list = []
    files = os.listdir(folder_path)
    for file in files:
        _, extension = os.path.splitext(file)
        if extension.lower() in image_extensions:
            image_path_list.append(os.path.join(folder_path, file)) 
    return image_path_list


def within_15_minutes(timestamp1, timestamp2):
    time_format = "%Y:%m:%d %H:%M:%S"
    time1 = datetime.strptime(timestamp1, time_format)
    time2 = datetime.strptime(timestamp2, time_format)
    time_difference = abs(time1 - time2)
    return time_difference <= timedelta(minutes=15)


def create_image_pairs(image_paths, spam=False):
    # Open all images in a batch
    images = [Image.open(image_path) for image_path in image_paths]

    # Extract EXIF data for all images
    exif_data_list = [img._getexif() for img in images]

    # Process the EXIF data
    datetimes = []
    for exif_data in exif_data_list:
        if exif_data:
            datetime = get_image_timestamp(exif_data)
        else:
            datetime = None
        datetimes.append(datetime)

    image_pair_list = []
    omited_list = []
    paired = []
    for index1, datetime1 in enumerate(datetimes[:-1]):
        if (not datetime1):
            omited_list.append(image_paths[index1])
            continue
        if (index1 in paired):
            continue
        for index2, datetime2 in enumerate(datetimes[index1+1:], start=index1+1):
            if (not datetime2) or (index2 in paired):
                continue
            if index2 > index1 and within_15_minutes(datetime1, datetime2):
                image_pair_list.append((images[index1], images[index2]))
                paired.extend([index1, index2])
                break
        else:
            omited_list.append(image_paths[index1])

    if spam:
        print("Found", len(image_pair_list), "pairs")
        print("Pictures omited:", len(omited_list))

    return omited_list, image_pair_list


def list_to_txt(input_list, output_file):
    with open(output_file, 'w') as file:
        for item in input_list:
            file.write(str(item) + '\n')


def main():
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    input_folder_path = conf.get("Paths", "input_folder_path")
    output_folder_path = conf.get("Paths", "output_folder_path")
    print(f"Loading files from {input_folder_path}")

    # display_files_in_folder(rf"{input_folder_path}")
    images_path_list = filter_images_in_folder(rf"{input_folder_path}")
    print(f"Found {len(images_path_list)} images")
    omited, image_pair_list = create_image_pairs(images_path_list, spam=True)
    list_to_txt(omited, f"{output_folder_path}\Omited_files.txt")

    print("Stiching images:")
    for pair in image_pair_list:
        create_new_image(pair[0], pair[1], output_folder_path=output_folder_path, spam=True)


if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()
    run_time = end_time - start_time
    print("Completed in:", run_time)
