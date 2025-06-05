# Trade Journal Dashboard (Streamlit + Formatter Script)
- **Upload trade JSON**  
  - Accepts one or more `.json` files.  
  - Each file can be a single trade object or an array of trade objects.  
  - Displays all trade fields in editable text inputs.  
  - Allows you to add a “Suggestion” and a “Comment” for each trade.  
  - Saves each record (with edits, suggestions, comments, and timestamp) into an SQLite database (`trades.db`).

- **Upload trade TXT**  
  - Accepts one or more `.txt` files following a simple “block” format (header, cost, qty/price, then label/value pairs separated by blank lines).  
  - Internally calls `parse_trade_file(...)` (from `formatter.py`) to convert each `.txt` block into a Python dictionary.  
  - Shows the parsed fields in the same two-column edit UI (just like JSON).  
  - Allows “Suggestion” and “Comment” fields.  
  - Saves the final record into `trades.db`.

- **View saved trades**  
  - Displays an interactive DataFrame (via Streamlit) of all rows in `trades.db`, in descending order of save time.  
  - Shows every column: trade metadata plus suggestion/comment.

- **Project File Structure**
  - app.py
  - formatter.py
  - requirements.txt
  - trades.db (optional: gets created on first run)

- **Python Libraries**
  - pip install streamlit pandas
