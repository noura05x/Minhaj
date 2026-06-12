from agent_state import AgentState
import json
from langchain_core.messages import HumanMessage



class ValidationAgent:
    """
    Agent 3: Learning Design & Validation Agent
    Makes the course educationally correct and constraint-compliant
    """
    
    def __init__(self, llm):
        self.llm = llm
    
    def __call__(self, state: AgentState) -> AgentState:
        user_input = state["user_input"]
        structure = state["course_structure"]
        
        # Check if structure was built successfully
        if "error" in structure:
            print("✗ Cannot validate due to structure error")
            state["validated_course"] = {"error": "Structure failed"}
            return state
        
        # Prepare structure summary
        structure_text = json.dumps(structure, indent=2)[:4000]
        
        # Validate and improve
        prompt = f"""You are a learning design validator and educational quality expert.

User Requirements:
- Topic: {user_input['target_topic']}
- Level: {user_input['learner_level']}
- Duration: {user_input['duration_weeks']} weeks
- Goals: {user_input['learning_goals']}
- Constraints: {user_input['constraints_requests']}

Course Structure to Validate:
{structure_text}

Your task: Validate and improve the course structure. Return JSON:
{{
  "validation_results": {{
    "alignment_check": {{
      "goals_to_modules": "pass/fail - reason",
      "modules_to_lessons": "pass/fail - reason",
      "objectives_measurability": "pass/fail - reason"
    }},
    "constraint_compliance": {{
      "duration_check": "pass/fail - reason",
      "level_appropriateness": "pass/fail - reason",
      "constraint_adherence": "pass/fail - reason"
    }},
    "prerequisite_coverage": {{
      "missing_prerequisites": ["..."],
      "status": "pass/fail"
    }},
    "topic_coverage": {{
      "major_gaps": ["..."],
      "status": "pass/fail"
    }},
    "pacing_balance": {{
      "overloaded_modules": ["..."],
      "underloaded_modules": ["..."],
      "status": "pass/fail"
    }}
  }},
  "improvements_made": [
    {{
      "issue": "...",
      "fix": "...",
      "location": "module X / lesson Y"
    }}
  ],
  "final_course": {{
    ... (improved course structure with same schema as input)
  }},
  "quality_score": {{
    "overall": "0-100",
    "breakdown": {{
      "alignment": "0-100",
      "coverage": "0-100",
      "pacing": "0-100",
      "clarity": "0-100"
    }}
  }},
  "recommendations": [
    "...", "..."
  ]
}}

Validation Rules:
1. Every learning goal must map to specific modules/lessons
2. All objectives must be measurable (use Bloom's taxonomy)
3. Duration must match {user_input['duration_weeks']} weeks
4. Level must be appropriate for {user_input['learner_level']}
5. Constraints must be followed: {user_input['constraints_requests']}
6. Prerequisites must be covered before advanced topics
7. No major topic gaps
8. No overloaded modules (too many topics in one module)
9. Logical ordering (no jumping between difficulty levels)

Generate ONLY valid JSON with improved course structure."""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Parse JSON
        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            validated = json.loads(content)
            state["validated_course"] = validated
            
            quality = validated.get("quality_score", {}).get("overall", "N/A")
            print(f"✓ Validator completed - Quality Score: {quality}/100")
            
            issues = validated.get("improvements_made", [])
            if issues:
                print(f"  Fixed {len(issues)} issues")
            
        except json.JSONDecodeError as e:
            print(f"✗ JSON parsing error in Validator: {e}")
            state["validated_course"] = {
                "error": "Failed to parse",
                "raw_response": response.content
            }
        
        return state


