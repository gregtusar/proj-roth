"""Copy to clipboard button component for Streamlit."""

import streamlit as st
import streamlit.components.v1 as components
import hashlib

def copy_button(text_to_copy: str, button_text: str = "📋", key: str = None):
    """
    Create a button that copies text to clipboard when clicked.
    
    Args:
        text_to_copy: The text to copy to clipboard
        button_text: The text/emoji to display on the button
        key: Unique key for the component
    
    Returns:
        True if the button was clicked, False otherwise
    """
    if key is None:
        # Generate a unique key based on the text content
        key = hashlib.md5(text_to_copy.encode()).hexdigest()[:8]
    
    # Create the HTML/JavaScript for the copy button
    html_code = f"""
    <style>
        .copy-btn {{
            background: transparent;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .copy-btn:hover {{
            background: #f0f0f0;
            border-color: #3B5D7C;
        }}
        .copy-btn.copied {{
            background: #e8f5e9;
            border-color: #4caf50;
        }}
    </style>
    <button class="copy-btn" id="copy-btn-{key}" onclick="copyToClipboard_{key}()">
        {button_text}
    </button>
    <script>
        function copyToClipboard_{key}() {{
            const text = {repr(text_to_copy)};
            navigator.clipboard.writeText(text).then(function() {{
                const btn = document.getElementById('copy-btn-{key}');
                const originalText = btn.innerText;
                btn.innerText = '✅ Copied!';
                btn.classList.add('copied');
                setTimeout(function() {{
                    btn.innerText = originalText;
                    btn.classList.remove('copied');
                }}, 2000);
            }}).catch(function(err) {{
                console.error('Failed to copy: ', err);
                // Fallback for older browsers
                const textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.position = "fixed";
                textArea.style.left = "-999999px";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    const btn = document.getElementById('copy-btn-{key}');
                    const originalText = btn.innerText;
                    btn.innerText = '✅ Copied!';
                    btn.classList.add('copied');
                    setTimeout(function() {{
                        btn.innerText = originalText;
                        btn.classList.remove('copied');
                    }}, 2000);
                }} catch (err) {{
                    console.error('Fallback copy failed: ', err);
                }}
                document.body.removeChild(textArea);
            }});
        }}
    </script>
    """
    
    components.html(html_code, height=40, scrolling=False)
    return False  # Since this is a JavaScript-only interaction