from tools.links_fetcher import PreferredLinkFetcher
from agent_state import AgentState
from langchain_core.messages import HumanMessage

def _detect_source_type(url: str) -> str:
    """Detect if source is academic, documentation, tutorial, etc."""
    url_lower = url.lower()
    if any(x in url_lower for x in ['.edu', 'arxiv', 'scholar', 'academic']):
        return "academic"
    elif any(x in url_lower for x in ['docs', 'documentation', 'reference']):
        return "documentation"
    elif any(x in url_lower for x in ['tutorial', 'course', 'learn']):
        return "tutorial"
    elif any(x in url_lower for x in ['github', 'gitlab']):
        return "code_repository"
    else:
        return "general"


class ResearcherAgent:
    """
    Agent generates search queries and retrieves content from web + preferred links
    """
    
    def __init__(self, llm, search_tool, link_fetcher):
        self.llm = llm
        self.search_tool = search_tool
        self.link_fetcher = link_fetcher
    
    def __call__(self, state: AgentState) -> AgentState:
        user_input = state["user_input"]
        
        # Extract key information
        topic = user_input["target_topic"]
        level = user_input["learner_level"]
        duration = user_input["duration_weeks"]
        goals = user_input["learning_goals"]
        
        # Generate search queries
        prompt = f"""You are a curriculum researcher. Generate 5-6 specific search queries to find:
- Course syllabi and curriculum structures for {topic}
- {level} level {topic} topics and learning sequences
- Learning outcomes for {duration}-week courses in {topic}
- Technical coverage: algorithms, frameworks, tools for {topic}
- Industry-standard {topic} skills at {level} level
- Practical labs and projects for {topic}

Goals to prioritize: {goals}

Generate ONLY the search queries, one per line. Be specific and academic."""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Parse queries
        queries = [
            line.strip()
            for line in response.content.split("\n")
            if line.strip() and len(line.strip()) > 10
        ][:6]
        
        print(f"✓ Researcher generated {len(queries)} queries")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")
        
        state["search_queries"] = queries
        
        # Perform web searches
        all_results = []
        for query in queries:
            results = self.search_tool.search(query)
            all_results.extend(results)
        
        # Normalize web search results
        normalized_results = []
        for result in all_results:
            resource = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "relevance_score": result.get("score", 0),
                "source_type": _detect_source_type(result.get("url", "")),
                "source": "web_search"
            }
            normalized_results.append(resource)
        
        state["web_search_results"] = normalized_results
        print(f"✓ Researcher found {len(normalized_results)} web resources")
        
        # Fetch preferred link if provided
        reference_link = user_input.get("reference_link", "").strip()
        if reference_link:
            print(f"✓ Fetching preferred link: {reference_link}")
            link_content = self.link_fetcher.fetch(reference_link)
            state["preferred_link_content"] = link_content
            if link_content["success"]:
                print(f"✓ Successfully fetched preferred link")
            else:
                print(f"✗ Failed to fetch preferred link: {link_content.get('error', 'Unknown error')}")
        else:
            state["preferred_link_content"] = {"success": False, "content": ""}
            print("ℹ No preferred link provided")
        
        return state
