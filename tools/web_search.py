"""Search Tool"""
from tavily import TavilyClient
from config import TAVILY_API_KEY, MAX_SEARCH_RESULTS, SEARCH_DEPTH

    
class WebSearchTool:
    """Web search tool using Tavily API"""
    
    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=TAVILY_API_KEY)
    
    def search(self, query: str) -> list:
        """Perform web search and return results"""
        try:
            response = self.client.search(
                query=query,
                max_results=MAX_SEARCH_RESULTS,
                search_depth=SEARCH_DEPTH,
                include_answer=True
            )
            return response.get('results', [])
        except Exception as e:
            print(f"Search error: {e}")
            return []