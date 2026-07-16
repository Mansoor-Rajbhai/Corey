# X:\Corey\utilities\web_search.py
from duckduckgo_search import DDGS

def search_internet(query: str, max_results: int = 5):
    """
    Queries the internet for real-time information.
    Returns a structured list of results with titles, links, and text snippets.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
        if not results:
            return {"status": "success", "results": [], "message": "No web pages found."}
            
        formatted_results = []
        for index, item in enumerate(results, start=1):
            formatted_results.append({
                "position": index,
                "title": item.get("title", "No Title"),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")
            })
            
        return {
            "status": "success",
            "query": query,
            "results": formatted_results
        }
    except Exception as e:
        return {"status": "error", "message": f"Web navigation failed: {str(e)}"}