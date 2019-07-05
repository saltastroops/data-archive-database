import os
from PIL import Image
from astropy.io import fits
from astropy.io.fits import ImageHDU
from typing import List, Tuple

from ssda.instrument.instrument_fits_data import DataPreviewType

MAX_WIDTH = 500
TARGET_HEIGHT = 500  # Base height for all thumbnail


def get_thumbnail_size(original_size: Tuple[float, float]):
    """
    Calculate the thumbnail dimensions for given original image dimensions.

    Parameters
    ----------
    original_size : Tuple[float, float]
        Pair of width and height of the original image.

    Returns
    -------
    thumbnail : Tuple[float, float]
        Width and height of the thumbnail.

    """

    factor = original_size[1] / TARGET_HEIGHT
    thumbnail_size = original_size[0] / factor, original_size[1] / factor

    if thumbnail_size[0] > MAX_WIDTH:
        max_width_factor = thumbnail_size[0] / MAX_WIDTH
        thumbnail_size = (thumbnail_size[0] / max_width_factor, thumbnail_size[1] / max_width_factor)

    return thumbnail_size


def save_image_data(fits_file: str, save_dir: str) -> List[Tuple[str, DataPreviewType]]:
    """
    Crete the thumbnail images for a FITS file.

    Existing files will be overwritten.

    Parameters
    ----------
    fits_file : str
        File path of the FITS file.
    save_dir : str
        Directory where to save the images.

    """

    # Get the file name without extension
    basename = os.path.basename(fits_file).split(".")[0]
    created_images = []

    # Create the directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Read in the images, rescale them and save them
    with fits.open(fits_file) as hdul:
        for index, image in enumerate(hdul):
            if isinstance(image, ImageHDU):
                # Convert FITS data to a Pillow object
                im = Image.fromarray(image.data.astype('uint8'))

                # Rescale the image to thumbnail size
                original_width, original_height = image.data.shape[1], image.data.shape[0]
                im.thumbnail(get_thumbnail_size((original_width, original_height)))

                # Save the thumbnail
                image_save_path = os.path.join(
                    save_dir, "{basename}-image-{order}.png".format(basename=basename, order=index)
                )
                im.save(image_save_path)

                # Record the created thumbnail
                created_images.append((image_save_path, DataPreviewType.IMAGE))

    return created_images
