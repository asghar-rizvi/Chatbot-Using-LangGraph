import json, os
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI

from services.tools import get_all_tools


class AgentState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]
    
SYSTEM_PROMPT = (
    "You are a helpful AI assistant.\n"
    "Tools available:\n"
    "• Calculator (add, subtract, multiply, divide)\n"
    "• get_stock_price — real-time stock quotes\n"
    "• web_search — DuckDuckGo internet search\n"
    "• search_documents — search user-uploaded PDFs\n\n"
    "Use the right tool when needed. Be concise and friendly."
)

_graph = None

def build_graph():
    global _graph
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
        streaming=True,
    )
    
    tools = get_all_tools()
    tool_node = ToolNode(tools)
    
    llm_with_tools = llm.bind_tools(tools)
    
    async def chatbot_node(state: AgentState):
        messages = state["messages"]
        mssg= [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = await llm_with_tools.ainvoke(mssg)
        return {"messages" : [response] }
    
    # Graph Initialize
    g= StateGraph(AgentState)
    
    #Graphs Nodes
    g.add_node("chatbot_node", chatbot_node)
    g.add_node("tools", tool_node)
    
    #Graphs Edges
    g.add_edge(START, "chatbot_node")
    g.add_conditional_edges("chatbot_node", tools_condition)
    g.add_edge("tools", "chatbot_node")
    
    _graph = g.compile()

def get_graph():
    return _graph

async def stream_response(messages: list[BaseMessage]): 
    graph = get_graph()
    tool_names = {t.name for t in get_all_tools()}

    full = ''
    try:
        async for ev in graph.astream_events({"messages": messages}, version = "v2"):
            kind = ev["event"]
            
            if kind == "on_chat_model_stream":
                
                chunk = ev["data"]["chunk"]

                text = ""
                if hasattr(chunk, "content"):
                    c = chunk.content

                    if isinstance(c, str):
                        text = c

                    elif isinstance(c, list):
                        for block in c:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text += block.get("text", "")
                            elif isinstance(block, str):
                                text += block

                if text:
                    full += text
                    yield f"data: {json.dumps({'type':'token','content': text})}\n\n"
                
            elif kind == "on_tool_start" and ev.get("name") in tool_names:
                yield f"data: {json.dumps({'type':'tool_start','name':ev['name']})}\n\n"

            elif kind == "on_tool_end" and ev.get("name") in tool_names:
                yield f"data: {json.dumps({'type':'tool_end','name':ev['name']})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type':'error','content':str(e)})}\n\n"
    print('model output: ', full)
    yield f"data: {json.dumps({'type':'end','full_response':full})}\n\n"

