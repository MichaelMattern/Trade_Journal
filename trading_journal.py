# app.py

import streamlit as st
import sqlite3
import json
import tempfile
from datetime import datetime
from pathlib import Path

# ─── IMPORT THE PARSER FROM formatter.py ────────────────────────────────────────
from formatter import parse_trade_file

# ─── CONSTANTS ─────────────────────────────────────────────────────────────────

DB_PATH = Path("trades.db")   # SQLite file in the same folder as app.py

# ─── DATABASE SETUP ────────────────────────────────────────────────────────────

def init_db():
    """
    Create the trades table if it doesn’t already exist.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            header TEXT,
            total_cost TEXT,
            quantity_price TEXT,
            type TEXT,
            position_effect TEXT,
            time_in_force TEXT,
            submitted TEXT,
            quantity TEXT,
            account TEXT,
            status TEXT,
            filled_quantity TEXT,
            filled TEXT,
            limit_price TEXT,
            est_cost TEXT,
            est_reg_fees TEXT,
            suggestion TEXT,
            comment TEXT,
            saved_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def insert_trade(record: dict):
    """
    Insert one trade record (including suggestion/comment) into the database.
    Keys in `record` must exactly match the column names (except id).
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO trades (
            header, total_cost, quantity_price, type, position_effect,
            time_in_force, submitted, quantity, account, status,
            filled_quantity, filled, limit_price, est_cost, est_reg_fees,
            suggestion, comment, saved_at
        ) VALUES (
            :header, :total_cost, :quantity_price, :type, :position_effect,
            :time_in_force, :submitted, :quantity, :account, :status,
            :filled_quantity, :filled, :limit_price, :est_cost, :est_reg_fees,
            :suggestion, :comment, :saved_at
        )
        """,
        record
    )
    conn.commit()
    conn.close()

def fetch_all_trades():
    """
    Return a list of all saved trades as dicts (ordered by saved_at DESC).
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM trades ORDER BY saved_at DESC")
    rows = c.fetchall()
    colnames = [desc[0] for desc in c.description]
    conn.close()
    trade_dicts = []
    for row in rows:
        trade_dicts.append({colnames[i]: row[i] for i in range(len(colnames))})
    return trade_dicts

# ─── STREAMLIT APP LAYOUT ───────────────────────────────────────────────────────

st.set_page_config(page_title="Trade Journal Dashboard", layout="wide")
st.title("📔 Trade Journal Dashboard")

# Initialize the DB on first run
init_db()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1: UPLOAD JSON FILES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.header("1. Upload Trade JSON Files")
uploaded_json = st.file_uploader(
    label="Select one or more trade JSON files",
    type=["json"],
    accept_multiple_files=True,
    help="Each JSON should be either a single trade object or a list of trade objects."
)

