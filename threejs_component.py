import streamlit.components.v1 as components
import os
import tempfile
import base64

def render_threejs_enhanced(html_content, height=600):
    """Render Three.js content with additional features."""
    # Add error handling wrapper around the HTML content
    enhanced_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; overflow: hidden; font-family: Arial, sans-serif; }}
            #errorOverlay {{
                display: none;
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.7);
                color: white;
                padding: 20px;
                box-sizing: border-box;
                overflow: auto;
                z-index: 1000;
            }}
            #stats {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                background-color: rgba(0,0,0,0.5);
                color: white;
                padding: 5px;
                border-radius: 3px;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div id="errorOverlay"></div>
        <div id="stats"></div>
        <script>
            // Error handling
            window.addEventListener('error', function(event) {{
                const errorOverlay = document.getElementById('errorOverlay');
                errorOverlay.innerHTML = '<h3>Error:</h3><pre>' + event.message + 
                    '\\n\\nLine: ' + event.lineno + 
                    '\\nFile: ' + event.filename + '</pre>';
                errorOverlay.style.display = 'block';
                console.error(event);
            }});
            
            // Performance stats
            let frameCount = 0;
            let lastTime = performance.now();
            
            function updateStats() {{
                const now = performance.now();
                const elapsed = now - lastTime;
                
                if (elapsed >= 1000) {{
                    const fps = Math.round((frameCount * 1000) / elapsed);
                    document.getElementById('stats').textContent = fps + ' FPS';
                    
                    frameCount = 0;
                    lastTime = now;
                }}
                
                frameCount++;
                requestAnimationFrame(updateStats);
            }}
            
            requestAnimationFrame(updateStats);
        </script>
        
        {html_content}
    </body>
    </html>
    """
    
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
        f.write(enhanced_html)
        temp_path = f.name
    
    # Read the file content
    with open(temp_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Delete the temporary file
    os.unlink(temp_path)
    
    # Render HTML in an iframe
    components.html(html_content, height=height, scrolling=False)