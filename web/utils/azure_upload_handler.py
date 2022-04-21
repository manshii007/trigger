from django.core.files.uploadhandler import FileUploadHandler
import sys
from io import StringIO
import uuid
from storages.utils import setting
from .unique_filename import unique_upload
from azure.storage.blob import BlockBlobService
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.core.files.storage import DefaultStorage
import logging
import os


logger = logging.getLogger('debug')


def clean_name(name):
    return os.path.normpath(name).replace("\\", "/")


class AzureFileUploadHandler(FileUploadHandler):
    max_chunk_size = BlockBlobService.MAX_BLOCK_SIZE
    account_name = setting("AZURE_ACCOUNT_NAME")
    account_key = setting("AZURE_ACCOUNT_KEY")
    azure_container = setting("AZURE_CONTAINER")

    def __init__(self, request=None):
        super(AzureFileUploadHandler, self).__init__(request)
        self.file = None
        self.block_num = 0
        self.block = None
        self.block_blob_service = BlockBlobService(self.account_name, self.account_key)

    def new_file(self, field_name, file_name, content_type, content_length, charset=None, content_type_extra=None):
        logger.debug('new file')
        self.file_name = unique_upload(None, file_name)
        super(AzureFileUploadHandler, self).new_file(field_name, self.file_name, content_type, content_length, charset,
                                                     content_type_extra)

    def receive_data_chunk(self, raw_data, start):
        logger.debug(str(self.block_num))
        raw_data_size = sys.getsizeof(raw_data)
        logger.debug(str(raw_data_size))
        if self.block:
            self.block += raw_data
            if sys.getsizeof(self.block) > (self.max_chunk_size - raw_data_size):
                self.upload_part()
                self.block = None
        else:
            self.block = raw_data

    def upload_part(self):
        try:
            self.block_blob_service._put_blob(self.azure_container, self.file_name, self.block)
        except RuntimeError as e:
            logger.debug(e)
        logger.debug(str(self.block_num))
        logger.debug(str(self.file_name))
        self.block_num += 1

    def file_complete(self, file_size):
        if self.block:
            self.upload_part()
        logger.debug("not open")
        blob = self.block_blob_service.get_blob_to_bytes(self.azure_container, self.file_name)
        self.file = ContentFile(blob.content)
        self.file.name = self.file_name
        self.file.size = blob.properties.content_length
        logger.debug("upload complete")
        return self.file
