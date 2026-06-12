from agent_state import AgentState
import json 
from langchain_core.messages import HumanMessage

class KnowledgeSynthesizerAgent:
    """
    Agent 1: Knowledge & Resource Synthesizer
    Turns web search + preferred links into curriculum-relevant knowledge
    """
    
    def __init__(self, llm):
        self.llm = llm
    
    def __call__(self, state: AgentState) -> AgentState:
        user_input = state["user_input"]
        web_results = state["web_search_results"]
        preferred_link = state["preferred_link_content"]
        
        # Prepare resources text
        resources_text = ""
        
        # Prioritize preferred link
        if preferred_link.get("success"):
            resources_text += f"PREFERRED REFERENCE (HIGH PRIORITY):\n"
            resources_text += f"Title: {preferred_link.get('title', 'N/A')}\n"
            resources_text += f"Content: {preferred_link['content'][:2000]}\n\n"
            resources_text += "="*80 + "\n\n"
        
        # Add web search results
        resources_text += "WEB SEARCH RESULTS:\n\n"
        for i, r in enumerate(web_results[:10], 1):
            resources_text += f"Source {i} ({r['source_type']}): {r['title']}\n"
            resources_text += f"{r['content'][:400]}\n\n"
        
        # Synthesize knowledge
        prompt = f"""You are a knowledge synthesizer for curriculum design.

User Requirements:
- Topic: {user_input['target_topic']}
- Level: {user_input['learner_level']}
- Duration: {user_input['duration_weeks']} weeks
- Goals: {user_input['learning_goals']}
- Constraints: {user_input['constraints_requests']}
- Preferred Tools: {user_input.get('preferred_tools', 'N/A')}

Resources:
{resources_text}

Your task: Extract and synthesize curriculum-relevant knowledge as JSON:
{{
  "key_subtopics": [
    {{
      "name": "...",
      "priority": "high/medium/low",
      "source": "preferred_link/web_search",
      "prerequisites": ["..."],
      "typical_duration": "... hours"
    }}
  ],
  "common_learning_order": [
    "subtopic1", "subtopic2", "..."
  ],
  "important_tools_technologies": [
    {{
      "name": "...",
      "category": "framework/library/tool/platform",
      "relevance": "high/medium/low",
      "reason": "..."
    }}
  ],
  "practical_applications": [
    "...", "..."
  ],
  "recommended_prerequisites": [
    "...", "..."
  ],
  "common_challenges": [
    "...", "..."
  ]
}}

Rules:
1. PRIORITIZE information from preferred link over web search
2. Remove duplicates and irrelevant information
3. Align with user's learning goals and constraints
4. Be specific and practical
5. Generate ONLY valid JSON"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Parse JSON
        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            synthesized = json.loads(content)
            state["synthesized_knowledge"] = synthesized
            print(f"✓ Synthesizer extracted {len(synthesized.get('key_subtopics', []))} subtopics")
            
        except json.JSONDecodeError as e:
            print(f"✗ JSON parsing error in Synthesizer: {e}")
            state["synthesized_knowledge"] = {
                "error": "Failed to parse",
                "raw_response": response.content
            }
        
        return state
