from azure.storage.blob import (
    BlockBlobService,
    BlobPermissions
)
import uuid
from datetime import datetime, timedelta

# Azure storage
AZURE_ACCOUNT_NAME='triggerbackendnormal'
AZURE_ACCOUNT_KEY='tadQP8+aFdnxzHBx37KYLoIV92H+Ju9U7a+k1qtwaQDE0tH23qQ7mUUD1qzvXBGd6cGgo7rW4jeA8H6AzXZdPg=='
AZURE_CONTAINER='backend-media'


def generate_blob_sas():
    block_blob_service = BlockBlobService(account_name=AZURE_ACCOUNT_NAME,
                                          account_key=AZURE_ACCOUNT_KEY)
    video_name = "{}.{}".format(uuid.uuid4(), 'mp4')
    block_blob_service.create_blob_from_bytes(AZURE_CONTAINER, video_name, b'')
    token = block_blob_service.generate_blob_shared_access_signature(AZURE_CONTAINER, video_name,
                                                                     BlobPermissions.WRITE,
                                                                     datetime.utcnow() + timedelta(hours=120))
    full_path = "https://" + AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + AZURE_CONTAINER + "/" + video_name
    return [full_path, token]


if __name__ == '__main__':
    print(generate_blob_sas())