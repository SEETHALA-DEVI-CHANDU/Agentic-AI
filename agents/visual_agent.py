# agents/visual_agent.py - Optimized for Blackboard-Friendly Drawings

class VisualAgent:
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        
        # Enhanced system prompt optimized for blackboard drawing
        self.system_prompt = """
You are an educational AI that creates simple SVG diagrams specifically designed for teachers to easily draw on a blackboard or whiteboard.

CRITICAL REQUIREMENTS:
1. Use ONLY simple geometric shapes: circles, rectangles, triangles, straight lines, and basic curves
2. Use thick black lines (stroke-width="3" or higher) for maximum visibility
3. No complex shapes, gradients, patterns, or fine details
4. Maximum 8-10 elements per diagram to keep it simple
5. Clear, bold text labels using large fonts (font-size="16" or larger)
6. High contrast: black lines on white background only
7. Arrange elements with plenty of spacing for clarity

BLACKBOARD-FRIENDLY DESIGN PRINCIPLES:
- Think "How would a teacher draw this with chalk in 2 minutes?"
- Use basic shapes that are easy to draw freehand
- Keep proportions simple and forgiving
- Arrows should be simple triangles or basic arrow shapes
- Text should be minimal but clear
- Focus on showing relationships and flow rather than realistic details

OUTPUT FORMAT:
- Return ONLY the SVG code starting with <svg> and ending with </svg>
- Use viewBox="0 0 400 300" for consistent sizing
- No explanations, descriptions, or additional text

EXAMPLE STYLE:
Simple circles for sun/processes, rectangles for containers, basic arrows for flow, stick-figure style simplicity.
"""

    def generate_visual(self, user_description: str) -> str:
        """
        Generate blackboard-friendly educational visuals
        
        Args:
            user_description: Teacher's description of what they want to draw
            
        Returns:
            Clean SVG code ready for display and easy blackboard replication
        """
        
        # Enhanced prompt with specific blackboard instructions
        full_prompt = [
            self.system_prompt,
            f"""
Create a simple diagram for: {user_description}

REMEMBER:
- A teacher should be able to copy this on a blackboard in under 3 minutes
- Use only basic shapes a person can draw freehand
- Keep it simple enough that students can also sketch it in their notebooks
- Focus on the key concept, not artistic beauty
- Make text large and readable from across a classroom

Generate the SVG now:
"""
        ]

        # Call the AI service to get the response
        svg_code = self.gemini_service.generate_text_response(full_prompt)

        # Enhanced cleanup and validation
        cleaned_svg = self._clean_and_validate_svg(svg_code)
        return cleaned_svg

    def _clean_and_validate_svg(self, svg_code: str) -> str:
        """Clean and validate the SVG code for blackboard use"""
        
        # Extract SVG content
        if "<svg" in svg_code and "</svg>" in svg_code:
            start = svg_code.find("<svg")
            end = svg_code.rfind("</svg>") + len("</svg>")
            clean_svg = svg_code[start:end]
        else:
            return self._create_fallback_svg("Error: Could not generate proper SVG")
        
        # Basic validation for blackboard-friendly elements
        if not self._is_blackboard_friendly(clean_svg):
            return self._create_fallback_svg("Simple diagram placeholder")
            
        return clean_svg

    def _is_blackboard_friendly(self, svg_code: str) -> bool:
        """Check if the SVG uses blackboard-friendly elements"""
        
        # Check for overly complex elements that would be hard to draw
        complex_elements = [
            'path d="M', 'bezier', 'curve', 'polygon points=', 
            'gradient', 'pattern', 'filter', 'animation'
        ]
        
        svg_lower = svg_code.lower()
        for element in complex_elements:
            if element in svg_lower:
                return False
                
        return True

    def _create_fallback_svg(self, message: str) -> str:
        """Create a simple fallback SVG when generation fails"""
        return f'''<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
  <rect x="50" y="50" width="300" height="200" fill="none" stroke="black" stroke-width="3"/>
  <text x="200" y="160" text-anchor="middle" font-size="16" fill="black">{message}</text>
</svg>'''

    def generate_concept_diagram(self, concept: str, elements: list = None) -> str:
        """
        Generate specific educational concept diagrams
        
        Args:
            concept: The educational concept (e.g., "water cycle", "photosynthesis")
            elements: Optional list of specific elements to include
            
        Returns:
            SVG code for the concept diagram
        """
        
        if elements:
            element_text = f"Include these specific elements: {', '.join(elements)}"
        else:
            element_text = "Include the most important elements for understanding this concept"
            
        description = f"Create a simple {concept} diagram. {element_text}. Make it perfect for a teacher to draw on a blackboard."
        
        return self.generate_visual(description)

    def generate_process_flow(self, process_name: str, steps: list) -> str:
        """
        Generate simple process flow diagrams
        
        Args:
            process_name: Name of the process
            steps: List of steps in the process
            
        Returns:
            SVG code for the process flow
        """
        
        steps_text = " → ".join(steps)
        description = f"Create a simple flow diagram for {process_name} with these steps: {steps_text}. Use boxes and arrows that are easy to draw on a blackboard."
        
        return self.generate_visual(description)

    def generate_comparison_chart(self, title: str, items: dict) -> str:
        """
        Generate simple comparison charts
        
        Args:
            title: Chart title
            items: Dictionary of items to compare
            
        Returns:
            SVG code for the comparison chart
        """
        
        comparison_text = ", ".join([f"{k}: {v}" for k, v in items.items()])
        description = f"Create a simple comparison chart for {title}. Compare: {comparison_text}. Use simple boxes and text that can be easily drawn on a blackboard."
        
        return self.generate_visual(description)