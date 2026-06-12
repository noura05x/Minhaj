"""Workflow"""
from langgraph.graph import StateGraph, END
import operator
from langchain_groq import ChatGroq
from tools.web_search import WebSearchTool
from tools.links_fetcher import PreferredLinkFetcher
from agents.researcher import ResearcherAgent
from agents.knowledge_synthesizer import KnowledgeSynthesizerAgent
from agents.structure_builder import StructureBuilderAgent
from agents.validation import ValidationAgent
from agents.slides_agent import SlidesAgent
from agents.labs_agent import LabsAgent
from agents.quiz_agent import QuizAgent
from utils.zipper import create_course_zip
import config
from agent_state import AgentState


class Workflow:
    """Orchestrates the multi-agent course generation workflow"""
    
    def __init__(self):
        # Initialize LLMs
        self.researcher_llm = ChatGroq(
            model=config.RESEARCHER_MODEL,
            temperature=0.1,
            max_tokens=500,
            api_key=config.GROQ_API_KEY
        )
        self.synthesizer_llm = ChatGroq(
            model=config.SYNTHESIZER_MODEL,
            temperature=0.3,
            max_tokens=2000,
            api_key=config.GROQ_API_KEY
        )
        self.structure_llm = ChatGroq(
            model=config.STRUCTURE_MODEL,
            temperature=0.3,
            max_tokens=3000,
            api_key=config.GROQ_API_KEY
        )
        self.validator_llm = ChatGroq(
            model=config.VALIDATOR_MODEL,
            temperature=0.2,
            max_tokens=3000,
            api_key=config.GROQ_API_KEY
        )
        self.content_llm = ChatGroq(
            model=config.CONTENT_MODEL,
            temperature=0.7,
            max_tokens=3000,
            api_key=config.GROQ_API_KEY
        )
        
        # Initialize tools
        self.search_tool = WebSearchTool(config.TAVILY_API_KEY)
        self.link_fetcher = PreferredLinkFetcher()
        
        # Initialize Phase 1 agents (Research & Structure)
        self.researcher = ResearcherAgent(
            self.researcher_llm, 
            self.search_tool, 
            self.link_fetcher
        )
        self.synthesizer = KnowledgeSynthesizerAgent(self.synthesizer_llm)
        self.structure_builder = StructureBuilderAgent(self.structure_llm)
        self.validator = ValidationAgent(self.validator_llm)
        
        # Initialize Phase 2 agents (Content Generation)
        self.slides_agent = SlidesAgent(self.content_llm)
        self.labs_agent = LabsAgent(self.content_llm)
        self.quiz_agent = QuizAgent(self.content_llm)
        
        # Build workflow graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construct the complete agent workflow graph"""
        workflow = StateGraph(AgentState)
        
        # Phase 1: Research & Structure nodes
        workflow.add_node("researcher", self.researcher)
        workflow.add_node("synthesizer", self.synthesizer)
        workflow.add_node("structure_builder", self.structure_builder)
        workflow.add_node("validator", self.validator)
        
        # Phase 2: Content Generation nodes
        workflow.add_node("slides_generation", self.slides_agent)
        workflow.add_node("labs_generation", self.labs_agent)
        workflow.add_node("quiz_generation", self.quiz_agent)
        
        # Phase 1 flow: Research → Synthesize → Structure → Validate
        workflow.set_entry_point("researcher")
        workflow.add_edge("researcher", "synthesizer")
        workflow.add_edge("synthesizer", "structure_builder")
        workflow.add_edge("structure_builder", "validator")
        
        # Phase 2 flow: Slides → Labs → Quiz → End
        workflow.add_edge("validator", "slides_generation")
        workflow.add_edge("slides_generation", "labs_generation")
        workflow.add_edge("labs_generation", "quiz_generation")
        workflow.add_edge("quiz_generation", END)
        
        return workflow.compile()
    
    def run(self, user_input: dict) -> dict:
        """
        Execute the complete workflow with user input
        
        Args:
            user_input: Dictionary containing:
                - target_topic: Course topic
                - learner_level: Target audience level
                - duration_weeks: Course duration
                - learning_goals: List of learning objectives
                - constraints_requests: Any specific constraints
                - preferred_link: Optional reference link
        
        Returns:
            Dictionary with complete workflow results
        """
        
        # Initialize state
        initial_state = AgentState(
            messages=[],
            user_input=user_input,
            search_queries=[],
            web_search_results=[],
            preferred_link_content={},
            synthesized_knowledge={},
            course_structure={},
            validated_course={},
            slides_content={},
            labs_content={},
            quiz_content={},
            next_agent="researcher"
        )
        
        print("\n" + "="*70)
        print("MULTI-AGENT COURSE GENERATION WORKFLOW")
        print("="*70)
        print(f"\nTopic: {user_input.get('target_topic', 'N/A')}")
        print(f"Level: {user_input.get('learner_level', 'N/A')}")
        print(f"Duration: {user_input.get('duration_weeks', 'N/A')} weeks")
        print("\n" + "="*70)
        print("PHASE 1: RESEARCH & STRUCTURE")
        print("="*70 + "\n")
        
        # Run the complete graph
        result = self.graph.invoke(initial_state)
        
        print("\n" + "="*70)
        print("PHASE 2: CONTENT GENERATION COMPLETE")
        print("="*70 + "\n")
        
        # Create ZIP archive
        print("="*70)
        print("FINALIZING OUTPUT")
        print("="*70 + "\n")
        
        try:
            create_course_zip()
        except Exception as e:
            print(f"  Warning: Could not create ZIP: {e}")
        
        # Prepare comprehensive result
        final_result = {
            "user_input": user_input,
            
            # Phase 1 results
            "search_queries": result["search_queries"],
            "web_results_count": len(result["web_search_results"]),
            "preferred_link_fetched": result["preferred_link_content"].get("success", False),
            "synthesized_knowledge": result["synthesized_knowledge"],
            "course_structure": result["course_structure"],
            "validation_results": result["validated_course"],
            "final_course": result["validated_course"].get("final_course", {}),
            
            # Phase 2 results
            "content_generated": {
                "slides_count": len(result.get("slides_content", {})),
                "labs_count": len(result.get("labs_content", {})),
                "quizzes_count": len(result.get("quiz_content", {}))
            },
            
            # Quality metrics
            "quality_score": result["validated_course"].get("quality_score", {}),
            
            # Status
            "status": "completed",
            "output_directory": "course/",
            "zip_file": "course/course.zip"
        }
        
        # Print final summary
        self._print_final_summary(final_result)
        
        return final_result
    
    def _print_final_summary(self, result: dict):
        """Print comprehensive workflow summary"""
        print("\n" + "="*70)
        print("WORKFLOW EXECUTION SUMMARY")
        print("="*70)
        
        print("\n PHASE 1: Research & Structure")
        print(f"  • Search Queries: {len(result['search_queries'])}")
        print(f"  • Web Results: {result['web_results_count']}")
        print(f"  • Preferred Link: {'✓' if result['preferred_link_fetched'] else '✗'}")
        
        quality = result.get("quality_score", {})
        if quality:
            overall = quality.get("overall", "N/A")
            print(f"  • Quality Score: {overall}/100")
        
        print("\n PHASE 2: Content Generation")
        content = result["content_generated"]
        print(f"  • Slides Generated: {content['slides_count']} days")
        print(f"  • Labs Generated: {content['labs_count']} days")
        print(f"  • Quizzes Generated: {content['quizzes_count']} days")
        
        print("\n Output Location")
        print(f"  • Directory: {result['output_directory']}")
        print(f"  • ZIP Archive: {result['zip_file']}")
        
        print("\n Status: " + result["status"].upper())
        print("="*70 + "\n")