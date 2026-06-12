from tavily import TavilyClient
from config import TAVILY_API_KEY, MAX_SEARCH_RESULTS, SEARCH_DEPTH

class PreferredLinkFetcher:
    """Fetch and parse content from preferred links using Tavily"""

    tavily = TavilyClient(api_key=TAVILY_API_KEY)

    @staticmethod
    def fetch(url: str) -> dict:
        """Fetch content from a URL using Tavily"""
        try:
            result = PreferredLinkFetcher.tavily.extract(
                urls=[url],
                include_raw_content=False
            )

            if not result or "results" not in result or len(result["results"]) == 0:
                return {
                    "url": url,
                    "content": "",
                    "success": False,
                    "error": "No content returned from Tavily"
                }

            page = result["results"][0]

            return {
                "url": url,
                "title": page.get("title", ""),
                "content": page.get("content", "")[:5000],
                "success": True
            }

        except Exception as e:
            print(f"Error fetching {url} with Tavily: {e}")
            return {
                "url": url,
                "content": "",
                "success": False,
                "error": str(e)
            }
