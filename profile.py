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
