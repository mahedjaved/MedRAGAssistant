import re
import io
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from modules.load_vectorstore import load_vectorstore
from logger import logger
from pathlib import Path
from schemas import UploadFileSchema, UploadResponse
from constants.k import (
    ALLOWED_FILE_EXTENSIONS,
    PDF_MAGIC_BYTES,
    MAX_UPLOAD_FILES,
    MAX_FILE_SIZE_BYTES,
)

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
            # get file size (read content to get size)
            content = await file.read()
            file_size = len(content)

            # enforce per-file size limit
            if file_size > MAX_FILE_SIZE_BYTES:
                raise ValueError(
                    f"File size exceeds {MAX_FILE_SIZE_BYTES} bytes ({file_size} provided)"
                )

            total_size += file_size

            # validate PDF magic bytes
            if not content.startswith(PDF_MAGIC_BYTES):
                raise ValueError("Invalid PDF file (missing PDF magic bytes)")

            # sanitise filename
            safe_filename = sanitize_filename(file.filename)

            # validate MIME type
            if file.content_type not in {"application/pdf"}:
                raise ValueError("Only PDF files are allowed (wrong MIME type)")

            # build validated schema (registers any extra field violation)
            validated = UploadFileSchema(
                filename=safe_filename,
                content_type=file.content_type,
                size=file_size,
            )

            # reassign the consumed file content so load_vectorstore can read it
            file.file = io.BytesIO(content)
            validated_files.append(validated)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid file {file.filename}: {str(e)}",
            )

    try:
        logger.info(
            f"Received {len(validated_files)} files for upload "
            f"(rejected {rejected_count})."
        )
        load_vectorstore(files)
        logger.info("Successfully processed and uploaded PDFs to Pinecone.")
    except Exception as e:
        logger.exception(f"Error uploading PDFs: {e}")
        return JSONResponse(
            content={"error": "Failed to upload PDFs"},
            status_code=500,
        )

    return UploadResponse(
        status="success",
        uploaded_count=len(validated_files),
        rejected_count=rejected_count,
        files=validated_files,
    )


# helper functions
def sanitize_filename(filename: str) -> str:
    safe_filename = re.sub(r"[^\w\-_\.]", "_", filename)
    safe_filename = safe_filename.strip()

    if not safe_filename:
        raise ValueError("Filename cannot be empty")

    if Path(safe_filename).suffix.lower() not in ALLOWED_FILE_EXTENSIONS:
        raise ValueError("Only PDF files are allowed")

    return safe_filename
