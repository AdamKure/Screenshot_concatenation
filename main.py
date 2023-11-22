from PIL import Image

def find_overlap(img_1, img_2):
    # Determines the height of the compared are from both pictures
    overlap_area_height = img_2.height*0.75

    # Set the number of pixels to compare for overlap (x, y)
    overlap_threshold = (min(img_1.width, img_2.width), 500)

    # Get the bottom strip of pixels from the first image
    bottom_strip = img_1.crop((0, img_1.height*0.5, img_1.width, img_1.height))

    # Get the top strip of pixels from the second image
    top_strip = img_2.crop((0, 0, img_2.width, overlap_area_height))

    # Compare the two strips pixel by pixel
    for y_bot in range(bottom_strip.height-overlap_threshold[1], -1, -5):
        for y_top in range(bottom_strip.height-overlap_threshold[1], -1, -1):
            pixel_1 = bottom_strip.getpixel((150, y_bot))
            pixel_2 = top_strip.getpixel((150, y_top))
            if pixel_1 != pixel_2:
                continue
            flag = False
            for x in range(0, overlap_threshold[0], 15):
                for y in range(0, overlap_threshold[1], 15):
                    pixel_3 = bottom_strip.getpixel((x, y+y_bot))
                    pixel_4 = top_strip.getpixel((x, y+y_top))
                    if pixel_3 != pixel_4:
                        flag = True
                        break
                if flag:
                    break
            else:
                return (bottom_strip.height-y_bot, y_top)  # Return the y-coordinate where the images start to differ
    return (0, 0)  # If no difference is found, return 0

def concatenate_screenshots(image1_path, image2_path, output_path):
    # Open the images
    img1 = Image.open(image1_path)
    img2 = Image.open(image2_path)

    # Find the overlapping region
    overlap = find_overlap(img1, img2)
    print(overlap)
    overlap_total = overlap[0] + overlap[1]

    # Determine the size of the concatenated image
    new_width = max(img1.width, img2.width)
    new_height = img1.height + img2.height - overlap_total

    # Create a new image with the determined size and a white background
    new_image = Image.new("RGB", (new_width, new_height), "white")

    # Paste the first image at the top
    new_image.paste(img1.crop((0, 0, img1.width, img1.height-overlap[0])), (0, 0))

    # Paste the second image below the first one, excluding the overlapping region
    new_image.paste(img2.crop((0, overlap[1], img2.width, img2.height)), (0, img1.height-overlap[0]))

    # Save the result
    # new_image.save(output_path)
    new_image.show()

if __name__ == "__main__":
    image1_path = "signal-2023-11-20-131643.png"
    image2_path = "signal-2023-11-20-131643-1.png"
    output_path = "new_img_1.png"

    concatenate_screenshots(image1_path, image2_path, output_path)
