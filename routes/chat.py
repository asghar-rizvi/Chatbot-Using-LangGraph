import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

from schemas.chat import CreateChatReq, MessageReq
from database import (
    create_chat, get_chats, delete_chat,
    save_message, get_messages,
    update_chat_title, get_message_count,
)

from services.agent import stream_response


router = APIRouter(prefix='/api')

@router.post('/chats')
async def create_chat_route(req: CreateChatReq):
    await create_chat(req.id, req.title)
    return {'id': req.id, "title" : req.title}

@router.get('/chats')
async def list_chats():
    return await get_chats()

@router.delete('/chats/{chat_id}')
async def delete_chat_route(chat_id: str):
    await delete_chat(chat_id)
    return {"ok": True}

@router.get('/chats/{chat_id}/messages')
async def get_messages_route(chat_id: str):
    return await get_messages(chat_id)

@router.post('/chats/{chat_id}/message')
async def send_message_route(chat_id: str, req: MessageReq):
    await save_message(chat_id, "user", req.content)
    
    if await get_message_count(chat_id) == 1:
        title = req.content[:50] + ("..." if len(req.content)>50 else "")
        await update_chat_title(chat_id, title)   
    
    rows = await get_messages(chat_id)
    
    lc = []

    for r in rows:
        if r['role'] == 'user':
            lc.append(HumanMessage(content=r['content']))
        elif r['role'] =='assistant':
            lc.append(AIMessage(content=r['content']))
            
    async def generate():
        full= ""
        async for chunk in stream_response(lc):
            yield chunk
            if chunk.startswith("data: "):
                try:
                    d = json.loads(chunk[6:].strip())
                    if d["type"] == "token":
                        full += d["content"]
                    elif d["type"] == "end":
                        full = d.get("full_response", full)
                except Exception:
                    pass
        if full:
            await save_message(chat_id, "assistant", full)
    
    return StreamingResponse(
        generate(),
        media_type='text/event-stream',
        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
                