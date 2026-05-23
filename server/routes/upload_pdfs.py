from fastapi import APIRouter, File, UploadFile
from typing import List
from modules.load_vectorstore import load_vectorstore
from fastapi.responses import JSONResponse
from logger import logger

# Initialise our API router
router = APIRouter()


@router.post("/upload_pdfs/")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    try:
        logger.info(f"Received {len(files)} files for upload.")
        load_vectorstore(files)
        logger.info("Successfully processed and uploaded PDFs to Pinecone.")
    except Exception as e:
        logger.exception(f"Error uploading PDFs: {e}")
        return JSONResponse(content={"error": "Failed to upload PDFs"}, status_code=500)
