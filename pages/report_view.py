import streamlit as st
from db.queries import generate_summary_report, get_logistics_records

if "role" not in st.session_state or st.session_state.role != "Admin":
    st.error("⛔ Access Denied: Admins only.")
    st.stop()

st.title("📊 Reports & Analytics")

# --- Summary Metrics ---
report = generate_summary_report()

st.metric("Total Orders", report["Total Orders"])
st.metric("Processed Orders", report["Processed Orders"])
st.metric("Low Stock Items", report["Low Stock Items"])
st.metric("Total Logistics Cost (₹)", f"{report['Total Logistics Cost']:.2f}")

# --- Logistics Cost Table ---
st.subheader("📦 Logistics Movements")

logistics = get_logistics_records()

if logistics:
    logistics_table = []
    total_cost = 0

    for record in logistics:
        sku, origin, destination, cost = record
        logistics_table.append({
            "SKU": sku,
            "From": origin,
            "To": destination,
            "Cost (₹)": f"{cost:.2f}",
        })
        total_cost += cost

    st.table(logistics_table)
    st.success(f"🧾 Total Logistics Cost: ₹{total_cost:.2f}")
else:
    st.info("No logistics records found.")
