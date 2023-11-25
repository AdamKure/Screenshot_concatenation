from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

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
                for y in range(0, overlap_threshold[1], 10):
                    pixel3 = bottom_strip.getpixel((x, y+y_bot))
                    pixel4 = top_strip.getpixel((x, y+y_top))
                    if pixel3 != pixel4:
                        flag = True
                        break
                if flag:
                    break
            else:
                return (bottom_strip.height-y_bot, y_top)  # Return the y-coordinate where the images start to differ
    return (0, 0)  # If no difference is found, return 0

def concatenate_screenshots(img1, img2):    
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
    avg_datetime_str = midpoint.strftime("%Y:%m:%d %H:%M:%S")

    return avg_datetime_str

"""
def get_readable_exif_data(image_path):
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data is not None:
                # Convert the raw EXIF data to a more readable format
                exif_data = {TAGS[key]: exif_data[key] for key in exif_data.keys() if key in TAGS and TAGS[key] != "MakerNote"}
                return exif_data
            else:
                print("No EXIF data found.")
    except Exception as e:
        print(f"Error: {e}")
"""

def get_image_timestamp(exif_data):
    if 36867 in exif_data:
        return exif_data[36867]  # DateTimeOriginal field
    else:
        return None

def check_if_reversed_time(datetime1, datetime2):
    if datetime1 is not None and datetime2 is not None:
        # Check if they need to be switched
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

    # Check if they need to be switched and switch
    if check_if_reversed_time(time1, time2):
        return img2, img1
    return img1, img2

def update_timestamp(exif_data, datetime):
    for tag, value in exif_data.items():
        if TAGS.get(tag) == 'DateTimeOriginal':
            exif_data[tag] = datetime

    return exif_data

def create_new_image(image1_path, image2_path, output_path):
    # Open images from a given path
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    # Get images in correct order
    img1, img2 = sort_by_time(image1, image2)

    # Get concatenated image
    new_img = concatenate_screenshots(img1, img2)

    try:
        # Get the date and time from the metadata
        datetime1 = img1._getexif()[36867]
        datetime2 = img2._getexif()[36867]

        # Copy exif from image 1
        new_exif = img1._getexif()

        # Calculate the average date and time
        if datetime1 and datetime2:
            avg_datetime = get_average_datetime(datetime1, datetime2)
            # new_exif[36867] = avg_datetime

        # Change exif data
        new_exif = update_timestamp(new_exif, avg_datetime)
        # print(new_exif)

        # Save the result with the averaged metadata, so far JPEG and TIFF, NO PNG
        # new_img.save(output_path, exif=exif_bytes)
        print("Finished")
    except Exception as e:
        new_img.save(output_path)
        print(f"Error changing exif: {e}")
    finally:
        new_img.show()

if __name__ == "__main__":
    # image1_path = "signal-2023-11-20-131643.PNG"
    # image2_path = "signal-2023-11-20-131643-1.PNG"

    # image1_path = "signal-2023-11-20-131643-3.PNG"
    # image2_path = "signal-2023-11-20-131643-2.PNG"

    image1_path = "IMG_6659.PNG"
    image2_path = "IMG_6660.PNG"
    output_path = "new_img.png"

    create_new_image(image1_path, image2_path, output_path)
    
    # print(Image.open(output_path)._getexif())
    # print(Image.open(output_path).info.get("exif", "b"))
    # print(Image.open(image1_path)._getexif())
    # print(Image.open(image1_path).info.get("exif", "b"))
