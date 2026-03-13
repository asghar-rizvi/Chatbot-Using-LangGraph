import os, asyncio
from fastapi import APIRouter, UploadFile, File
from services.rag import add_pdf

router = APIRouter(prefix='/api')

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR,exist_ok=True)

@router.post('/upload')
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return {"error": "Only Pdf files are supported"}
    
    path = os.path.join(UPLOAD_DIR, file.filename)
    data = await file.read()
    
    chunks = await asyncio.to_thread(add_pdf, path)

    return {"filename": file.filename, "chunks": chunks}