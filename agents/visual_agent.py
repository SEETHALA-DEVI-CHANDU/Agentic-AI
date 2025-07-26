# agents/visual_agent.py - Updated with Custom Instructions

class VisualAgent:
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        
        # Updated system prompt with new instructions
        self.system_prompt = """
You are an educational AI that creates SVG diagrams to clearly explain data or answer questions for students.

CRITICAL REQUIREMENTS:
1. The image should clearly explain the data given by the user or answer the question if users asks it
2. Keep it simple and easy to understand
3. Do not include any toxic content since the end user might probably be a student
4. You are allowed to add colors and do any creative things until the image provides amazing response
5. Focus on clarity and educational value
6. Make the diagram engaging and visually appealing
7. Use appropriate colors to enhance understanding

DESIGN PRINCIPLES:
- Prioritize clear communication of the concept or data
- Make it visually engaging with appropriate use of colors
- Ensure the image content is appropriate for students
- Be creative in your approach while maintaining educational focus
- Use visual elements that enhance comprehension

OUTPUT FORMAT:
- Return ONLY the SVG code starting with <svg> and ending with </svg>
- Use viewBox="0 0 400 300" for consistent sizing
- No explanations, descriptions, or additional text

Focus on creating amazing visual responses that effectively communicate the information or answer the user's question.
"""

    def generate_visual(self, user_description: str) -> str:
        """
        Generate educational visuals that clearly explain data or answer questions
        
        Args:
            user_description: User's description of what they want visualized or question to be answered
            
        Returns:
            Clean SVG code ready for display
        """
        
        # Enhanced prompt with specific instructions
        full_prompt = [
            self.system_prompt,
            f"""
Create a diagram for: {user_description}

REMEMBER:
- Clearly explain the data or answer the question provided
- Keep it simple but engaging
- Use colors creatively to enhance understanding
- Ensure content is appropriate for students
- Make the visual response amazing and effective

Generate the SVG now:
"""
        ]

        # Call the AI service to get the response
        svg_code = self.gemini_service.generate_text_response(full_prompt)

        # Clean and validate the SVG code
        cleaned_svg = self._clean_and_validate_svg(svg_code)
        return cleaned_svg

    def _clean_and_validate_svg(self, svg_code: str) -> str:
        """Clean and validate the SVG code"""
        
        # Extract SVG content
        if "<svg" in svg_code and "</svg>" in svg_code:
            start = svg_code.find("<svg")
            end = svg_code.rfind("</svg>") + len("</svg>")
            clean_svg = svg_code[start:end]
        else:
            return self._create_fallback_svg("Error: Could not generate proper SVG")
        
        # Basic validation
        if not self._is_valid_svg(clean_svg):
            return self._create_fallback_svg("Simple diagram placeholder")
            
        return clean_svg

    def _is_valid_svg(self, svg_code: str) -> bool:
        """Check if the SVG is valid and appropriate"""
        
        # Check for basic SVG structure
        if not ("<svg" in svg_code and "</svg>" in svg_code):
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
            
        description = f"Create a diagram explaining {concept}. {element_text}. Make it colorful, engaging, and educational."
        
        return self.generate_visual(description)

    def generate_process_flow(self, process_name: str, steps: list) -> str:
        """
        Generate process flow diagrams
        
        Args:
            process_name: Name of the process
            steps: List of steps in the process
            
        Returns:
            SVG code for the process flow
        """
        
        steps_text = " → ".join(steps)
        description = f"Create a flow diagram for {process_name} with these steps: {steps_text}. Use colors and creative design to make it engaging."
        
        return self.generate_visual(description)

    def generate_comparison_chart(self, title: str, items: dict) -> str:
        """
        Generate comparison charts
        
        Args:
            title: Chart title
            items: Dictionary of items to compare
            
        Returns:
            SVG code for the comparison chart
        """
        
        comparison_text = ", ".join([f"{k}: {v}" for k, v in items.items()])
        description = f"Create a comparison chart for {title}. Compare: {comparison_text}. Use colors and creative design to clearly show the differences."
        
        return self.generate_visual(description)