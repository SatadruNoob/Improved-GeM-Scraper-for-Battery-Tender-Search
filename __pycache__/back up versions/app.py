# file: app.py

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import time
import sys
import os

# -------------------------------------------------
# Resolve BASE directory (exe-aware)
# -------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

# DEBUG: Write debug info
app_debug_path = BASE_DIR / "app_debug.log"
with open(app_debug_path, "w") as f:
    f.write(f"sys.frozen: {getattr(sys, 'frozen', False)}\n")
    f.write(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}\n")
    f.write(f"__file__: {__file__}\n")
    f.write(f"BASE_DIR: {BASE_DIR}\n")
    f.write(f"DATA_DIR: {DATA_DIR}\n")
    f.write(f"STATUS_FILE: {DATA_DIR / 'run_status.json'}\n")
    f.write(f"Working directory: {os.getcwd()}\n")

from backend_pipeline import (
    run_raw_extraction,
    prepare_analysis_excel,
    cancel_extraction,
    load_checked_bids,
    save_checked_bids,
    mark_bid_checked,
    unmark_bid_checked,
    is_bid_checked,
    get_checked_info
)

CSV_FILE = DATA_DIR / "gem_all_bids.csv"
EXCEL_FILE = DATA_DIR / "gem_bid_analysis.xlsx"
LOG_FILE = DATA_DIR / "scrape_status.log"
STATUS_FILE = DATA_DIR / "run_status.json"
CHECKED_BIDS_FILE = DATA_DIR / "checked_bids.json"
SHEET_NAME = "Target_Keyword_Bids"

st.set_page_config(
    page_title="GeM Bid Intelligence Dashboard",
    layout="wide"
)

# ────────────────────────────────────────
# Helpers
# ────────────────────────────────────────
def is_extraction_running():
    """Check if extraction is currently running by checking status file and session states"""
    if not Path(STATUS_FILE).exists():
        return False
    
    try:
        status_content = Path(STATUS_FILE).read_text().strip()
        if not status_content:
            return False
        
        status = json.loads(status_content)
        
        # Check extraction_status field
        extraction_status = status.get("extraction_status", "")
        if extraction_status in ["RUNNING", "MERGING"]:
            return True
        
        # Also check if any individual session is still running
        for i in range(1, 5):
            session_key = f"session{i}_status"
            if session_key in status:
                session_status = status[session_key].get("status", "")
                if session_status == "RUNNING":
                    return True
        
        return False
        
    except (json.JSONDecodeError, Exception):
        return False

def read_last_lines(path, n=50):
    if not Path(path).exists():
        return ["[waiting for logs…]"]
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()[-n:]

