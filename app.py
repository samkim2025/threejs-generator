import streamlit as st
import anthropic
import os
import re
import json
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

# Get API key (will use secrets in Streamlit Cloud)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")

if not ANTHROPIC_API_KEY:
    st.error("ANTHROPIC_API_KEY is not set. Please add it to your Streamlit secrets.")
    st.stop()

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Set page configuration
st.set_page_config(
    page_title="AI Three.js Scene Generator",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if "history" not in st.session_state:
    st.session_state.history = []
if "current_scene" not in st.session_state:
    st.session_state.current_scene = None

def extract_code(response_text):
    """Extract Three.js code from Claude's response."""
    # Try to extract HTML code blocks first
    html_pattern = r"```(?:html)(.*?)```"
    html_matches = re.findall(html_pattern, response_text, re.DOTALL)
    
    if html_matches:
        return html_matches[0].strip(), "html"
    
    # Then try JavaScript code blocks
    js_pattern = r"```(?:javascript|js)(.*?)```"
    js_matches = re.findall(js_pattern, response_text, re.DOTALL)
    
    if js_matches:
        return js_matches[0].strip(), "js"
    
    # Fallback: try to find any code block
    generic_pattern = r"```(.*?)```"
    generic_matches = re.findall(generic_pattern, response_text, re.DOTALL)
    
    if generic_matches:
        return generic_matches[0].strip(), "generic"
    
    return "", ""

def generate_threejs_code(prompt):
    """Generate Three.js code using Claude API."""
    system_prompt = """You are an expert in Three.js, WebGL, and 3D web development. 
    Your task is to create complete, standalone Three.js code based on the user's description.
    
    The code must:
    1. Include all necessary Three.js imports from CDN (use the latest stable version)
    2. Set up a proper canvas, scene, camera, renderer, and lighting
    3. Create the 3D objects described by the user with appropriate materials and textures
    4. Include smooth animations and camera controls (OrbitControls)
    5. Be complete, error-free, and ready to run in a browser
    6. Use only Three.js code that works in all modern browsers
    7. Include detailed comments explaining key aspects of the implementation
    
    Format your response with a single code block containing complete HTML with the Three.js code embedded.
    The HTML should be a fully functional standalone page that can be saved and run directly in a browser.
    
    Important guidelines:
    - For textures and models, use only URLs that are publicly accessible and stable
    - Make sure all event listeners are properly set up and removed when appropriate
    - Include responsive design to handle window resizing
    - Use requestAnimationFrame for smooth animations
    - Add error handling for texture and model loading
    """
    
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Create a Three.js scene with the following description: {prompt}. Make it visually interesting with good lighting and materials."}
            ]
        )
        code, code_type = extract_code(response.content[0].text)
        return code, code_type, response.content[0].text
    except Exception as e:
        st.error(f"Error generating code: {str(e)}")
        return "", "", f"Error: {str(e)}"

def create_html_with_code(threejs_code, code_type):
    """Create complete HTML with the Three.js code."""
    # If the code already contains <html>, assume it's complete
    if code_type == "html" and "<html" in threejs_code.lower():
        return threejs_code
    
    # If we have JavaScript code, wrap it in HTML
    if code_type == "js" and not "<html" in threejs_code.lower():
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AI Generated Three.js Scene</title>
            <style>
                body {{ margin: 0; overflow: hidden; }}
                canvas {{ width: 100%; height: 100%; display: block; }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
        </head>
        <body>
            <script>
            {threejs_code}
            </script>
        </body>
        </html>
        """
    
    # If we have generic code or empty code, return as is
    return threejs_code if threejs_code.strip() else ""

def add_to_history(prompt, html_content):
    """Add a generated scene to history."""
    st.session_state.history.append({
        "prompt": prompt,
        "html": html_content,
        "timestamp": st.session_state.get("current_timestamp", "")
    })

def render_threejs_scene(html_content, height=600):
    """Render the Three.js scene in an iframe."""
    # Use streamlit components to render HTML
    st.components.v1.html(html_content, height=height, scrolling=False)

# Sidebar
with st.sidebar:
    st.title("🎮 Scene History")
    
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            if st.button(f"Scene {i+1}: {item['prompt'][:30]}...", key=f"history_{i}"):
                st.session_state.current_scene = item
    else:
        st.info("Your generated scenes will appear here")

# Main content
st.title("🎮 AI Three.js Scene Generator")
st.write("Enter a description and get a 3D scene generated with Three.js")

# Input form
with st.form("scene_generator_form"):
    user_prompt = st.text_area(
        "Describe your 3D scene:", 
        placeholder="Describe your Three.js scene here! For example: A forest with trees, a flowing river, and birds flying overhead",
        height=150
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        submitted = st.form_submit_button("Generate 3D Scene", use_container_width=True)
    with col2:
        example_button = st.form_submit_button("Use Random Example", use_container_width=True)
    
    # Handle random example
    if example_button:
        examples = [
            "A solar system with textured planets orbiting around the sun",
            "A peaceful forest scene with trees, a lake, and animated birds flying",
            "A futuristic city with neon buildings and flying vehicles",
            "An underwater scene with fish, coral, and bubbles rising to the surface",
            "A mountain landscape with snow-capped peaks and a log cabin"
        ]
        import random
        user_prompt = random.choice(examples)
        submitted = True
    
    if submitted and user_prompt:
        with st.spinner("Generating your 3D scene..."):
            import time
            st.session_state.current_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            code, code_type, full_response = generate_threejs_code(user_prompt)
            
            if code:
                html_content = create_html_with_code(code, code_type)
                
                # Save current scene to state
                st.session_state.current_scene = {
                    "prompt": user_prompt,
                    "html": html_content,
                    "code": code,
                    "code_type": code_type,
                    "full_response": full_response,
                    "timestamp": st.session_state.current_timestamp
                }
                
                # Add to history
                add_to_history(user_prompt, html_content)
                
                st.success("Scene generated successfully!")
            else:
                st.error("Failed to generate Three.js code. Please try a different description.")

# Display current scene if available
if st.session_state.current_scene:
    scene = st.session_state.current_scene
    
    st.subheader(f"Scene: {scene['prompt']}")
    
    render_threejs_scene(scene["html"])
    
    # Display code and response
    tab1, tab2 = st.tabs(["Generated Code", "AI Response"])
    
    with tab1:
        st.code(scene.get("code", ""), language="javascript")
        
        # Download button for HTML
        html_content = scene.get("html", "")
        if html_content:
            st.download_button(
                label="Download HTML",
                data=html_content,
                file_name="threejs_scene.html",
                mime="text/html"
            )
    
    with tab2:
        st.text_area("Full AI Response", value=scene.get("full_response", ""), height=400, disabled=True)

# Instructions
st.markdown("---")
st.markdown("""
### 🚀 How to use this tool
1. Enter a description of the 3D scene you want to create
2. Click "Generate 3D Scene"
3. The AI will create Three.js code and render the scene
4. Interact with the scene using your mouse:
   - Left-click + drag: Rotate the camera
   - Right-click + drag: Pan the camera
   - Scroll: Zoom in/out

### 💡 Tips for better results
- Be specific about colors, shapes, materials, and lighting
- Mention if you want animations or interactions
- Specify camera position and perspective if important
- Describe the mood or atmosphere you want to create
""")
