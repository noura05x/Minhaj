import os
import json
from pathlib import Path
from agent_state import AgentState
from langchain_core.messages import HumanMessage
import config

class QuizAgent:
    """Agent for generating daily quizzes"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self):
        with open('prompts/quiz_prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    
    def __call__(self, state: AgentState) -> AgentState:
        validated = state["validated_course"]
        
        if "error" in validated:
            print("✗ QuizAgent: Cannot generate - validation failed")
            return state
        
        if "slides_content" not in state or not state["slides_content"]:
            print("✗ QuizAgent: No slides content found")
            return state
        
        final_course = validated.get("final_course", {})
        
        print(f"\n{'='*60}")
        print("QUIZ GENERATION PHASE")
        print(f"{'='*60}\n")
        
        if "quiz_content" not in state:
            state["quiz_content"] = {}
        
        # Get daily schedule
        daily_schedule = self._extract_daily_schedule(final_course, state)
        
        # Generate quiz for each day that has slides
        for day_num, slides_content in sorted(state["slides_content"].items()):
            day_info = next((d for d in daily_schedule if d.get("day") == day_num), None)
            
            if day_info:
                self._generate_day_quiz(day_info, slides_content, final_course, state)
            else:
                print(f"⚠️  Warning: No schedule info for Day {day_num}, skipping quiz")
        
        print(f"\n✓ QuizAgent: Completed {len(state['quiz_content'])} quizzes\n")
        
        return state
    
    def _extract_daily_schedule(self, final_course, state):
        """Extract daily breakdown ensuring 5 days per week"""
        daily_schedule = []
        
        # Get duration
        duration_weeks = state["user_input"].get("duration_weeks", 1)
        days_per_week = 5
        total_days = duration_weeks * days_per_week
        
        # Try different structures
        if "daily_breakdown" in final_course:
            daily_schedule = final_course["daily_breakdown"]
            
        elif "modules" in final_course:
            modules = final_course["modules"]
            lessons_list = []
            
            for module in modules:
                lessons = module.get("lessons", [])
                lessons_list.extend(lessons)
            
            # CRITICAL: Ensure exactly total_days
            if len(lessons_list) < total_days:
                while len(lessons_list) < total_days:
                    day_num = len(lessons_list) + 1
                    lessons_list.append({
                        "title": f"Day {day_num} - Review",
                        "topics": ["Review"]
                    })
            elif len(lessons_list) > total_days:
                lessons_list = lessons_list[:total_days]
            
            # Convert to daily schedule
            for day_counter, lesson in enumerate(lessons_list, 1):
                week_num = ((day_counter - 1) // days_per_week) + 1
                daily_schedule.append({
                    "day": day_counter,
                    "week": week_num,
                    "title": lesson.get("title", f"Day {day_counter}"),
                    "topics": lesson.get("topics", [])
                })
        
        elif "weeks" in final_course:
            weeks = final_course["weeks"]
            day_counter = 1
            
            for week_num in range(1, duration_weeks + 1):
                if week_num - 1 < len(weeks):
                    week = weeks[week_num - 1]
                    days_in_week = week.get("days", [])
                else:
                    days_in_week = []
                
                # CRITICAL: Ensure exactly 5 days per week
                for day_in_week in range(days_per_week):
                    if day_in_week < len(days_in_week):
                        day_data = days_in_week[day_in_week]
                    else:
                        day_data = {"title": f"Day {day_counter} - Review", "topics": []}
                    
                    daily_schedule.append({
                        "day": day_counter,
                        "week": week_num,
                        "title": day_data.get("title", f"Day {day_counter}"),
                        "topics": day_data.get("topics", [])
                    })
                    day_counter += 1
        
        else:
            # No structure - create generic
            for day_counter in range(1, total_days + 1):
                week_num = ((day_counter - 1) // days_per_week) + 1
                daily_schedule.append({
                    "day": day_counter,
                    "week": week_num,
                    "title": f"Day {day_counter}",
                    "topics": []
                })
        
        # FINAL CHECK: Must be exactly total_days
        if len(daily_schedule) != total_days:
            if len(daily_schedule) > total_days:
                daily_schedule = daily_schedule[:total_days]
            else:
                while len(daily_schedule) < total_days:
                    day_num = len(daily_schedule) + 1
                    week_num = ((day_num - 1) // days_per_week) + 1
                    daily_schedule.append({
                        "day": day_num,
                        "week": week_num,
                        "title": f"Day {day_num} - Review",
                        "topics": []
                    })
        
        return daily_schedule
    
    def _generate_day_quiz(self, day_info, slides_content, final_course, state):
        """Generate quiz for a single day"""
        day_num = day_info.get("day", 1)
        week_num = day_info.get("week", 1)
        day_title = day_info.get("title", f"Day {day_num}")
        
        # Get question count
        constraints = final_course.get("constraints", {})
        questions_count = constraints.get("questions_per_quiz", 5)
        
        # Build prompt
        prompt = self.prompt_template.format(
            validated_course_json=json.dumps(final_course, indent=2)[:2000],
            day_number=day_num,
            day_title=day_title,
            day_slides_content=slides_content[:8000],
            questions_count=questions_count
        )
        
        print(f"  Week {week_num}, Day {day_num}: {day_title}...")
        
        try:
            # Generate content
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # Get output paths
            paths = config.get_output_paths(week_num, day_num)
            
            # Save to file
            with open(paths["quiz"], 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"    ✓ Saved: {paths['quiz']}")
            
            # Store in state
            state["quiz_content"][day_num] = content
            
        except Exception as e:
            print(f"    ✗ Error generating quiz for Day {day_num}: {e}")
            state["quiz_content"][day_num] = f"# Error\n\nFailed to generate quiz: {e}"