if uploaded_json:
    for uploaded in uploaded_json:
        try:
            raw = uploaded.read().decode("utf-8")
            parsed_json = json.loads(raw)
        except Exception as e:
            st.error(f"❌ Could not parse {uploaded.name} as JSON: {e}")
            continue

        # Ensure we always have a list of trade‐dicts
        if isinstance(parsed_json, dict):
            trades_list = [parsed_json]
        elif isinstance(parsed_json, list):
            trades_list = parsed_json
        else:
            st.error(f"❌ {uploaded.name} does not contain a JSON object or array.")
            continue

        expected_keys = {
            "header", "Total Cost", "Quantity + Price", "Type", "Position effect",
            "Time in force", "Submitted", "Quantity", "Account", "Status",
            "Filled quantity", "Filled", "Limit price", "Est cost", "Est regulatory fees"
        }

        for idx, trade_data in enumerate(trades_list):
            st.markdown("---")
            st.markdown(f"#### File: **{uploaded.name}** | Trade #{idx + 1}")

            missing = expected_keys - set(trade_data.keys())
            if missing:
                st.warning(f"Trade #{idx + 1} is missing fields: {', '.join(missing)}")

            col1, col2 = st.columns(2)
            prefix = f"{uploaded.name}_json_trade{idx}"

            with col1:
                hdr = st.text_input("Header", value=trade_data.get("header", ""), key=f"hdr_{prefix}")
                tc = st.text_input("Total Cost", value=trade_data.get("Total Cost", ""), key=f"tc_{prefix}")
                qp = st.text_input("Quantity + Price", value=trade_data.get("Quantity + Price", ""), key=f"qp_{prefix}")
                tp = st.text_input("Type", value=trade_data.get("Type", ""), key=f"type_{prefix}")
                peff = st.text_input("Position effect", value=trade_data.get("Position effect", ""), key=f"peff_{prefix}")
                tif = st.text_input("Time in force", value=trade_data.get("Time in force", ""), key=f"tif_{prefix}")
                subm = st.text_input("Submitted", value=trade_data.get("Submitted", ""), key=f"sub_{prefix}")

            with col2:
                qty = st.text_input("Quantity", value=trade_data.get("Quantity", ""), key=f"qty_{prefix}")
                acct = st.text_input("Account", value=trade_data.get("Account", ""), key=f"acct_{prefix}")
                stat = st.text_input("Status", value=trade_data.get("Status", ""), key=f"stat_{prefix}")
                fq = st.text_input("Filled quantity", value=trade_data.get("Filled quantity", ""), key=f"fq_{prefix}")
                filled_time = st.text_input("Filled", value=trade_data.get("Filled", ""), key=f"filled_{prefix}")
                lp = st.text_input("Limit price", value=trade_data.get("Limit price", ""), key=f"lp_{prefix}")
                ec = st.text_input("Est cost", value=trade_data.get("Est cost", ""), key=f"ec_{prefix}")
                erf = st.text_input("Est regulatory fees", value=trade_data.get("Est regulatory fees", ""), key=f"erf_{prefix}")

            suggestion = st.text_area(
                "Suggestion (e.g., lessons learned, trade improvement ideas)",
                key=f"sugg_{prefix}"
            )
            comment = st.text_area(
                "Comment (any additional notes you want to store)",
                key=f"comm_{prefix}"
            )

            if st.button(f"Save JSON Trade #{idx + 1} from {uploaded.name}"):
                # Build record by preferring any edited value in session_state, otherwise fallback to trade_data
                record = {
                    "header": st.session_state.get(f"hdr_{prefix}", trade_data.get("header", "")),
                    "total_cost": st.session_state.get(f"tc_{prefix}", trade_data.get("Total Cost", "")),
                    "quantity_price": st.session_state.get(f"qp_{prefix}", trade_data.get("Quantity + Price", "")),
                    "type": st.session_state.get(f"type_{prefix}", trade_data.get("Type", "")),
                    "position_effect": st.session_state.get(f"peff_{prefix}", trade_data.get("Position effect", "")),
                    "time_in_force": st.session_state.get(f"tif_{prefix}", trade_data.get("Time in force", "")),
                    "submitted": st.session_state.get(f"sub_{prefix}", trade_data.get("Submitted", "")),
                    "quantity": st.session_state.get(f"qty_{prefix}", trade_data.get("Quantity", "")),
                    "account": st.session_state.get(f"acct_{prefix}", trade_data.get("Account", "")),
                    "status": st.session_state.get(f"stat_{prefix}", trade_data.get("Status", "")),
                    "filled_quantity": st.session_state.get(f"fq_{prefix}", trade_data.get("Filled quantity", "")),
                    "filled": st.session_state.get(f"filled_{prefix}", trade_data.get("Filled", "")),
                    "limit_price": st.session_state.get(f"lp_{prefix}", trade_data.get("Limit price", "")),
                    "est_cost": st.session_state.get(f"ec_{prefix}", trade_data.get("Est cost", "")),
                    "est_reg_fees": st.session_state.get(f"erf_{prefix}", trade_data.get("Est regulatory fees", "")),
                    "suggestion": suggestion,
                    "comment": comment,
                    "saved_at": datetime.now().isoformat()
                }
                insert_trade(record)
                st.success(f"✅ JSON Trade #{idx + 1} from {uploaded.name} saved to journal.")

    st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1b: UPLOAD TXT FILES (using parse_trade_file from formatter.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.header("1b. Upload Trade TXT Files")
uploaded_txt = st.file_uploader(
    label="Select one or more trade TXT files",
    type=["txt"],
    accept_multiple_files=True,
    key="txt_uploader",
    help="Each .txt should follow your block format: header, cost, quantity+price, then label/value pairs."
)

if uploaded_txt:
    for uploaded in uploaded_txt:
        # Save uploaded file to a temporary path so parse_trade_file can read it
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            tmp_file.write(uploaded.read())
            tmp_file.flush()
            tmp_file_path = tmp_file.name
            tmp_file.close()
        except Exception as e:
            st.error(f"❌ Could not write {uploaded.name} to temp file: {e}")
            continue

        # Now call parse_trade_file(...) on the temp path
        trades_list = parse_trade_file(tmp_file_path)

        if not trades_list:
            st.warning(f"No valid trade blocks found in {uploaded.name}.")
            continue

        expected_keys = {
            "header", "Total Cost", "Quantity + Price", "Type", "Position effect",
            "Time in force", "Submitted", "Quantity", "Account", "Status",
            "Filled quantity", "Filled", "Limit price", "Est cost", "Est regulatory fees"
        }

        for idx, trade_data in enumerate(trades_list):
            st.markdown("---")
            st.markdown(f"#### File: **{uploaded.name}** | TXT Trade #{idx + 1}")

            missing = expected_keys - set(trade_data.keys())
            if missing:
                st.warning(f"TXT Trade #{idx + 1} is missing fields: {', '.join(missing)}")

            col1, col2 = st.columns(2)
            prefix = f"{uploaded.name}_txt_trade{idx}"

            with col1:
                hdr = st.text_input("Header", value=trade_data.get("header", ""), key=f"hdr_{prefix}")
                tc = st.text_input("Total Cost", value=trade_data.get("Total Cost", ""), key=f"tc_{prefix}")
                qp = st.text_input("Quantity + Price", value=trade_data.get("Quantity + Price", ""), key=f"qp_{prefix}")
                tp = st.text_input("Type", value=trade_data.get("Type", ""), key=f"type_{prefix}")
                peff = st.text_input("Position effect", value=trade_data.get("Position effect", ""), key=f"peff_{prefix}")
                tif = st.text_input("Time in force", value=trade_data.get("Time in force", ""), key=f"tif_{prefix}")
                subm = st.text_input("Submitted", value=trade_data.get("Submitted", ""), key=f"sub_{prefix}")

            with col2:
                qty = st.text_input("Quantity", value=trade_data.get("Quantity", ""), key=f"qty_{prefix}")
                acct = st.text_input("Account", value=trade_data.get("Account", ""), key=f"acct_{prefix}")
                stat = st.text_input("Status", value=trade_data.get("Status", ""), key=f"stat_{prefix}")
                fq = st.text_input("Filled quantity", value=trade_data.get("Filled quantity", ""), key=f"fq_{prefix}")
                filled_time = st.text_input("Filled", value=trade_data.get("Filled", ""), key=f"filled_{prefix}")
                lp = st.text_input("Limit price", value=trade_data.get("Limit price", ""), key=f"lp_{prefix}")
                ec = st.text_input("Est cost", value=trade_data.get("Est cost", ""), key=f"ec_{prefix}")
                erf = st.text_input("Est regulatory fees", value=trade_data.get("Est regulatory fees", ""), key=f"erf_{prefix}")

            suggestion = st.text_area(
                "Suggestion (e.g., lessons learned, trade improvement ideas)",
                key=f"sugg_{prefix}"
            )
            comment = st.text_area(
                "Comment (any additional notes you want to store)",
                key=f"comm_{prefix}"
            )

            if st.button(f"Save TXT Trade #{idx + 1} from {uploaded.name}"):
                # Build record by preferring any edited value; fallback to the parsed TXT data
                record = {
                    "header": st.session_state.get(f"hdr_{prefix}", trade_data.get("header", "")),
                    "total_cost": st.session_state.get(f"tc_{prefix}", trade_data.get("Total Cost", "")),
                    "quantity_price": st.session_state.get(f"qp_{prefix}", trade_data.get("Quantity + Price", "")),
                    "type": st.session_state.get(f"type_{prefix}", trade_data.get("Type", "")),
                    "position_effect": st.session_state.get(f"peff_{prefix}", trade_data.get("Position effect", "")),
                    "time_in_force": st.session_state.get(f"tif_{prefix}", trade_data.get("Time in force", "")),
                    "submitted": st.session_state.get(f"sub_{prefix}", trade_data.get("Submitted", "")),
                    "quantity": st.session_state.get(f"qty_{prefix}", trade_data.get("Quantity", "")),
                    "account": st.session_state.get(f"acct_{prefix}", trade_data.get("Account", "")),
                    "status": st.session_state.get(f"stat_{prefix}", trade_data.get("Status", "")),
                    "filled_quantity": st.session_state.get(f"fq_{prefix}", trade_data.get("Filled quantity", "")),
                    "filled": st.session_state.get(f"filled_{prefix}", trade_data.get("Filled", "")),
                    "limit_price": st.session_state.get(f"lp_{prefix}", trade_data.get("Limit price", "")),
                    "est_cost": st.session_state.get(f"ec_{prefix}", trade_data.get("Est cost", "")),
                    "est_reg_fees": st.session_state.get(f"erf_{prefix}", trade_data.get("Est regulatory fees", "")),
                    "suggestion": suggestion,
                    "comment": comment,
                    "saved_at": datetime.now().isoformat()
                }
                insert_trade(record)
                st.success(f"✅ TXT Trade #{idx + 1} from {uploaded.name} saved to journal.")

        # (Optional) Clean up the temporary file if you want
        # os.remove(tmp_file_path)

    st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2: VIEW SAVED TRADES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.header("2. Saved Trades")
trades = fetch_all_trades()

if not trades:
    st.info("No trades have been saved yet. Upload a JSON or TXT file above and click its Save button.")
else:
    from pandas import DataFrame

    # Show every column for verification
    df = DataFrame(
        [
            {
                "Saved At": t["saved_at"],
                "Header": t["header"],
                "Total Cost": t["total_cost"],
                "Quantity+Price": t["quantity_price"],
                "Type": t["type"],
                "Position effect": t["position_effect"],
                "Time in force": t["time_in_force"],
                "Submitted": t["submitted"],
                "Quantity": t["quantity"],
                "Account": t["account"],
                "Status": t["status"],
                "Filled qty": t["filled_quantity"],
                "Filled": t["filled"],
                "Limit price": t["limit_price"],
                "Est cost": t["est_cost"],
                "Est reg fees": t["est_reg_fees"],
                "Suggestion": t["suggestion"],
                "Comment": t["comment"],
            }
            for t in trades
        ]
    )
    st.dataframe(df, use_container_width=True)

st.markdown(
    """
    **How it works under the hood:**  
    1. **Uploading JSON files**  
       - You can upload one or more `.json` files (each file can contain a single object or a list of objects).  
       - For each trade in each file, we display all the fields in two columns (pre‐filled from JSON).  
       - You can edit any field, add a “Suggestion” and a “Comment,” then click **Save**.  
       - We assemble a `record` dict by preferring any edited values from `st.session_state`, else we fall back to the original JSON.  
       - That `record` (with all fields) is inserted into `trades.db`.  

    2. **Uploading TXT files**  
       - You can upload one or more `.txt` files following your block format. Each block is separated by at least one blank line.  
       - We save each uploaded file to a temp path (e.g. via `NamedTemporaryFile`).  
       - We call `parse_trade_file(path)` (from `formatter.py`), which:  
         - Splits on blank lines to isolate each trade block.  
         - Reads the first line as `"header"`, second as `"Total Cost"`, third as `"Quantity + Price"`.  
         - Then scans for each label (e.g. `"Type"`, `"Position effect"`, etc.) and pulls its value from the next line.  
       - Once parsed, each trade gets shown in the same two‐column inputs plus “Suggestion” & “Comment.”  
       - Clicking **Save** builds a `record` that preferentially takes any edited field from `session_state`, or else uses the parsed TXT value.  
       - That `record` is then written to `trades.db`.  

    3. **Viewing saved trades**  
       - Under “Saved Trades,” you’ll see a DataFrame of every row in `trades.db`, showing each column (header, cost, quantity/price, type, etc.), plus your “Suggestion” and “Comment.”  

    You now have a single Streamlit app where JSON and TXT files produce identical workflows—TXT files get funneled through your existing `parse_trade_file` logic for normalization, and JSON files skip straight to the UI.  
    """
)
