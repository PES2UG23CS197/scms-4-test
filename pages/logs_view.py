import streamlit as st
from db.queries import get_logs, reset_simulation

if "role" not in st.session_state or st.session_state.role != "Admin":
    st.error("⛔ Access Denied: Admins only.")
    st.stop()

st.title("📝 Logs Viewer")

# --- Logs Table ---
st.subheader("System Logs")

logs = get_logs()

if logs:
    log_table = []
    for log in logs:
        user_id, action = log
        log_table.append({
            "User ID": user_id,
            "Action": action
        })
    st.table(log_table)
else:
    st.info("No logs available.")

# --- Reset Button ---
st.subheader("🧹 Reset Simulation")

if st.button("Reset All Data"):
    reset_simulation()
    st.success("✅ Simulation has been reset to its initial state.")
