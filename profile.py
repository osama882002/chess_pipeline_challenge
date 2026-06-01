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



# STAGE 1: PROFILING 

def profile_chess_data(df: pd.DataFrame):
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


# =========================================================================
# Stage 3: Analytical Questions
# =========================================================================
def analyze_stage_3(df: pd.DataFrame):
    """تنفيذ العمليات التحليلية والإحصائية المطلوبة في المرحلة الثالثة."""
    print("\n" + "="*55 + "\n   STAGE 3: ADVANCED ANALYTICAL QUESTIONS\n" + "="*55)
    
    # Q10: Win rate for White, Black, and Draw? (% of total games)
    print("Q10: Win rate (% of total games):")
    win_rates = df['winner'].value_counts(normalize=True) * 100
    for winner, rate in win_rates.items():
        print(f"     -> {winner}: {rate:.2f}%")
        
    # Q11: What is the most common way games end (victory_status)?
    victory_status = df['victory_status'].value_counts().idxmax()
    print(f"\nQ11: What is the most common way games end: {victory_status}")
    
    # Q12: Which victory_status has the highest average number of turns?
    highest_avg_turns_status = df.groupby('victory_status')['turns'].mean().idxmax()
    highest_avg_turns_val = df.groupby('victory_status')['turns'].mean().max()
    print(f"\nQ12: Victory status with highest average turns: {highest_avg_turns_status} ({highest_avg_turns_val:.1f} turns)")
    
    # Q13: Which opening family is most popular when Black wins? Same for White?
    black_wins_df = df[df['winner'] == 'Black']
    white_wins_df = df[df['winner'] == 'White']
    popular_opening_black = black_wins_df['opening_family'].value_counts().idxmax()
    popular_opening_white = white_wins_df['opening_family'].value_counts().idxmax()
    print(f"\nQ13: Most popular opening family:")
    print(f"     -> When White wins: {popular_opening_white}")
    print(f"     -> When Black wins: {popular_opening_black}")
    
    # Q14: Do rated games have a different White win rate than unrated games?
    print(f"\nQ14: White win rate comparison (Rated vs Unrated):")
    rated_comparison = df.groupby('rated')['winner'].apply(lambda x: (x == 'White').mean() * 100)
    print(f"     -> Rated Games (True): {rated_comparison.get(True, 0):.2f}%")
    print(f"     -> Unrated Games (False): {rated_comparison.get(False, 0):.2f}%")
    
    # Q15: Classify each game as Short/Medium/Long using apply(). What % is each?
    def classify_game_length(turns):
        if turns < 20:
            return 'Short'
        elif turns < 60:
            return 'Medium'
        return 'Long'
        
    df_analyzed = df.copy()
    df_analyzed['game_length'] = df_analyzed['turns'].apply(classify_game_length)
    
    print(f"\nQ15: Game length classification distribution (%):")
    length_dist = df_analyzed['game_length'].value_counts(normalize=True) * 100
    for length_cat, pct in length_dist.items():
        print(f"     -> {length_cat}: {pct:.2f}%")
        
    print("="*55)



if __name__ == "__main__":

    print("=== STARTING THE PIPELINE CHALLENGE ===")

    URL_CHESS_GAMES = 'https://drive.google.com/file/d/1eR3NZtwIC6ECN3vhtrynqmx8okG0twA7/view?usp=sharing'
    URL_PLAYER_REGISTRY = 'https://drive.google.com/file/d/1wCSAkGagMzWiToedLC3ZGo_lGf_laF-k/view?usp=sharing'

    df_chess = fetch_drive_data(URL_CHESS_GAMES, "data/raw/chess_games.csv")
    df_players = fetch_drive_data(URL_PLAYER_REGISTRY, "data/raw/player_registry.csv")

    profile_chess_data(df_chess)
    df_chess_clean = clean_chess_pipeline(df_chess)
    df_cleaned_final = clean_chess_pipeline(df_chess)
    analyze_stage_3(df_cleaned_final)    