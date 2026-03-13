import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db
from services.agent import build_graph
from routes.chat import router as chat_router
from routes.uploads import router as upload_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database intialized completed")
    build_graph()
    print("Graph build Sucessfully")
    yield
    
app = FastAPI(lifespan=lifespan)
app.include_router(chat_router)
app.include_router(upload_router)

static = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static), name="static")

@app.get('/')
async def index():
    return FileResponse(os.path.join(static, "index.html"))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)