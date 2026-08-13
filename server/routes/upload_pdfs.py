import re
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from ..modules.load_vectorstore import load_vectorstore
from ..logger import logger
from pathlib import Path
from ..schemas import UploadFileSchema, UploadResponse

from ..constants.K import ALLOWED_FILE_EXTENSIONS, PDF_MAGIC_BYTES, MAX_UPLOAD_FILES, MAX_FILE_SIZE_BYTES

# Initialise our API router
router = APIRouter()


@router.post("/upload_pdfs/", response_model=UploadResponse)
async def upload_pdfs(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required")

    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {MAX_UPLOAD_FILES} files can be uploaded at once",
        )
    # validate each file
    validated_files: list[UploadFileSchema] = []
    rejected_count = 0
    total_size = 0

    for file in files:
        try:
            # get file size (read content to get size if not available)
            content = await file.read()
            file_size = len(content)

            total_size += file_size

            if total_size > MAX_UPLOAD_FILES * MAX_FILE_SIZE_BYTES:
                raise ValueError(
                    f"Total upload size exceeds {(MAX_UPLOAD_FILES * MAX_FILE_SIZE_BYTES )}"
                )

            # await file.seek(0)



            safe_filename = re.sub(r"[^\w\-_\.]", "_", file.filename)

            UploadFileSchema(
                filename=safe_filename, content_type=file.content_type, size=file_size
            )
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Invalid file {file.filename} : {str(e)}"
            )

    try:
        logger.info(f"Received {len(files)} files for upload.")
        load_vectorstore(files)
        logger.info("Successfully processed and uploaded PDFs to Pinecone.")
    except Exception as e:
        logger.exception(f"Error uploading PDFs: {e}")
        return JSONResponse(content={"error": "Failed to upload PDFs"}, status_code=500)


# helper functions
def sanitize_filename(filename: str) -> str:
    safe_filename = re.sub(r"[^\w\-_\.]", "_", filename)
    safe_filename = safe_filename.strip()

    if not safe_filename:
        raise ValueError("Filename cannot be empty")

    if Path(safe_filename).suffix.lower() not in ALLOWED_FILE_EXTENSIONS:
        raise ValueError("Only PDF file are allowed")

    return safe_filename


def validate_pdf_magic_bytes(content: bytes) -> None:
    if not content.startswith(PDF_MAGIC_BYTES):
        raise ValueError("Invalid PDF file")
