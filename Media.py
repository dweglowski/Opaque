import typing
import re
import os.path
import PIL.Image
import io
import random


class MediaController:
    """Used to access media files stored on the computer"""
    def __init__(self) -> None:
        self.__PROFILE_PICTURES_FOLDER : str = "MediaStorage/Images/ProfilePictures/Unencrypted/"

 
    def __sanitize_uuid(self, uuid : str) -> str:
        """Ensures a uuid is made purely of numeric chars, prevents attacks such as path traversal."""
        return re.sub("[^0-9]*","",uuid)

    def __profile_picture_exists(self, uuid : str) -> bool:
        return os.path.isfile(self.__PROFILE_PICTURES_FOLDER + uuid + ".png")

    def get_profile_picture(self, uuid : str) -> bytes:
        """Returns a profile picture matching a specific uuid."""
        uuid = self.__sanitize_uuid(uuid)

        if not self.__profile_picture_exists(uuid):
            return bytes()

        file_data : bytes
        with open(self.__PROFILE_PICTURES_FOLDER + uuid + ".png", "rb") as f:
            file_data = f.read()


        return file_data

    def __generate_uuid_profile_picture(self) -> str:
        """Generates a random uuid for profile picture."""

        while True:
            uuid : str = str(random.randint(1000000000000,10000000000000-1))

            if not self.__profile_picture_exists(uuid):
                return uuid     

    
    def upload_profile_picture(self, raw_data : bytes) -> str:
        """Saves a new profile picture under a random uuid, makes sure the picture fits specific criteria first to prevent attacks through file upload"""
        
        # Check if the file is too large, 200x200 png should fit in this size
        MAX_SIZE = 1 * 1024 * 1024
        if len(raw_data) > MAX_SIZE:
            return ""
        
        img : PIL.Image.Image = PIL.Image.open(io.BytesIO(raw_data))

        # Check if the image is a png, if not, abort
        if img.format != "PNG":
            return ""
        
        # create a new png without all the metadata (prevent sharing info such as location taken)
        sanitized_image : PIL.Image.Image = PIL.Image.new(img.mode, img.size)
        sanitized_image.putdata(list(img.getdata()))


        sanitized_image_data : io.BytesIO = io.BytesIO()
        sanitized_image.save(sanitized_image_data, format='png', optimize=True)

        uuid : str = self.__generate_uuid_profile_picture()
        with open(self.__PROFILE_PICTURES_FOLDER + uuid + ".png", "wb") as f:
            f.write(sanitized_image_data.getvalue())

        return uuid
