import os
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, UploadFile

from auth.auth_bearer import (
    AuthBearer,
    get_current_user,  # pyright: ignore reportPrivateUsage=none,
)
from models.brains import Brain
from models.files import File
from models.settings import common_dependencies
from models.users import User
from utils.file import (
    convert_bytes,  # pyright: ignore reportPrivateUsage=none,
    get_file_size,  # pyright: ignore reportPrivateUsage=none,
)
from utils.processors import filter_file  # pyright: ignore reportPrivateUsage=none

upload_router = APIRouter()


@upload_router.post("/upload", dependencies=[Depends(AuthBearer())], tags=["Upload"])
async def upload_file(  # pyright: ignore reportPrivateUsage=none
    request: Request,
    uploadFile: UploadFile,
    brain_id: UUID = Query(..., description="The ID of the brain"),
    enable_summarization: bool = False,
    current_user: User = Depends(
        get_current_user  # pyright: ignore reportPrivateUsage=none
    ),
):
    """
    Upload a file to the user's storage.

    - `file`: The file to be uploaded.
    - `enable_summarization`: Flag to enable summarization of the file's content.
    - `current_user`: The current authenticated user.
    - Returns the response message indicating the success or failure of the upload.

    This endpoint allows users to upload files to their storage (brain). It checks the remaining free space in the user's storage (brain)
    and ensures that the file size does not exceed the maximum capacity. If the file is within the allowed size limit,
    it can optionally apply summarization to the file's content. The response message will indicate the status of the upload.
    """

    print(brain_id, "brain_id")

    # [TODO] check if the user is the owner/editor of the brain
    brain = Brain(id=brain_id)
    print("brain", brain)
    commons = common_dependencies()

    if request.headers.get("Openai-Api-Key"):
        brain.max_brain_size = os.getenv(
            "MAX_BRAIN_SIZE_WITH_KEY", 209715200
        )  # pyright: ignore reportPrivateUsage=none
    remaining_free_space = brain.remaining_brain_size

    file_size = get_file_size(uploadFile)  # pyright: ignore reportPrivateUsage=none

    file = File(file=uploadFile)
    if remaining_free_space - file_size < 0:
        message = {
            "message": f"❌ User's brain will exceed maximum capacity with this upload. Maximum file allowed is : {convert_bytes(remaining_free_space)}",
            "type": "error",
        }
    else:
        message = await filter_file(  # pyright: ignore reportPrivateUsage=none
            commons,
            file,
            enable_summarization,
            brain_id=brain_id,
            openai_api_key=request.headers.get("Openai-Api-Key", None),
        )

    return message  # pyright: ignore reportPrivateUsage=none