# ────────────────────────────────────────
# Custom CSS for highlighting checked rows
# ────────────────────────────────────────
st.markdown("""
<style>
    /* Make dataframe cells more readable */
    .stDataFrame {
        font-size: 14px;
    }
    
    /* Highlight for checked status badge */
    .checked-badge {
        background-color: #ffd700;
        color: #000;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    
    .unchecked-badge {
        background-color: #e8e8e8;
        color: #666;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────
# Session state initialization
# ────────────────────────────────────────
if "data_ready" not in st.session_state:
    st.session_state.data_ready = False

if "current_filter" not in st.session_state:
    st.session_state.current_filter = "All"

if "show_only_unchecked" not in st.session_state:
    st.session_state.show_only_unchecked = False

# ────────────────────────────────────────
# UI
# ────────────────────────────────────────
st.title("📊 GeM Bid Intelligence Dashboard")

# Last Run Status
st.subheader("🕐 Last Run Status")

# Initialize variables
extraction_status = "UNKNOWN"
status = {}
has_active_sessions = False

if Path(STATUS_FILE).exists():
    try:
        status_content = Path(STATUS_FILE).read_text().strip()
        if status_content:
            status = json.loads(status_content)
            extraction_status = status.get("extraction_status", "UNKNOWN")
            
            # Check if any session is running
            for i in range(1, 5):
                session_key = f"session{i}_status"
                if session_key in status:
                    session_status = status[session_key].get("status", "")
                    if session_status == "RUNNING":
                        has_active_sessions = True
                        break
    except json.JSONDecodeError:
        st.error("Status file contains invalid JSON. Please check the file.")
        st.code(Path(STATUS_FILE).read_text()[:500], language="text")
    except Exception as e:
        st.error(f"Error reading status file: {e}")

# Display status based on extraction status or active sessions
if extraction_status in ["RUNNING", "MERGING"] or has_active_sessions:
    st.info(f"🔄 **Extraction Status: {extraction_status if extraction_status != 'UNKNOWN' else 'RUNNING'}**")
    
    # Show progress for each session
    sessions_running = status.get("sessions_running", 0)
    sessions_completed = status.get("sessions_completed", 0)
    
    if sessions_running > 0:
        progress = sessions_completed / sessions_running
        st.progress(progress)
        st.write(f"**Sessions Progress:** {sessions_completed}/{sessions_running} completed")
    
    # Individual session details - ALWAYS SHOW IF ANY SESSION DATA EXISTS
    st.markdown("### 📋 Session Details")
    cols = st.columns(4)
    
    sessions_found = False
    for i in range(1, 5):
        session_key = f"session{i}_status"
        if session_key in status:
            sessions_found = True
            session_data = status[session_key]
            with cols[i-1]:
                session_status = session_data.get("status", "UNKNOWN")
                keyword = session_data.get("keyword", "N/A")
                
                if session_status == "COMPLETED":
                    st.success(f"✅ Session {i}")
                elif session_status == "RUNNING":
                    st.info(f"⏳ Session {i}")
                else:
                    st.warning(f"⚪ Session {i}")
                
                st.write(f"**Keyword:** {keyword}")
                
                if "pages_processed" in session_data:
                    st.write(f"Pages: {session_data['pages_processed']}")
                if "new_bids_found" in session_data:
                    st.write(f"New: {session_data['new_bids_found']}")
                if "total_bids_seen" in session_data:
                    st.write(f"Total: {session_data['total_bids_seen']}")
    
    if not sessions_found:
        st.info("⏳ Waiting for session data...")
    
    st.divider()
    
elif extraction_status == "COMPLETED":
    st.success("✅ **Extraction Completed Successfully**")
    if "total_unique_bids" in status:
        st.metric("Total Unique Bids", status["total_unique_bids"])
    
    # Show final session summary
    with st.expander("📋 View Session Summary", expanded=False):
        cols = st.columns(4)
        for i in range(1, 5):
            session_key = f"session{i}_status"
            if session_key in status:
                session_data = status[session_key]
                with cols[i-1]:
                    st.success(f"✅ Session {i}")
                    st.write(f"**Keyword:** {session_data.get('keyword', 'N/A')}")
                    if "total_pages" in session_data:
                        st.write(f"Pages: {session_data['total_pages']}")
                    if "total_new_bids" in session_data:
                        st.write(f"New: {session_data['total_new_bids']}")
                    if "final_bid_count" in session_data:
                        st.write(f"Total: {session_data['final_bid_count']}")
    
elif extraction_status == "CANCELLED":
    st.warning("🛑 **Extraction Cancelled**")
elif extraction_status == "FAILED":
    st.error("❌ **Extraction Failed**")
    if "error" in status:
        st.error(f"Error: {status['error']}")
else:
    if Path(STATUS_FILE).exists() and status:
        st.info("No active extraction sessions.")
    else:
        st.info("No run history available. Click 'Run 4 Parallel Scraping Sessions' to start.")

# Show full status JSON in expandable section
if status:
    with st.expander("🔍 View Full Status JSON"):
        st.json(status)

st.divider()

# ────────────────────────────────────────
# Controls
# ────────────────────────────────────────
st.subheader("⚙ Actions")

status_box = st.empty()
progress_bar = st.progress(0)

def update_status(msg, pct=None):
    status_box.info(msg)
    if pct is not None:
        progress_bar.progress(pct)

col1, col2, col3 = st.columns(3)

with col1:
    currently_running = is_extraction_running()
    if st.button(
        "▶ Run 4 Parallel Scraping Sessions",
        disabled=currently_running,
        help="Launch 4 parallel sessions with different keywords"
    ):
        st.write("🔄 Launching 4 parallel scraping sessions...")
        run_raw_extraction(progress_cb=update_status)
        st.write("✅ All sessions started. Watch the logs below.")

        time.sleep(4)
        st.rerun()

with col2:
    currently_running = is_extraction_running()
    if st.button(
        "⛔ Cancel All Sessions",
        disabled=not currently_running,
        help="Stop all running scraper sessions"
    ):
        if cancel_extraction():
            st.warning("All sessions cancelled.")
        else:
            st.error("No running sessions found.")
        time.sleep(2)
        st.rerun()

with col3:
    currently_running = is_extraction_running()
    if st.button(
        "📊 Prepare Analysis & Refresh Dashboard",
        disabled=currently_running,
        help="Merge session data, analyze, and update visualizations"
    ):
        with st.spinner("⏳ Processing..."):
            try:
                prepare_analysis_excel(progress_cb=update_status)
                st.session_state.data_ready = True
                st.success("✅ Analysis complete! Dashboard updated.")
                time.sleep(1)
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.error("Check logs for details.")
                time.sleep(2)
        st.rerun()

st.divider()

# ────────────────────────────────────────
# Live Log Streaming
# ────────────────────────────────────────
st.subheader("🟢 Live Scraper Status (Real-time)")

log_placeholder = st.empty()

# Display the last 60 lines of the log file
log_placeholder.code("".join(read_last_lines(LOG_FILE, n=60)), language="text")

st.divider()

# ────────────────────────────────────────
# Dashboard with Interactive Checking
# ────────────────────────────────────────
if st.session_state.data_ready and Path(EXCEL_FILE).exists():
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    
    # Load checked bids
    checked_bids = load_checked_bids()
    
    # Add checked status column to dataframe
    df['Checked'] = df['Bid No'].astype(str).apply(
        lambda x: '✅ Checked' if str(x) in checked_bids else '⬜ Not Checked'
    )
    
    # Add checked date column
    df['Checked On'] = df['Bid No'].astype(str).apply(
        lambda x: checked_bids.get(str(x), {}).get('checked_date', '') if str(x) in checked_bids else ''
    )
    
    st.subheader("📌 Summary by Keyword Group")
    
    # Summary metrics with checked status
    cols = st.columns(4)
    
    total_bids = len(df)
    total_checked = len([bid for bid in df['Bid No'].astype(str) if str(bid) in checked_bids])
    total_unchecked = total_bids - total_checked
    
    with cols[0]:
        st.metric("Total Bids", total_bids)
    with cols[1]:
        st.metric("✅ Checked", total_checked)
    with cols[2]:
        st.metric("⬜ Unchecked", total_unchecked)
    with cols[3]:
        completion_pct = (total_checked / total_bids * 100) if total_bids > 0 else 0
        st.metric("Completion", f"{completion_pct:.1f}%")
    
    st.divider()
    
    # Filter controls
    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])
    
    with col_filter1:
        selected_group = st.selectbox(
            "🔍 Filter by Keyword Group",
            options=["All"] + sorted(df["Keyword Group"].unique()),
            key="keyword_group_filter"
        )
    
    with col_filter2:
        check_filter = st.selectbox(
            "✅ Filter by Check Status",
            options=["All", "Checked Only", "Unchecked Only"],
            key="check_status_filter"
        )
    
    with col_filter3:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("🔄 Refresh Data", help="Reload the data from Excel"):
            st.rerun()
    
    # Apply filters
    df_view = df.copy()
    
    if selected_group != "All":
        df_view = df_view[df_view["Keyword Group"] == selected_group]
    
    if check_filter == "Checked Only":
        df_view = df_view[df_view['Checked'] == '✅ Checked']
    elif check_filter == "Unchecked Only":
        df_view = df_view[df_view['Checked'] == '⬜ Not Checked']
    
    st.markdown(f"### 📋 Showing {len(df_view)} of {len(df)} bids")
    
    # Display dataframe with styled columns
    display_columns = [
        "Bid No",
        "Checked",
        "Checked On",
        "Items",
        "Quantity",
        "Keyword Group",
        "Department Name And Address",
        "Start Date",
        "End Date",
        "New Today",
        "End Date Changed"
    ]
    
    # Create a styled dataframe
    def highlight_checked_rows(row):
        if row['Checked'] == '✅ Checked':
            return ['background-color: #fffacd'] * len(row)  # Light yellow
        return [''] * len(row)
    
    styled_df = df_view[display_columns].style.apply(highlight_checked_rows, axis=1)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400
    )
    
    st.divider()
    
    # ────────────────────────────────────────
    # Interactive Bid Checking Section
    # ────────────────────────────────────────
    st.subheader("✅ Mark Bids as Checked")
    
    col_check1, col_check2 = st.columns([3, 1])
    
    with col_check1:
        st.markdown("""
        **How to use:**
        - Select bid(s) from the dropdown below
        - Click "Mark as Checked" to tag them (they'll turn yellow)
        - Click "Unmark Selected" to remove the check tag
        - Checked bids persist across sessions
        """)
    
    with col_check2:
        # Bulk operations
        if st.button("✅ Mark All Visible as Checked", help="Mark all currently filtered bids as checked"):
            for bid_no in df_view['Bid No'].astype(str):
                mark_bid_checked(bid_no)
            st.success(f"Marked {len(df_view)} bids as checked!")
            time.sleep(1)
            st.rerun()
    
    # Multi-select for bids
    bid_options = []
    for idx, row in df_view.iterrows():
        bid_no = row['Bid No']
        items = str(row['Items'])[:60]
        bid_options.append(f"{bid_no} - {items}...")
    
    bid_to_items_map = dict(zip(
        df_view['Bid No'].astype(str),
        df_view['Items']
    ))
    
    selected_bids_display = st.multiselect(
        "Select Bid(s) to Mark/Unmark",
        options=bid_options,
        help="You can select multiple bids"
    )
    
    # Extract actual bid numbers from selections
    selected_bid_nos = [item.split(' - ')[0] for item in selected_bids_display]
    
    if selected_bid_nos:
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("✅ Mark as Checked", type="primary"):
                for bid_no in selected_bid_nos:
                    mark_bid_checked(bid_no)
                st.success(f"Marked {len(selected_bid_nos)} bid(s) as checked!")
                time.sleep(1)
                st.rerun()
        
        with col_btn2:
            if st.button("❌ Unmark Selected"):
                for bid_no in selected_bid_nos:
                    unmark_bid_checked(bid_no)
                st.info(f"Unmarked {len(selected_bid_nos)} bid(s)")
                time.sleep(1)
                st.rerun()
        
        with col_btn3:
            # Show details of selected bids
            st.write(f"**Selected:** {len(selected_bid_nos)} bid(s)")
    
    st.divider()
    
    # ────────────────────────────────────────
    # Quick Stats by Keyword Group
    # ────────────────────────────────────────
    st.subheader("📊 Check Status by Keyword Group")
    
    group_stats = []
    for group in sorted(df["Keyword Group"].unique()):
        group_df = df[df["Keyword Group"] == group]
        total = len(group_df)
        checked = len([bid for bid in group_df['Bid No'].astype(str) if str(bid) in checked_bids])
        unchecked = total - checked
        pct = (checked / total * 100) if total > 0 else 0
        
        group_stats.append({
            'Keyword Group': group,
            'Total': total,
            'Checked': checked,
            'Unchecked': unchecked,
            'Completion %': f"{pct:.1f}%"
        })
    
    stats_df = pd.DataFrame(group_stats)
    st.dataframe(stats_df, use_container_width=True)
    
    st.divider()
    
    # Download buttons
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    
    with col_dl1:
        # Download filtered data
        csv_data = df_view.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv_data,
            file_name=f"gem_bids_{selected_group.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )
    
    with col_dl2:
        # Download checked bids only
        checked_df = df[df['Checked'] == '✅ Checked']
        if len(checked_df) > 0:
            checked_csv = checked_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Checked Bids (CSV)",
                data=checked_csv,
                file_name="gem_bids_checked.csv",
                mime="text/csv"
            )
    
    with col_dl3:
        # Download unchecked bids only
        unchecked_df = df[df['Checked'] == '⬜ Not Checked']
        if len(unchecked_df) > 0:
            unchecked_csv = unchecked_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Unchecked Bids (CSV)",
                data=unchecked_csv,
                file_name="gem_bids_unchecked.csv",
                mime="text/csv"
            )

else:
    st.info("Run extraction and analysis to populate the dashboard.")
    
    # Show info about the 4 session approach
    with st.expander("ℹ️ How does parallel scraping work?"):
        st.markdown("""
        ### 4-Session Parallel Scraping
        
        When you click **"Run 4 Parallel Scraping Sessions"**, the system:
        
        1. **Launches 4 independent browser sessions** simultaneously
        2. Each session searches with a different keyword:
           - Session 1: "battery"
           - Session 2: "batter"
           - Session 3: "lead acid"
           - Session 4: "traction"
        3. Each session writes to its own CSV file (`session1.csv`, `session2.csv`, etc.)
        4. **Data integrity is maintained** - each session tracks its own state
        5. **Process isolation** - sessions run independently and can't interfere with each other
        6. Once all 4 sessions complete, the system automatically:
           - **Merges** all 4 CSV files into one master file
           - **Removes duplicates** based on Bid No (keeping latest End Date)
           - **Preserves First Seen Date** from earliest occurrence
        7. The merged, deduplicated data is ready for analysis
        
        **Benefits:**
        - 🚀 **4x faster** data collection
        - 🔍 **Broader coverage** with multiple search terms
        - 🛡️ **No data loss** - deduplication preserves all unique bids
        - 🔄 **Reliable** - each session is independent
        """)
    
    with st.expander("✅ How does bid checking work?"):
        st.markdown("""
        ### Interactive Bid Checking System
        
        **Purpose:** Track which bids you've already reviewed to avoid re-checking the same bids daily.
        
        **How it works:**
        1. After running analysis, bids appear in the dashboard
        2. Select bid(s) you want to mark as "checked"
        3. Click "Mark as Checked" - they turn **yellow** and show a ✅
        4. The check status is **saved permanently** in `checked_bids.json`
        5. Next day when you run the scraper again:
           - Previously checked bids remain marked (yellow)
           - New bids appear unmarked (white)
           - You can instantly see which bids need review
        
        **Features:**
        - ✅ **Persistent tracking** - checks survive across sessions
        - 🎨 **Visual highlighting** - yellow background for checked bids
        - 📊 **Progress tracking** - see completion % for each category
        - 🔍 **Smart filtering** - show only checked/unchecked bids
        - 📥 **Separate exports** - download checked/unchecked bids separately
        
        **The system does NOT modify your scraping data** - it maintains a separate tracking file.
        """)

# ────────────────────────────────────────
# AUTO-REFRESH LOGIC (must be at the very end)
# ────────────────────────────────────────
# Check if extraction is running and refresh page every 2 seconds
if is_extraction_running():
    time.sleep(2)
    st.rerun()