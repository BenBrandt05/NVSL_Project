# =============================================================================
# LIBRARIES
# =============================================================================
import asyncio
import aiohttp
import csv
import os
import time
import threading
from bs4 import BeautifulSoup
import requests

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_directory = os.path.join(project_root, 'Data')

csv_lock = threading.Lock()

BASE_URL = "https://www.mynvsl.com/virtual-meet"

# =============================================================================
# FORM METADATA
# =============================================================================

def fetch_form_metadata(year_name):    
    s = requests.Session()
    resp = s.get(BASE_URL, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")

    hidden_fields = {
        inp["name"]: inp.get("value", "")
        for inp in soup.select("form input[type=hidden]")
        if inp.get("name")
    }

    headers = {
    "Referer": "https://www.mynvsl.com/virtual-meet",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    teams_resp = s.post("https://www.mynvsl.com/ajax/virtualmeet/GetTeams",
                        headers=headers,
                        data={"year": year_name})
    
    teams_data = teams_resp.json()["Data"]
    team_map = {
        item["text"]: item["id"] for item in teams_data if item["id"] and item["text"]
    }

    sample_team_id = next(iter(team_map.values()))

    dates_resp = s.post("https://www.mynvsl.com/ajax/virtualmeet/GetMeetDates",
                        headers=headers,
                        data={"year": year_name, "team": sample_team_id})

    dates_data = dates_resp.json()["Data"]
    date_value_list = [item["Value"] for item in dates_data if item["Value"] and item["Text"]]
    
    date_map = {
        f"Week{i+1}": val
        for i, val in enumerate(date_value_list)
    }

    return hidden_fields, team_map, date_map, date_value_list

# =============================================================================
# PROGRESS TRACKING
# =============================================================================

def save_progress(global_index, total_time_elapsed, total_errors):
    file_path = os.path.join(data_directory, f'progress.csv')
    with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([global_index, total_time_elapsed, total_errors])

def load_progress():
    file_path = os.path.join(data_directory, f'progress.csv')
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
        if rows:
            return int(rows[0][0]), float(rows[0][1]), int(rows[0][2])
    except Exception:
        pass
    return 0, 0.0, 0

# =============================================================================
# MATCH GENERATION
# =============================================================================

def generate_matches(num_teams, num_weeks):
    matches = []
    for h in range(1, num_teams + 1):
        for k in range(1, num_teams + 1):
            for i in range(1, num_weeks + 1):
                for j in range(1, num_weeks + 1):
                    matches.append((h, k, i, j))
    return matches

# =============================================================================
# SINGLE MATCH
# =============================================================================

async def scrape_single_match(session, match, year_name, team_list, date_value_list,
                              team_map, hidden_fields, semaphore, results_file, max_retries=3):
    
    h_idx, k_idx, i_idx, j_idx = match

    first_team  = team_list[h_idx - 1]
    second_team = team_list[k_idx - 1]
    first_week  = f"Week{i_idx}"
    second_week = f"Week{j_idx}"

    team1_val   = team_map[first_team]
    team2_val   = team_map[second_team]
    date1_val   = date_value_list[i_idx - 1]
    date2_val   = date_value_list[j_idx - 1]

    payload = {
        **hidden_fields,
        "ctl08$form$__post__":  "1",
        "ctl08$form$year1":     year_name,
        "ctl08$form$team1":     team1_val,
        "ctl08$form$meetDate1": date1_val,
        "ctl08$form$year2":     year_name,
        "ctl08$form$team2":     team2_val,
        "ctl08$form$meetDate2": date2_val,
    }

    for attempt in range(max_retries):
        try:
            async with semaphore:
                async with session.post(BASE_URL, data=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            score_table = soup.find("table", class_="big-text-bold-borders")

            if score_table is None:
                return (h_idx, k_idx, i_idx, j_idx, 'No meet')

            tds = score_table.find_all("td")
            if len(tds) < 2:
                return (h_idx, k_idx, i_idx, j_idx, 'No meet')

            score1 = tds[0].text.strip()   
            score2 = tds[1].text.strip()   
            score  = f"{score1} - {score2}"

            with csv_lock:
                with open(results_file, mode='a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow([first_team, first_week, second_team, second_week, score])

            return (h_idx, k_idx, i_idx, j_idx, 'Success')

        except Exception as e:
            err_msg = str(e).split('\n')[0][:150]
            print(f"  ERROR attempt {attempt+1}/{max_retries} ({first_team} {first_week} vs "
                  f"{second_team} {second_week}): {err_msg}", flush=True)
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

    return (h_idx, k_idx, i_idx, j_idx, 'Error')

#==========================================================================
# PROGESS REPORTING
#==========================================================================
def print_metadata(team_list, date_value_list, num_teams, num_weeks, total_matches,
                   start_index, remaining, max_concurrent, batch_size):
    print("Fetching form metadata...", flush=True)
    
    if len(team_list) < num_teams:
        print(f"WARNING: only {len(team_list)} teams found, adjusting num_teams")
        num_teams = len(team_list)
    if len(date_value_list) < num_weeks:
        print(f"WARNING: only {len(date_value_list)} weeks found, adjusting num_weeks")
        num_weeks = len(date_value_list)

    print(f"Teams:          {num_teams}")
    print(f"Weeks:          {num_weeks}")
    print(f"Total matches:  {total_matches:,}")
    print(f"Already done:   {start_index:,}")
    print(f"Remaining:      {len(remaining):,}")
    print(f"Concurrency:    {max_concurrent}")
    print(f"Batch size:     {batch_size:,}")
    print(f"{'='*60}")

def initialize_results_file(results_file):
    with open(results_file, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['First Team', 'First Week', 'Second Team', 'Second Week', 'Score'])
       
def print_batch_header(batch_num, batch_size, global_position, total_matches):
    batch_start_time = time.strftime("%m/%d %I:%M:%S %p")
    print(f"{'='*60}")
    print(f"BATCH {batch_num}: Processing {batch_size} matches starting at {batch_start_time}")
    print(f"Overall Progress: {global_position}/{total_matches} ({global_position/total_matches*100:.1f}%)")
    print(f"{'='*60}")

def print_progress_update(completed, matches, batch_start_time, last_checkpoint, checkpoint_size, errors):
    current_time = time.time()
    elapsed = current_time - batch_start_time
    elapsed_checkpoint = current_time - last_checkpoint

    rate_recent = checkpoint_size / elapsed_checkpoint      
    rate = completed / elapsed           
    remaining_batch = (len(matches) - completed) / rate

    print(f"Batch progress: {completed}/{len(matches)} ({completed/len(matches)*100:.1f}%) | "
          f"Rate: {rate_recent:.2f} matches/sec | "
          f"Batch ETA: {remaining_batch/60:.1f} min | "
          f"Errors: {errors}", flush=True)

    return current_time

def calculate_batch_metrics(start_index, batch_start, completed, batch_start_time, 
                           total_time_elapsed, total_errors, errors, total_matches):
    batch_elapsed = time.time() - batch_start_time
    global_index = start_index + batch_start + completed
    updated_total_errors = total_errors + errors
    updated_total_time = total_time_elapsed + batch_elapsed
    overall_rate = global_index / updated_total_time
    matches_remaining = total_matches - global_index

    return {
        'batch_elapsed': batch_elapsed,
        'global_index': global_index,
        'total_errors': updated_total_errors,
        'total_time_elapsed': updated_total_time,
        'overall_rate': overall_rate,
        'matches_remaining': matches_remaining
    }

def print_batch_summary(batch_num, completed, batch_size, elapsed, errors,
                        global_index, total_matches, total_errors, total_elapsed, overall_rate):
    
    matches_remaining = total_matches - global_index

    print(f"\n{'='*60}")
    print(f"*** BATCH {batch_num} COMPLETE ***")
    print(f"{'='*60}")
    print(f"Batch Stats:")
    print(f" - Matches completed: {completed}/{batch_size}")
    print(f" - Batch time: {elapsed/60:.2f} minutes")
    print(f" - Batch rate: {completed/elapsed:.2f} matches/sec")
    print(f" - Errors in batch: {errors}")
    print(f"\nOverall Progress:")
    print(f" - Total completed: {global_index}/{total_matches} ({global_index/total_matches*100:.1f}%)")
    print(f" - Total errors: {total_errors}")
    print(f" - Error rate: {total_errors/global_index*100:.2f}%")
    print(f" - Matches remaining: {matches_remaining}")
    print(f" - Time Elapsed: {total_elapsed/3600:.2f} hours")
    print(f" - Overall rate: {overall_rate:.3f} matches/sec")

    if matches_remaining > 0:
        eta_seconds = matches_remaining / overall_rate
        eta_hours = eta_seconds / 3600
        print(f" - ETA: {eta_hours:.2f} hours ({eta_hours/24:.1f} days)")

    print(f"{'='*60}\n")

# =============================================================================
# BATCH EXECUTION
# =============================================================================

async def run_batch(batch_start_time, matches, year_name, team_list, date_value_list,
                    team_map, hidden_fields, results_file, max_concurrent=75, checkpoint_size = 500):
    
    semaphore = asyncio.Semaphore(max_concurrent)
    completed = 0
    errors = 0
    last_checkpoint = batch_start_time

    connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            scrape_single_match(
                session, match, year_name, team_list, date_value_list,
                team_map, hidden_fields, semaphore, results_file) for match in matches]

        for coro in asyncio.as_completed(tasks):
            result = await coro
            completed += 1
            if result[4] == 'Error':
                errors += 1

            if completed % checkpoint_size == 0 or completed == len(matches):
                last_checkpoint = print_progress_update(completed, matches, batch_start_time,
                                                        last_checkpoint, checkpoint_size, errors)

    return completed, errors

# =============================================================================
# SCRAPE IN BATCHES - MAIN FUNCTION
# =============================================================================

def scrape_year(year_name, num_teams, num_weeks, max_concurrent=75, checkpoint_size = 500, batch_size=5000):
    results_file = os.path.join(data_directory, f"results_{year_name}.csv")

    hidden_fields, team_map, date_map, date_value_list = fetch_form_metadata(year_name)
    team_list = list(team_map.keys())

    all_matches   = generate_matches(num_teams, num_weeks)
    total_matches = len(all_matches)

    start_index, prev_time, prev_errors = load_progress()

    if start_index == 0:
        initialize_results_file(results_file)

    remaining = all_matches[start_index:]

    print_metadata(team_list, date_value_list, num_teams, num_weeks, total_matches,
                   start_index, remaining, max_concurrent, batch_size)

    total_time = prev_time
    total_errors = prev_errors
    global_index = start_index

    for batch_start in range(0, len(remaining), batch_size):
        batch = remaining[batch_start : batch_start + batch_size]
        batch_num = (global_index) // batch_size + 1

        print_batch_header(batch_num, batch_size, global_index, total_matches)

        batch_start_time = time.time()
        completed, errors = asyncio.run(
            run_batch(
                batch_start_time, batch, year_name, team_list, date_value_list,
                team_map, hidden_fields, results_file, max_concurrent
            )
        )

        metrics = calculate_batch_metrics(
            start_index, batch_start, completed, batch_start_time,
            total_time, total_errors, errors, total_matches
        )

        total_errors = metrics['total_errors']
        total_time = metrics['total_time_elapsed']
        batch_elapsed = metrics['batch_elapsed']
        global_index = metrics['global_index']
        overall_rate = metrics['overall_rate']
        matches_remaining = metrics['matches_remaining']

        save_progress(global_index, total_time, total_errors)

        print_batch_summary(batch_num, completed, batch_size, batch_elapsed, errors,
                            global_index, total_matches, total_errors, total_time,
                            overall_rate)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("NVSL SCRAPER")
    print("="*60)

    year_name = "2026"
    num_teams = 102
    num_weeks = 5
    max_concurrent = 100
    checkpoint_size = 500
    batch_size = 5000
    
    scrape_year(
        year_name = year_name,
        num_teams = num_teams,
        num_weeks = num_weeks,
        max_concurrent = max_concurrent,
        checkpoint_size = checkpoint_size,
        batch_size = batch_size
    )
    print("\n" + "="*60)
    print("ALL SCRAPING COMPLETE!")
    print("="*60)
    
