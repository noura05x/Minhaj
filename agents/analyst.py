"""analyst Agent     --old--"""
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from config import GROQ_API_KEY,  ANALYST_MODEL
import json
import sys
# Initialize LLMs
analyst_llm = ChatGroq(model=ANALYST_MODEL, temperature=0.3, api_key=GROQ_API_KEY)



def content_analyst(state):
    """
    Agent analyzes resources and structures curriculum signals
    """
    course_input = state["course_input"]
    resources = state["search_results"]
    
    if not resources:
        state["curriculum_structure"] = {"error": "No resources found"}
        return state
    
    # Prepare resources text
    resources_text = "\n\n".join([
        f"Source {i+1} ({r['source_type']}): {r['title']}\n{r['content'][:500]}"
        for i, r in enumerate(resources[:15])
    ])
    
    # Agent analyzes and structures content
    prompt = f"""Analyze these resources and extract curriculum structure for:
Course: {course_input['course_title']}
Level: {course_input['education_level']}
Duration: {course_input['duration_weeks']} weeks
Goals: {course_input['teaching_goals']}

Resources:
{resources_text}

Extract and structure as JSON:
{{
  "topics": [
    {{
      "week": 1,
      "topic_name": "...",
      "subtopics": ["...", "..."],
      "learning_outcomes": ["...", "..."],
      "technical_coverage": {{
        "core_concepts": ["...", "..."],
        "algorithms_models": ["...", "..."],
        "frameworks_tools": ["...", "..."]
      }},
      "difficulty_level": "beginner/intermediate/advanced"
    }}
  ],
  "overall_structure": {{
    "total_weeks": {course_input['duration_weeks']},
    "recommended_prerequisites": ["...", "..."],
    "assessment_pattern": "...",
    "lab_project_ratio": "..."
  }},
  "domain_technical_coverage": {{
    "core_concepts": ["...", "..."],
    "key_algorithms": ["...", "..."],
    "recommended_frameworks": ["...", "..."],
    "standard_libraries": ["...", "..."]
  }}
}}

Generate ONLY valid JSON. Be specific and technical."""
    
    response = analyst_llm.invoke([HumanMessage(content=prompt)])
    
    # Parse JSON
    try:
        # Extract JSON from response
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        curriculum = json.loads(content)
        state["curriculum_structure"] = curriculum
        print(f"✓ Analyst structured {len(curriculum.get('topics', []))} weeks of content")
        print("analyst output:", curriculum)
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing error: {e}")
        state["curriculum_structure"] = {"raw_response": response.content}
    return state

