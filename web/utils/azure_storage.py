from datetime import datetime
import os.path
import mimetypes
import time
from time import mktime
import logging
from django.core.files.base import ContentFile
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

try:
    import azure  # noqa
except ImportError:
    raise ImproperlyConfigured(
        "Could not load Azure bindings. "
        "See https://github.com/WindowsAzure/azure-sdk-for-python")

# azure-storage
from azure.storage.blob import BlockBlobService
from azure.common import AzureMissingResourceHttpError

from storages.utils import setting

logger = logging.getLogger('debug')

def clean_name(name):
    return os.path.normpath(name).replace("\\", "/")


@deconstructible
class AzureStorage(Storage):
    account_name = setting("AZURE_ACCOUNT_NAME")
    account_key = setting("AZURE_ACCOUNT_KEY")
    azure_container = setting("AZURE_CONTAINER")
    azure_ssl = setting("AZURE_SSL")

    def __init__(self, *args, **kwargs):
        super(AzureStorage, self).__init__(*args, **kwargs)
        self._connection = None

    @property
    def connection(self):
        if self._connection is None:
            self._connection = BlockBlobService(
                self.account_name, self.account_key)
        return self._connection

    @property
    def azure_protocol(self):
        if self.azure_ssl:
            return 'https'
        return 'http' if self.azure_ssl is not None else None

    def __get_blob_properties(self, name):
        try:
            return self.connection.get_blob_properties(
                self.azure_container,
                name
            )
        except AzureMissingResourceHttpError:
            return None
        # return None

    def _open(self, name, mode="rb"):
        blob = self.connection.get_blob_to_bytes(self.azure_container, name)
        return ContentFile(blob.content)

    def exists(self, name):
        return self.__get_blob_properties(name) is not None

    def delete(self, name):
        try:
            self.connection.delete_blob(self.azure_container, name)
        except AzureMissingResourceHttpError:
            pass

    def size(self, name):
        blob = self.connection.get_blob_properties(
            self.azure_container, name)
        return blob.properties.content_length

    def _save(self, name, content):
        if hasattr(content.file, 'content_type'):
            content_type = content.file.content_type
        else:
            content_type = mimetypes.guess_type(name)[0]

        if hasattr(content, 'chunks'):
            logger.debug('chunks')
            logger.debug(content.size)
            logger.debug(content.name)
            content_data = b''.join(chunk for chunk in content.chunks())
        else:
            logger.debug('no chunks')
            content_data = content.read()

        self.connection.create_blob_from_bytes(self.azure_container, name,
                                               content_data)
        return name

    def url(self, name):
        if hasattr(self.connection, 'make_blob_url'):
            return self.connection.make_blob_url(
                container_name=self.azure_container,
                blob_name=name,
                protocol=self.azure_protocol,
            )
        else:
            return "{}{}/{}".format(setting('MEDIA_URL'), self.azure_container, name)

    def modified_time(self, name):
        try:
            modified = self.__get_blob_properties(name).properties.last_modified
        except (TypeError, KeyError):
            return super(AzureStorage, self).modified_time(name)

        modified = time.strptime(modified, '%a, %d %b %Y %H:%M:%S %Z')
        modified = datetime.fromtimestamp(mktime(modified))

        return modified
