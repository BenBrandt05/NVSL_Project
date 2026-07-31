#==========================================================================
# LIBRARIES
#==========================================================================
import pandas as pd
import numpy as np
from collections import defaultdict
from pathlib import Path

#==========================================================================
# PATH CONFIGURATION
#==========================================================================
data_directory = Path(__file__).parent.parent / 'Data'

#==========================================================================
# DATA CLEANING
#==========================================================================
def normalize(s):
    return ' '.join(s.strip().split()).lower()

def clean_team_name(team):
    return {
        "Bren Mar-Edsall Park": "Edsall Park",
        "Fair Oaks ": "Fair Oaks",
        "Brookfield ": "Brookfield",
        "Oakton ": "Oakton",
        "Kings Ridge ": "Kings Ridge",
    }.get(team, team.strip())

def load_and_parse(file_path):
    df = pd.read_csv(file_path, header=None)
    df.columns = ['First Team', 'First Week', 'Second Team', 'Second Week', 'Score']
    df = df.iloc[1:].drop_duplicates().reset_index(drop=True)
 
    matches = []
    for row in df.itertuples(index=False):
        csv_team1, csv_team2, score_str = row[0], row[2], row[4]

        csv_team1 = clean_team_name(csv_team1)
        csv_team2 = clean_team_name(csv_team2)
 
        if pd.isna(score_str):
            continue
 
        parts = score_str.split(' - ')
        if len(parts) != 2:
            continue
 
        part1, part2 = parts[0].split(), parts[1].split()
        if len(part1) < 2 or len(part2) < 2:
            continue
 
        try:
            score1, score2 = float(part1[0]), float(part2[0])
        except ValueError:
            continue
 
        label1 = clean_team_name(' '.join(part1[1:]))
        label2 = clean_team_name(' '.join(part2[1:]))
 
        if label1 == label2 or csv_team1 == csv_team2:
            continue
 
        if normalize(csv_team1) == normalize(label1) and normalize(csv_team2) == normalize(label2):
            score_a, score_b = score1, score2
        elif normalize(csv_team1) == normalize(label2) and normalize(csv_team2) == normalize(label1):
            score_a, score_b = score2, score1
        else:
            continue
 
        matches.append((csv_team1, csv_team2, score_a, score_b))
 
    return matches

#==========================================================================
# ELO CALCULATION
#==========================================================================
def run_elo(matches, initial_elo=1600, k=8):
    teams = set()
    for team_a, team_b, _, _ in matches:
        teams.add(team_a)
        teams.add(team_b)
    elo = {team: initial_elo for team in teams}
 
    for team_a, team_b, score_a, score_b in matches:
        elo_a, elo_b = elo[team_a], elo[team_b]
        expected_a = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
 
        if score_a > score_b:
            actual_a = 1
        elif score_a < score_b:
            actual_a = 0
        else:
            actual_a = 0.5
 
        delta = k * (actual_a - expected_a)
        elo[team_a] += delta
        elo[team_b] -= delta
 
    return {team: round(val, 0) for team, val in elo.items()}

#==========================================================================
# MULTI-YEAR PROCESSING
#==========================================================================                     
def process_year(file_path, num_iterations):
    year = file_path.stem.split("_")[-1]
 
    matches = load_and_parse(file_path)         
    matches = np.array(matches, dtype=object)
 
    avg_rankings = defaultdict(list)
    avg_elos = defaultdict(list)
 
    for i in range(num_iterations):
        rng = np.random.default_rng(i)
        rng.shuffle(matches)
        elo = run_elo(matches)
        sorted_elo = sorted(elo.items(), key=lambda x: x[1], reverse=True)
        for rank, (team, val) in enumerate(sorted_elo, start=1):
            avg_rankings[team].append(rank)
            avg_elos[team].append(val)
 
    final_avg_elos = {team: round(np.mean(vals), 2) for team, vals in avg_elos.items()}
    final_avg_rankings = {team: round(np.mean(vals), 2) for team, vals in avg_rankings.items()}
 
    sorted_teams = sorted(final_avg_elos.items(), key=lambda x: x[1], reverse=True)
 
    rows = []
    for rank, (team, avg_elo) in enumerate(sorted_teams, start=1):
        rows.append({
            'Year': year,
            'Rank': rank,
            'Team': team,
            'Average ELO': avg_elo,
            'Average Ranking': final_avg_rankings[team],
        })
 
    return pd.DataFrame(rows)

def process_all_years(num_iterations):
    data_files = sorted(data_directory.glob("results_*.csv"))

    if not data_files:
        print(f"No results files found in {data_directory}")
        return

    all_years = []
    for file_path in data_files:
        year = file_path.stem.split("_")[-1]
        print(f"Processing {year}...", end=" ", flush=True)
        df_results = process_year(file_path, num_iterations)
        all_years.append(df_results)
        print(f"done ({len(df_results)} teams)")

    combined = pd.concat(all_years, ignore_index=True)
    combined.to_csv(data_directory / "elo_all_years.csv", index=False)
    print(f"\nDone. Combined CSV saved to {data_directory / 'elo_all_years.csv'} ({len(combined)} total rows)")

#==========================================================================
# OVERALL RECORD MATRIX
#==========================================================================                   
def filter_csv(file_path):
    year = file_path.stem.split("_")[-1]
    year_df = pd.read_csv(file_path)
    year_df = year_df.replace(["Bren Mar-Edsall Park", "Fair Oaks ", "Brookfield ", "Oakton ", "Kings Ridge "],
                              ["Edsall Park", "Fair Oaks", "Brookfield", "Oakton", "Kings Ridge"])
    return year, year_df

def get_wins_losses(teams_history, team):
    num_wins = 0
    num_losses = 0
    for i in range(len(teams_history)):
        score = teams_history.loc[i]["Score"].rsplit("-", 1)
        if team in score[0]:
            num_wins += 1    
        else:
            num_losses += 1
            
    return num_wins, num_losses

def win_loss_matrix():
    years_csvs = sorted(data_directory.glob("results_*.csv"))
    
    elo_df = pd.read_csv(data_directory / "elo_all_years.csv")
    
    elo_df = elo_df.replace(
        ["Bren Mar-Edsall Park", "Fair Oaks ", "Brookfield ", "Oakton ", "Kings Ridge "],
        ["Edsall Park", "Fair Oaks", "Brookfield", "Oakton", "Kings Ridge"]
    )
    
    team_list = list(elo_df["Team"].drop_duplicates().sort_values())
    
    final_df = pd.DataFrame()
    final_df["Team"] = team_list
    
    for file_path in years_csvs:
        year, year_df = filter_csv(file_path)
        records = []
        for i in range(len(team_list)):
            teams_history = year_df[year_df["First Team"] == team_list[i]].reset_index(drop=True)
            wins, losses = get_wins_losses(teams_history, team_list[i])
            score_str = f"{wins}-{losses}"
            records.append({
                "Team": team_list[i],
                f"{year}": score_str})
            
        records_df = pd.DataFrame(records)    
        final_df = final_df.merge(records_df, on="Team", how="inner")
        print(f"Processed {year}")

    final_df.to_csv(data_directory / "all_records_matrix.csv", index=False)
    print("Win/Loss Matrix written to 'all_records_matrix.csv'")
              
#==========================================================================
# MAIN
#========================================================================== 
if __name__ == '__main__':    
    num_iterations = 100
    process_all_years(num_iterations)
    win_loss_matrix()

