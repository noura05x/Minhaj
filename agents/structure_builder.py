from agent_state import AgentState
import json
from langchain_core.messages import HumanMessage



class StructureBuilderAgent:
    """
    Agent 2: Course Structure Builder (Main Brain)
    Designs the actual course structure
    """
    
    def __init__(self, llm):
        self.llm = llm
    
    def __call__(self, state: AgentState) -> AgentState:
        user_input = state["user_input"]
        knowledge = state["synthesized_knowledge"]
        
        # Check if synthesis was successful
        if "error" in knowledge:
            print("✗ Cannot build structure due to synthesis error")
            state["course_structure"] = {"error": "Synthesis failed"}
            return state
        
        # Prepare knowledge summary
        knowledge_text = json.dumps(knowledge, indent=2)[:3000]
        
        # Build course structure
        prompt = f"""You are a course structure architect.

User Requirements:
- Topic: {user_input['target_topic']}
- Level: {user_input['learner_level']}
- Duration: {user_input['duration_weeks']} weeks
- Goals: {user_input['learning_goals']}
- Constraints: {user_input['constraints_requests']}
- Preferred Tools: {user_input.get('preferred_tools', 'N/A')}

Synthesized Knowledge:
{knowledge_text}

Design the complete course structure as JSON:
{{
  "course_metadata": {{
    "title": "...",
    "duration_weeks": {user_input['duration_weeks']},
    "estimated_hours_per_week": "...",
    "level": "{user_input['learner_level']}",
    "prerequisites": ["..."]
  }},
  "modules": [
    {{
      "module_number": 1,
      "module_title": "...",
      "module_goals": ["...", "..."],
      "duration_hours": "...",
      "lessons": [
        {{
          "lesson_number": 1,
          "lesson_title": "...",
          "learning_objectives": ["...", "..."],
          "topics_covered": ["...", "..."],
          "estimated_duration": "... hours",
          "lab_focus": "...",
          "deliverables": ["..."]
        }}
      ]
    }}
  ],
  "learning_progression": {{
    "week_1": "Focus area",
    "week_2": "Focus area",
    ...
  }},
  "assessment_strategy": {{
    "formative": ["...", "..."],
    "summative": ["...", "..."],
    "practical_projects": ["...", "..."]
  }}
}}

Design Rules:
1. Number of modules = duration_weeks (or duration_weeks/2 for longer courses)
2. Each module should have 3-5 lessons
3. Logical learning progression (fundamentals → intermediate → advanced)
4. Scope depth appropriate for {user_input['learner_level']} level
5. Respect constraint: {user_input['constraints_requests']}
6. Each lesson should have clear, measurable objectives
7. Include practical lab focus as requested

Generate ONLY valid JSON."""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Parse JSON
        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            structure = json.loads(content)
            state["course_structure"] = structure
            print(f"✓ Structure Builder created {len(structure.get('modules', []))} modules")
            
        except json.JSONDecodeError as e:
            print(f"✗ JSON parsing error in Structure Builder: {e}")
            state["course_structure"] = {
                "error": "Failed to parse",
                "raw_response": response.content
            }
        
        return state
