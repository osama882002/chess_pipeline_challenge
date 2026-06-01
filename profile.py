import os
import pandas as pd


def fetch_drive_data(url: str, local_filename: str) -> pd.DataFrame:
    local_path = os.path.join("data", "raw", local_filename)
    if os.path.exists(local_path):
        print(f"[+] Loading from local cache: {local_path}")
        return pd.read_csv(local_path)
    
    print(f"[!] Downloading {local_filename} from Google Drive...")
    try:
        file_id = url.split('/')[-2]
        direct_download_url = f'https://docs.google.com/uc?export=download&id={file_id}'
        df = pd.read_csv(direct_download_url)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        df.to_csv(local_path, index=False)
        return df
    except Exception as e:
        print(f"[-] Error downloading {local_filename}: {e}")
        return pd.DataFrame()

URL_CHESS_GAMES = 'https://drive.google.com/file/d/1eR3NZtwIC6ECN3vhtrynqmx8okG0twA7/view?usp=sharing'
URL_PLAYER_REGISTRY = 'https://drive.google.com/file/d/1wCSAkGagMzWiToedLC3ZGo_lGf_laF-k/view?usp=sharing'

print("=== STARTING THE PIPELINE CHALLENGE ===")
df_chess = fetch_drive_data(URL_CHESS_GAMES, "data/raw/chess_games.csv")
df_players = fetch_drive_data(URL_PLAYER_REGISTRY, "data/raw/player_registry.csv")


# STAGE 1: PROFILING 

print("\n" + "="*45 + "\n   STAGE 1: CHESS GAMES PROFILING\n" + "="*45)
print(f"    -> Available Columns in Chess Dataset: {df_chess.columns.tolist()}")
print(f"Q1: Number of records: {df_chess.shape[0]}")
print(f"Q2: Exact duplicate rows: {df_chess.duplicated().sum()}")
print(f"Q3: Games with duplicate move sequences: {df_chess.duplicated(subset=['moves']).sum()}")
print(f"Q4: Missing opening_response: {df_chess['opening_response'].isnull().mean() * 100:.2f}%")
print(f"Q5: Missing opening_variation: {df_chess['opening_variation'].isnull().mean() * 100:.2f}%")
print(f"Q6: Minimum number of turns: {df_chess['turns'].min()}")
print("    -> Why suspicious? Early forfeits/disconnects create noise (0-1 turns) and ruin analysis.")

#  Stage 2: Clean & Transform Pipeline
def clean_chess_pipeline(df: pd.DataFrame) -> pd.DataFrame:

    print("\n" + "="*55 + "\n   STAGE 2: BUILD clean_chess() PIPELINE\n" + "="*55)
    
    df_clean = df.drop_duplicates().copy()
    print(f"[+] Dropped exact duplicates. Remaining rows for pipeline: {df_clean.shape[0]}")
    
    df_clean[['time_base', 'time_inc']] = df_clean['time_increment'].str.split('+', expand=True).astype(int)
    print("[+] 2a: Parsed 'time_increment' into 'time_base' and 'time_inc'.")
    
    df_clean['rating_diff'] = df_clean['white_rating'] - df_clean['black_rating']
    print("[+] 2b: Added 'rating_diff' column.")
    
    df_clean['opening_family'] = df_clean['opening_fullname'].str.split(':').str[0].str.strip()
    print("[+] 2c: Extracted 'opening_family'.")
    
    df_clean = df_clean.drop(columns=['opening_response'])
    print("[+] 2d: Dropped high-null column 'opening_response'.")
    
    df_clean['is_suspicious'] = df_clean['turns'] < 5
    print("[+] 2e: Flagged short games (< 5 turns) in 'is_suspicious'.")
    
    assert df_clean['rating_diff'].notna().all(), "Validation Failed: rating_diff contains nulls!"
    assert df_clean.duplicated().sum() == 0, "Validation Failed: Dataset still contains duplicates!"
    print("[+] 2f: Validation Passed! (Asserts successful).")
    
    print("-" * 55)
    print("[+] Stage 2 Analytical Questions:")
    
    print(df_clean['winner'].value_counts())

    non_draw_games = df_clean[df_clean['winner'] != 'Draw']
    higher_rated_won = (
        ((non_draw_games['white_rating'] > non_draw_games['black_rating']) & (non_draw_games['winner'] == 'White')) |
        ((non_draw_games['black_rating'] > non_draw_games['white_rating']) & (non_draw_games['winner'] == 'Black'))
    )
    print(f"Q7: % of games the higher-rated player won (non-draw): {higher_rated_won.mean() * 100:.1f}%")
    
    print(f"Q8: Number of games flagged as suspicious (< 5 turns): {df_clean['is_suspicious'].sum()}")
    print("="*55)
    
    return df_clean

df_chess_clean = clean_chess_pipeline(df_chess)