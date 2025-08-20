"""
List Manager UI component for displaying and managing saved voter lists
"""
import streamlit as st
import pandas as pd
import io
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import logging
from ..voter_list_tool import VoterListTool
from ..bigquery_tool import BigQueryReadOnlyTool

logger = logging.getLogger(__name__)

class ListManagerUI:
    """UI component for managing voter lists"""
    
    def __init__(self):
        self.list_tool = VoterListTool()
        self.bq_tool = BigQueryReadOnlyTool()
        
    def render_list_manager(self):
        """Render the list manager in the sidebar"""
        # Get current user info
        user_info = st.session_state.get("user_info", {})
        user_id = user_info.get("google_id", user_info.get("id", "default_user"))
        user_email = user_info.get("email", "user@example.com")
        
        # Fetch user's lists
        lists = self.list_tool.get_user_lists(user_id, include_shared=True)
        
        if not lists:
            st.markdown("""
            <div class="empty-state">
                No saved lists yet
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Display lists
        for list_item in lists:
            list_name = list_item.get("list_name", "Unnamed List")
            list_id = list_item.get("list_id")
            row_count = list_item.get("row_count", 0)
            created_at = list_item.get("created_at", "")
            
            # Create clickable list item
            if st.button(
                f"📋 {list_name} ({row_count:,} voters)",
                key=f"list_{list_id}",
                use_container_width=True,
                help=f"Created: {created_at[:10] if created_at else 'Unknown'}"
            ):
                # Store selected list in session state
                st.session_state.selected_list = list_item
                st.session_state.show_list_modal = True
                st.rerun()
    
    def render_list_modal(self):
        """Render the modal popup for list details (legacy method for compatibility)"""
        self.render_list_modal_content()
    
    def render_list_modal_content(self):
        """Render the content of the list modal (used by dialog)"""
        list_item = st.session_state.get("selected_list")
        if not list_item:
            st.error("No list selected")
            return
        # Close button
        if st.button("✕ Close", key="close_modal", type="secondary"):
            st.session_state.show_list_modal = False
            st.session_state.selected_list = None
            st.rerun()
        
        st.markdown(f"### {list_item['list_name']}")
        
        # Editable description
        new_description = st.text_area(
            "Description",
            value=list_item.get("description_text", ""),
            key="list_description_edit",
            height=80
        )
        
        # List info
        info_cols = st.columns(3)
        with info_cols[0]:
            st.metric("Total Voters", f"{list_item.get('row_count', 0):,}")
        with info_cols[1]:
            created_at = list_item.get("created_at", "")
            if created_at:
                created_date = datetime.fromisoformat(created_at).strftime("%b %d, %Y")
            else:
                created_date = "Unknown"
            st.metric("Created", created_date)
        with info_cols[2]:
            st.metric("Access Count", list_item.get("access_count", 0))
        
        # Action buttons
        button_cols = st.columns(4)
        
        with button_cols[0]:
            if st.button("🔄 Re-run Query", key="rerun_query_btn", type="primary"):
                st.session_state.should_rerun_query = True
        
        with button_cols[1]:
            if st.button("💾 Save Changes", key="save_changes"):
                if new_description != list_item.get("description_text"):
                    # Update the list description
                    user_info = st.session_state.get("user_info", {})
                    user_id = user_info.get("google_id", user_info.get("id", "default_user"))
                    result = self.list_tool.update_list(
                        list_id=list_item["list_id"],
                        user_id=user_id,
                        description_text=new_description
                    )
                    if result.get("success"):
                        st.success("List updated successfully!")
                        list_item["description_text"] = new_description
                        st.session_state.selected_list = list_item
                    else:
                        st.error(f"Failed to update: {result.get('error')}")
        
        with button_cols[2]:
            if st.button("📋 Copy to Clipboard", key="copy_csv"):
                st.session_state.should_copy_to_clipboard = True
        
        with button_cols[3]:
            if st.button("🗑️ Delete List", key="delete_list"):
                st.session_state.confirm_delete = True
        
        # Confirm delete
        if st.session_state.get("confirm_delete"):
            st.warning("Are you sure you want to delete this list?")
            confirm_cols = st.columns(2)
            with confirm_cols[0]:
                if st.button("Yes, Delete", key="confirm_delete_yes", type="primary"):
                    user_info = st.session_state.get("user_info", {})
                    user_id = user_info.get("google_id", user_info.get("id", "default_user"))
                    result = self.list_tool.delete_list(
                        list_id=list_item["list_id"],
                        user_id=user_id
                    )
                    if result.get("success"):
                        st.success("List deleted successfully!")
                        st.session_state.show_list_modal = False
                        st.session_state.selected_list = None
                        st.session_state.confirm_delete = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to delete: {result.get('error')}")
            with confirm_cols[1]:
                if st.button("Cancel", key="confirm_delete_no"):
                    st.session_state.confirm_delete = False
                    st.rerun()
        
        # SQL Query display
        st.markdown("#### SQL Query")
        st.code(list_item.get("sql_query", ""), language="sql")
        
        # Run query and show results
        if st.session_state.get("should_rerun_query") or not st.session_state.get("query_results"):
            with st.spinner("Running query..."):
                try:
                    # Run the query
                    sql_query = list_item.get("sql_query", "")
                    # Limit to 20 rows for display
                    if "LIMIT" not in sql_query.upper():
                        display_query = f"{sql_query} LIMIT 20"
                    else:
                        # Replace existing limit with 20
                        import re
                        display_query = re.sub(r'LIMIT\s+\d+', 'LIMIT 20', sql_query, flags=re.IGNORECASE)
                    
                    result = self.bq_tool.run(display_query)
                    
                    if result.get("error"):
                        st.error(f"Query failed: {result['error']}")
                        st.session_state.query_results = None
                    else:
                        st.session_state.query_results = result
                        st.session_state.should_rerun_query = False
                        
                        # Increment access count
                        self.list_tool.increment_access_count(list_item["list_id"])
                        
                except Exception as e:
                    st.error(f"Error running query: {str(e)}")
                    st.session_state.query_results = None
        
        # Display results
        if st.session_state.get("query_results"):
            result = st.session_state.query_results
            rows = result.get("rows", [])
            total_count = list_item.get("row_count", len(rows))
            
            # Results summary
            st.info(f"{total_count:,} total results (showing first {len(rows)})")
            
            # Display table
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, height=400)
                
                # Copy to clipboard functionality
                if st.session_state.get("should_copy_to_clipboard"):
                    # Convert to CSV
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()
                    
                    # Create a download button as CSV
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_data,
                        file_name=f"{list_item['list_name'].replace(' ', '_')}.csv",
                        mime="text/csv",
                        key="download_csv"
                    )
                    
                    # Also provide a copyable text area with JavaScript copy button
                    st.markdown("""
                    <script>
                    function copyToClipboard() {
                        const csvData = document.getElementById('csv_data_hidden').value;
                        navigator.clipboard.writeText(csvData).then(function() {
                            // Show success message
                            const btn = document.getElementById('copy_btn');
                            const originalText = btn.innerText;
                            btn.innerText = '✅ Copied!';
                            btn.style.background = '#28a745';
                            setTimeout(() => {
                                btn.innerText = originalText;
                                btn.style.background = '#007bff';
                            }, 2000);
                        }, function(err) {
                            console.error('Could not copy text: ', err);
                            alert('Failed to copy. Please use Ctrl+A and Ctrl+C instead.');
                        });
                    }
                    </script>
                    """, unsafe_allow_html=True)
                    
                    # Hidden textarea with the data
                    st.markdown(f"""
                    <textarea id="csv_data_hidden" style="position: absolute; left: -9999px;">{csv_data}</textarea>
                    <button id="copy_btn" onclick="copyToClipboard()" style="
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                        margin: 10px 0;
                    ">📋 Copy to Clipboard</button>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.should_copy_to_clipboard = False
            else:
                st.info("No results to display")
    
    def set_user_context(self, user_id: str, user_email: str):
        """Set user context for saving lists"""
        import os
        os.environ["VOTER_LIST_USER_ID"] = user_id
        os.environ["VOTER_LIST_USER_EMAIL"] = user_email