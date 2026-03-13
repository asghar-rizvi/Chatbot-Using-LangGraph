from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
import requests

search_tool = DuckDuckGoSearchRun()

@tool
def calculator(firstNum: float, SecondNum: float, operation: str) -> dict:
    """Perform basic 4 operations of calculator on the 2 numbers  given
        operations to perform: add, mul, div, sub
    """
    try:
        if operation == "add":
            result = firstNum + SecondNum
        elif operation == "sub":
            result = firstNum - SecondNum
        elif operation == "mul":
            result = firstNum * SecondNum
        elif operation == "div":
            if SecondNum == 0:
                return {"error": "Division by zero performed"}
            result = firstNum / SecondNum
        else :
            return {"error" : "No supported operation"}
        
        return {"first number":firstNum, "Second Number": SecondNum, "operation":operation, "result":result}
    
    except Exception as e:
        return {"error" : str(e)}
    
@tool
def fetch_stock_price(symbol:str) ->dict:
    """
    Fetch the latest stock price of the given symbol (ecample : GOOGLE, AAPL, TSLA)
    using the api of Alpha Vantage
    """
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=FIFWKMIO8G23ZZ8D'
    r = requests.get(url)
    return r.json()

@tool
def search_documents(query: str) -> str:
    """Search through the uploaded documents for relevant information"""
    from services.rag import search_docs
    return search_docs(query)

ALL_TOOLS = [calculator, fetch_stock_price, search_documents, search_tool]

def get_all_tools():
    return ALL_TOOLS