import os
import json
from pathlib import Path
from agent_state import AgentState
from langchain_core.messages import HumanMessage
import config

class SlidesAgent:
    """Agent for generating daily slides content"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self):
        with open('prompts/slides_prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    
    def __call__(self, state: AgentState) -> AgentState:
        validated = state["validated_course"]
        
        if "error" in validated:
            print("✗ SlidesAgent: Cannot generate - validation failed")
            return state
        
        final_course = validated.get("final_course", {})
        
        # Extract daily breakdown with proper week calculation
        daily_schedule = self._extract_daily_schedule(final_course, state)
        
        if not daily_schedule:
            print("✗ SlidesAgent: No daily schedule found")
            return state
        
        print(f"\n{'='*60}")
        print("SLIDES GENERATION PHASE")
        print(f"{'='*60}\n")
        
        if "slides_content" not in state:
            state["slides_content"] = {}
        
        # Generate slides for each day
        for day_info in daily_schedule:
            self._generate_day_slides(day_info, final_course, state)
        
        total_weeks = max([d['week'] for d in daily_schedule])
        print(f"\n✓ SlidesAgent: Completed {len(daily_schedule)} days across {total_weeks} weeks\n")
        
        return state
    
    def _extract_daily_schedule(self, final_course, state):
        """Extract daily breakdown ensuring 5 days per week"""
        daily_schedule = []
        
        # Get duration
        duration_weeks = state["user_input"].get("duration_weeks", 1)
        days_per_week = 5
        total_days = duration_weeks * days_per_week
        
        print(f"Course Duration: {duration_weeks} weeks × {days_per_week} days = {total_days} total days")
        
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
                print(f"⚠️  Only {len(lessons_list)} lessons found, padding to {total_days}")
                while len(lessons_list) < total_days:
                    day_num = len(lessons_list) + 1
                    lessons_list.append({
                        "title": f"Day {day_num} - Review and Practice",
                        "topics": ["Review previous concepts", "Hands-on practice"],
                        "objectives": ["Reinforce learning"]
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
                    "topics": lesson.get("topics", []),
                    "objectives": lesson.get("objectives", [])
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
                        day_data = {
                            "title": f"Day {day_counter} - Review",
                            "topics": ["Review and Practice"]
                        }
                    
                    daily_schedule.append({
                        "day": day_counter,
                        "week": week_num,
                        "title": day_data.get("title", f"Day {day_counter}"),
                        "topics": day_data.get("topics", []),
                        "objectives": day_data.get("objectives", [])
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
                    "topics": ["Course Content"],
                    "objectives": []
                })
        
        # FINAL CHECK: Must be exactly total_days
        if len(daily_schedule) != total_days:
            print(f"⚠️  Adjusting schedule from {len(daily_schedule)} to {total_days} days")
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
                        "topics": ["Review and Practice"]
                    })
        
        return daily_schedule
    
    def _generate_day_slides(self, day_info, final_course, state):
        """Generate slides for a single day"""
        day_num = day_info.get("day", 1)
        week_num = day_info.get("week", 1)
        day_title = day_info.get("title", "Untitled Day")
        day_topics = day_info.get("topics", [])
        
        # Extract constraints
        constraints = final_course.get("constraints", {})
        min_slides = constraints.get("min_slides_per_day", 10)
        max_slides = constraints.get("max_slides_per_day", 15)
        learner_level = state["user_input"].get("learner_level", "Beginner")
        day_duration = constraints.get("hours_per_day", 2)
        course_title = final_course.get("title", "Course")
        
        # Build prompt
        prompt = self.prompt_template.format(
            validated_course_json=json.dumps(final_course, indent=2)[:3000],
            day_number=day_num,
            day_title=day_title,
            day_topics=", ".join(day_topics) if day_topics else "General topics",
            min_slides=min_slides,
            max_slides=max_slides,
            learner_level=learner_level,
            day_duration_hours=day_duration,
            course_title=course_title
        )
        
        print(f"  Generating slides for Day {day_num}: {day_title}...")
        
        try:
            # Generate content
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # Get output paths
            paths = config.get_output_paths(week_num, day_num)
            
            # Create directories
            Path(paths["day_dir"]).mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(paths["slides"], 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"    ✓ Saved: {paths['slides']}")
            
            # Store in state
            state["slides_content"][day_num] = content
            
        except Exception as e:
            print(f"    ✗ Error generating slides for Day {day_num}: {e}")
            state["slides_content"][day_num] = f"# Error\n\nFailed to generate slides: {e}"