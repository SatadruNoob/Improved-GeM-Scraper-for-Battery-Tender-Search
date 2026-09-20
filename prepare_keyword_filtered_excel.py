# file: prepare_keyword_filtered_excel.py

import pandas as pd
import re

INPUT_CSV = "gem_all_bids.csv"
OUTPUT_XLSX = "gem_bid_analysis.xlsx"

TARGET_KEYWORDS = [
    "plante",
    "lead acid",
    "1652",
    "traction batter",
    "5154",
    "diesel loco",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower())


def keyword_match(items: str) -> bool:
    text = normalize(items)
    return any(keyword in text for keyword in TARGET_KEYWORDS)


def main():
    df = pd.read_csv(INPUT_CSV)

    # Ensure Items column exists
    df["Items"] = df["Items"].fillna("")

    # Apply keyword filter
    df["Keyword Match"] = df["Items"].apply(keyword_match)
    df_filtered = df[df["Keyword Match"]].drop(columns=["Keyword Match"])

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="All_Bids", index=False)
        df_filtered.to_excel(writer, sheet_name="Target_Keyword_Bids", index=False)

    print(f"[✓] Excel created: {OUTPUT_XLSX}")
    print(f"[✓] Total bids: {len(df)}")
    print(f"[✓] Keyword-matched bids: {len(df_filtered)}")


if __name__ == "__main__":
    main()
