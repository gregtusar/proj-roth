/**
 * Theme injector utility to forcefully override Base UI and Styletron styles
 */

export const injectThemeStyles = (theme: 'light' | 'dark' | 'terminal') => {
  // Remove any existing injected theme styles
  const existingStyle = document.getElementById('theme-injector-styles');
  if (existingStyle) {
    existingStyle.remove();
  }

  // Don't inject anything for light theme
  if (theme === 'light') {
    return;
  }

  // Create a new style element with maximum specificity overrides
  const styleElement = document.createElement('style');
  styleElement.id = 'theme-injector-styles';
  
  let styles = '';
  
  if (theme === 'dark') {
    styles = `
      /* Dark Mode Ultimate Override */
      * {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
      }
      
      input, textarea, select {
        background-color: #2d2d2d !important;
        border-color: #404040 !important;
      }
      
      button {
        background-color: #404040 !important;
      }
      
      button:hover {
        background-color: #525252 !important;
      }
      
      /* Override Styletron styles */
      [class*="css-"] {
        background-color: inherit !important;
        color: inherit !important;
      }
      
      /* Cards and modals need slightly different background */
      [data-baseweb="card"],
      [data-baseweb="modal"],
      [data-baseweb="popover"] {
        background-color: #2d2d2d !important;
      }
    `;
  } else if (theme === 'terminal') {
    styles = `
      /* Terminal Mode Ultimate Override */
      * {
        background-color: #0a0a0a !important;
        color: #00ff00 !important;
        font-family: "Courier New", Monaco, Consolas, monospace !important;
        text-shadow: 0 0 1px rgba(0, 255, 0, 0.5) !important;
      }
      
      input, textarea, select, button {
        background-color: #0a0a0a !important;
        color: #00ff00 !important;
        border: 1px solid #00ff00 !important;
      }
      
      button:hover, a:hover {
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.8) !important;
      }
      
      /* Override Styletron styles */
      [class*="css-"] {
        background-color: inherit !important;
        color: inherit !important;
        font-family: inherit !important;
      }
      
      ::placeholder {
        color: #007700 !important;
      }
      
      ::selection {
        background-color: #00ff00 !important;
        color: #0a0a0a !important;
      }
      
      ::-webkit-scrollbar-thumb {
        background-color: #00ff00 !important;
      }
    `;
  }
  
  styleElement.innerHTML = styles;
  document.head.appendChild(styleElement);
};

// Also export a function to watch for DOM changes and reapply styles
export const watchAndEnforceTheme = (theme: 'light' | 'dark' | 'terminal') => {
  if (theme === 'light') return;
  
  // Create a mutation observer to watch for new elements
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof HTMLElement) {
            // Reset styles on newly added elements
            if (theme === 'dark') {
              node.style.backgroundColor = '';
              node.style.color = '';
            } else if (theme === 'terminal') {
              node.style.backgroundColor = '';
              node.style.color = '';
              node.style.fontFamily = '';
            }
          }
        });
      }
    });
  });
  
  // Start observing
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
  
  // Return disconnect function
  return () => observer.disconnect();
};