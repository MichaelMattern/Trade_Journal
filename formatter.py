import json
import os
import re

def parse_trade_file(path):
    """
    Reads a .txt file containing one or more trades (separated by at least one blank line)
    and returns a list of dictionaries, each matching the requested JSON structure.
    """
    labels = [
        "Type",
        "Position effect",
        "Time in force",
        "Submitted",
        "Quantity",
        "Account",
        "Status",
        "Filled quantity",
        "Filled",
        "Limit price",
        "Est cost",
        "Est regulatory fees"
    ]

    # 1) Read entire file as text
    with open(path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # 2) Split into blocks wherever there are one or more blank lines.
    #    (r'\n\s*\n+' matches at least two consecutive newlines, possibly with spaces/tabs in between)
    trade_blocks = re.split(r'\n\s*\n+', raw_text.strip())

    all_trades = []

    for block in trade_blocks:
        # 3) Split block into individual lines, strip each line, and drop blank lines
        raw_lines = [line.strip() for line in block.splitlines()]
        lines = [line for line in raw_lines if line]

        # 4) Drop any line containing “·” (e.g., "Individual · Jun 2")
        lines = [line for line in lines if "·" not in line]

        # If there are fewer than 3 lines, it can't be a valid trade—skip it
        if len(lines) < 3:
            continue

        parsed = {}

        # 5) First line is the header (e.g. "Buy SPY $645 Call 7/31")
        parsed["header"] = lines[0]

        # 6) Second line is Total Cost (e.g. "$94.00")
        parsed["Total Cost"] = lines[1]

        # 7) Third line is Quantity + Price (e.g. "2 contracts at $0.47")
        parsed["Quantity + Price"] = lines[2]

        # 8) Everything from index 3 onward: look for each label and grab the next line
        idx = 3
        for label in labels:
            # Advance idx until it either matches the label or runs out
            while idx < len(lines) and lines[idx] != label:
                idx += 1

            # If we found the label and there is a next line, capture it
            if idx < len(lines) and lines[idx] == label and (idx + 1) < len(lines):
                parsed[label] = lines[idx + 1]
                idx += 2
            else:
                # Label not found or no line after it; just move on
                idx += 1

        all_trades.append(parsed)

    return all_trades


if __name__ == "__main__":
    # Replace this with the path to your multi‐trade .txt file:
    spyc_path = "trade_order_raw.txt"

    # Parse all trades in the file
    result = parse_trade_file(spyc_path)

    # Derive the JSON filename: replace .txt with .json
    base, ext = os.path.splitext(spyc_path)
    json_path = base + ".json"

    # Write the list of trade‐dictionaries out to <same_base>.json
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(result, jf, indent=4)

    print(f"Parsed {len(result)} trade(s) saved to: {json_path}")
