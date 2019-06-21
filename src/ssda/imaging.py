import os
from PIL import Image
from astropy.io import fits
from astropy.io.fits import ImageHDU

BASE_HEIGHT = 644  # Base height for all thumbnail


def get_thumbnail_size(size):
    """
    Create a thumbnail size with a width of BASE_HEIGHT
    :param size: Image size (tuple of width by height (w,h,))
    :return: width and height of the thumbnail
    """
    factor = size[1]/BASE_HEIGHT
    return size[1]/factor, size[0]/factor


def save_image_data(image_path, save_path):
    """
    It creates and save the image and the thumpnail of the image.
    If the same filename is opened from the the same telescope the image will be over written
    :param image_path:
        Path of fits file to save image of
    :param save_path:
        Telescope name the file is from.
            To separate the files by telescope used. this will guarantee that files are not over written since
            telescopes saves files differently.
    :return: Image path and Thumbnail path
    """

    basename = image_path.split("/")[-1].split(".")[0]  # get a file name without an extension
    created_images = []

    # creating a directory if it doesn't exist
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    with fits.open(image_path) as hdul:
        for index, image in enumerate(hdul):
            if isinstance(image, ImageHDU):
                im = Image.fromarray(image.data.astype('uint8'))  # Image creation
                image_saved_path = os.path.join(
                    save_path, "{basename}-image-{order}.png".format(basename=basename, order=index)
                )
                im.thumbnail(get_thumbnail_size(image.data.shape))  # getting a thumbnail scale see BASE_HEIGHT
                # save a thumbnail
                im.save(image_saved_path)
                created_images.append(image_saved_path)

    return created_images
