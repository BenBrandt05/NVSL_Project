#==========================================================================
# LIBRARIES
#==========================================================================
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import csv
import threading
import psutil
import os

#==========================================================================
# PATH CONFIGURATION
#==========================================================================

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_directory = os.path.join(project_root, 'Data')

csv_lock = threading.Lock()

#==========================================================================
# DRIVER SETUP
#==========================================================================

def create_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--disk-cache-size=1")
        options.add_argument("--media-cache-size=1")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-cache")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-javascript")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--disable-features=VizDisplayCompositor,IsolateOrigins,site-per-process")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--single-process")
        options.add_argument("--disable-breakpad")
        options.add_argument("--disable-component-update")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--renderer-process-limit=2")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    
    return driver

#==========================================================================
# PAGE INTERACTION FUNCTIONS
#==========================================================================

def get_first_team(driver, team_num):
    team1 = WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl08_form_team1"]')))
    select = Select(team1)
    select.select_by_index(team_num)
   
def get_first_week(driver, week_num):
    week1 = WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl08_form_meetDate1"]')))
    select = Select(week1)
    select.select_by_index(week_num)
   
def get_second_team(driver, team_num):
    team2 = WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl08_form_team2"]')))
    select = Select(team2)
    select.select_by_index(team_num)
    
def get_second_week(driver, week_num):
    week2 = WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl08_form_meetDate2"]')))
    select = Select(week2)
    select.select_by_index(week_num)

def get_first_year(driver, year_num):
    year1 = WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl08_form_year1"]')))
    select = Select(year1)
    select.select_by_index(year_num)

def get_second_year(driver, year_num):
    year2 = WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl08_form_year2"]'))) 
    select = Select(year2)
    select.select_by_index(year_num)

def press_submit(driver):
    press_submit = driver.find_element('xpath','//*[@id="ctl08_form"]/button')
    press_submit.click()

def get_score(driver):
    score1_element = WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, '//*[@id="league_schedules"]/table[3]/tbody/tr/td[1]')))
    score2_element = WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, '//*[@id="league_schedules"]/table[3]/tbody/tr/td[2]')))
    score1 = score1_element.text               
    score2 = score2_element.text               
    total_score = score1 + ' - ' + score2      
    return total_score

def return_virtual_meet(driver):
    return_back = driver.find_element('xpath','//*[@id="league_schedules"]/p/a')
    return_back.click()

def get_team_list(driver):
    team_list = []
    options = driver.find_elements('xpath','//*[@id="ctl08_form_team1"]/option')
    for option in options:
        team_list.append(option.text.strip())
        
    return team_list

def get_week_list():
    week_list = ['','Week1','Week2','Week3','Week4','Week5']
    return week_list

#==========================================================================
# PROGRESS TRACKING
#==========================================================================

def save_progress(global_index, total_time_elapsed, total_errors):
    file_path = os.path.join(data_directory, 'progress.csv')
    with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow([global_index, total_time_elapsed, total_errors])

def load_progress():
    file_path = os.path.join(data_directory, 'progress.csv')
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            progress = list(reader)
        if progress:
            return int(progress[0][0]), float(progress[0][1]), int(progress[0][2])
        else:
            return 0, 0.0, 0
    except Exception as e:
        print(f"Error loading progress: {e}")
        return 0, 0.0, 0

#==========================================================================
# MATCH GENERATION
#==========================================================================
  
def generate_matches(h, k, i, j, num_teams_one, num_weeks_one, num_teams_two, num_weeks_two):
    matches = []
    for h_index in range(h, num_teams_one+1):
        for k_index in range(k if h_index == h else 1, num_teams_two+1):
            for i_index in range(i if h_index == h and k_index == k else 1, num_weeks_one+1):
                for j_index in range(j if h_index == h and k_index == k and i_index == i else 1, num_weeks_two+1):
                    matches.append((h_index, k_index, i_index, j_index))
    return matches


#==========================================================================
# SINGLE MATCH SCRAPING
#==========================================================================

driver_pool = threading.local()
active_drivers = []
active_drivers_lock = threading.Lock()

def get_pooled_driver():
    if not hasattr(driver_pool, 'driver') or driver_pool.driver is None:
        driver_pool.driver = create_driver(headless=True)
        with active_drivers_lock:
            active_drivers.append(driver_pool.driver)
    return driver_pool.driver

def scrape_single_match(match_data, year_index, year_name, team_list, week_list, max_retries=2):
    h_index, k_index, i_index, j_index = match_data
    results_file = os.path.join(data_directory, f"results_{year_name}.csv")
    
    for attempt in range(max_retries):
        driver = get_pooled_driver()
        try:
            driver.get('https://www.mynvsl.com/virtual-meet')
            
            first_team = team_list[h_index]
            first_week = week_list[i_index]
            second_team = team_list[k_index]
            second_week = week_list[j_index]

            get_first_year(driver, year_index)
            get_first_team(driver, h_index)
            get_first_week(driver, i_index)
            get_second_year(driver, year_index)
            get_second_team(driver, k_index)
            get_second_week(driver, j_index)
                
            press_submit(driver)
            score = get_score(driver)
            return_virtual_meet(driver)

            with csv_lock:
                with open(results_file, mode='a', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    writer.writerow([first_team, first_week, second_team, second_week, score])
            
            return (h_index, k_index, i_index, j_index, 'Success')
        
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            if len(error_msg) > 150:
                error_msg = error_msg[:150] + "..."
    
            print(f"ERROR: {error_msg} at ({h_index},{k_index},{i_index},{j_index}) - Attempt {attempt + 1}/{max_retries}")
            
            try:
                driver.quit()
            except:
                pass
            finally:
                driver_pool.driver = None
            
            if attempt == max_retries - 1:
                return (h_index, k_index, i_index, j_index, f'Error: {e}')
            
            time.sleep(2)

#==========================================================================
# CHROME CLEANUP
#==========================================================================

def cleanup_drivers():
    with active_drivers_lock:
        for driver in active_drivers:
            try:
                driver.quit()
            except:
                pass
        active_drivers.clear()

def cleanup_chrome_processes():
    cleanup_start = time.time()
    killed = 0

    for proc in psutil.process_iter(['name', 'pid']):
        try:
            name = proc.info['name'].lower()
            if 'chrome' in name or 'chromedriver' in name:
                proc.kill()
                proc.wait(timeout=2)
                killed += 1
        except:
            pass

    cleanup_elapsed = time.time() - cleanup_start
    print(f" Killed {killed} ChromeDriver processes in {cleanup_elapsed:.1f}s", flush=True)
    return killed

#==========================================================================
# PROGESS REPORTING
#==========================================================================

def print_batch_header(batch_num, batch_size, global_position, total_matches):
    batch_start_time = time.strftime("%m/%d %I:%M:%S %p")
    print(f"\n{'='*60}")
    print(f"BATCH {batch_num}: Processing {batch_size} matches starting at {batch_start_time}")
    print(f"Overall Progress: {global_position}/{total_matches} ({global_position/total_matches*100:.1f}%)")
    print(f"{'='*60}\n")

def print_batch_summary(batch_num, completed, batch_size, elapsed, errors,
                        global_index, total_matches, total_errors, total_elapsed, overall_rate):
    
    matches_remaining = total_matches - global_index

    print(f"\n{'='*70}")
    print(f"*** BATCH {batch_num} COMPLETE ***")
    print(f"{'='*70}")
    print(f"Batch Stats:")
    print(f" - Matches completed: {completed}/{batch_size}")
    print(f" - Batch time: {elapsed/60:.2f} minutes ({elapsed/3600:.2f} hours)")
    print(f" - Batch rate: {completed/elapsed:.2f} matches/sec")
    print(f" - Errors in batch: {errors}")
    print(f"\nOverall Progress:")
    print(f" - Total completed: {global_index}/{total_matches} ({global_index/total_matches*100:.1f}%)")
    print(f" - Total errors: {total_errors}")
    print(f" - Error rate: {total_errors/global_index*100:.2f}%")
    print(f" - Matches remaining: {matches_remaining}")
    print(f" - Time Elapsed: {total_elapsed/3600:.2f} hours ({total_elapsed/86400:.1f} days)")
    print(f" - Overall rate: {overall_rate:.3f} matches/sec")

    if matches_remaining > 0:
        eta_seconds = matches_remaining / overall_rate
        eta_hours = eta_seconds / 3600
        print(f" - ETA: {eta_hours:.2f} hours ({eta_hours/24:.1f} days)")

    print(f"{'='*70}\n")

def print_progress_update(completed, batch_size, start_time, last_checkpoint, errors):
    current_time = time.time()
    elapsed = current_time - start_time
    elapsed_100 = current_time - last_checkpoint

    rate_recent = 100 / elapsed_100
    rate = completed / elapsed
    remaining_batch = (batch_size - completed) / rate

    print(f"Batch progress: {completed}/{batch_size} ({completed/batch_size*100:.1f}%) | "
          f"Rate: {rate_recent:.2f} matches/sec | "
          f"Batch ETA: {remaining_batch/60:.1f} min | "
          f"Errors: {errors}", flush=True)

    return current_time

#==========================================================================
# BATCH EXECUTION - HELPER FUNCTIONS
#==========================================================================

def submit_new_work(pending_matches, executor, year_index, year_name, team_list, week_list, 
                    active_futures, future_start_times, max_workers):
    while pending_matches and len(active_futures) < max_workers * 2:
        match = pending_matches.pop(0)
        future = executor.submit(scrape_single_match, match, year_index, year_name, team_list, week_list)
        active_futures[future] = match
        future_start_times[future] = time.time()

def handle_completed_future(future, match, completed, errors, failed_matches):
    try:
        result = future.result(timeout=5)
        completed += 1
        h_idx, k_idx, i_idx, j_idx, status = result

        if 'Error' in status:
            errors += 1
            failed_matches.append((h_idx, k_idx, i_idx, j_idx))

        return completed, errors, None

    except Exception as e:
        print(f"ERROR processing future {match}: {e}", flush=True)

        if 'Connection aborted' in str(e):
            return completed, errors, match
        else:
            completed += 1
            errors += 1
            failed_matches.append(match)
            return completed, errors, None

def cleanup_future(future, active_futures, future_start_times): 
    if future in active_futures:
        del active_futures[future]
    if future in future_start_times:
        del future_start_times[future]

def abandon_stragglers(active_futures, future_start_times, completed, errors, failed_matches):
    straggler_timeout = 60
    min_completed_before_abandon = 100

    if completed <= min_completed_before_abandon:
        return completed, errors

    current_time = time.time()
    stragglers_to_abandon = []

    for future in list(active_futures.keys()):
        elapsed = current_time - future_start_times.get(future, current_time)
        if elapsed > straggler_timeout:
            stragglers_to_abandon.append(future)

    for future in stragglers_to_abandon:
        match = active_futures[future]
        elapsed = current_time - future_start_times[future]
        print(f"ABANDONING straggler after {elapsed:.0f}s: {match}", flush=True)

        future.cancel()
        failed_matches.append(match)
        cleanup_future(future, active_futures, future_start_times)
        errors += 1
        completed += 1

    return completed, errors

#==========================================================================
# BATCH EXECUTION - MAIN FUNCTION
#==========================================================================

def execute_batch(batch_matches, year_index, year_name, team_list, week_list, max_workers):
    completed = 0
    errors = 0
    failed_matches = []
    start_time = time.time()
    last_checkpoint = time.time()

    future_start_times = {}
    active_futures = {}
    pending_matches = list(batch_matches)

    executor = ThreadPoolExecutor(max_workers=max_workers)

    try:
        for _ in range(min(max_workers * 2, len(pending_matches))):
            match = pending_matches.pop(0)
            future = executor.submit(scrape_single_match, match, year_index, year_name, team_list, week_list)
            active_futures[future] = match
            future_start_times[future] = time.time()

        while active_futures:
            if completed >= len(batch_matches):
                print("Warning: completed count reached batch size but futures remain; forcing exit.", flush=True)
                for f in list(active_futures.keys()):
                    f.cancel()
                active_futures.clear()
                break
            
            try:
                for future in as_completed(list(active_futures.keys()), timeout=1):
                    match = active_futures[future]
                    completed, errors, retry_match = handle_completed_future(
                        future, match, completed, errors, failed_matches)
                    
                    cleanup_future(future, active_futures, future_start_times)

                    if retry_match:
                        print(f"Retrying match {retry_match} due to connection failure", flush=True)
                        retry_future = executor.submit(scrape_single_match, retry_match, year_index, 
                                                      year_name, team_list, week_list)
                        active_futures[retry_future] = retry_match
                        future_start_times[retry_future] = time.time()

                    submit_new_work(pending_matches, executor, year_index, year_name, 
                                  team_list, week_list, active_futures, future_start_times, max_workers)
                    
                    if completed % 100 == 0:
                        last_checkpoint = print_progress_update(
                            completed, len(batch_matches), start_time, last_checkpoint, errors
                        )
                        
                   

            except TimeoutError:
                pass

            completed, errors = abandon_stragglers(active_futures, future_start_times,
                                                   completed, errors, failed_matches)

    finally:
        cleanup_drivers()
        cleanup_chrome_processes()
        executor.shutdown(wait=False, cancel_futures=True)

    return completed, errors, failed_matches
    
#==========================================================================
# SCRAPE IN BATCHES - HELPER FUNCTIONS
#==========================================================================

def initialize_scraping(year_name):
    temp_driver = create_driver(headless=False)
    temp_driver.get('https://www.mynvsl.com/virtual-meet')
    team_list = get_team_list(temp_driver)
    week_list = get_week_list()
    temp_driver.quit()
    return team_list, week_list

def initialize_results_file(results_file):
    with open(results_file, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['First Team', 'First Week', 'Second Team', 'Second Week', 'Score'])

def print_scraping_summary(year_name, total_matches, start_index, remaining_matches, batch_size, max_workers):
    print(f"Starting scrape for {year_name}")
    print(f"Total matches: {total_matches}")
    print(f"Already completed: {start_index}")
    print(f"Remaining: {len(remaining_matches)}")
    print(f"Batch size: {batch_size} matches")
    print(f"Using {max_workers} parallel workers\n")

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

#==========================================================================
# SCRAPE IN BATCHES - MAIN FUNCTION
#==========================================================================

def scrape_in_batches(year_index, year_name, num_teams_one, num_weeks_one,
                      num_teams_two, num_weeks_two, max_workers, batch_size):
    results_file = os.path.join(data_directory, f"results_{year_name}.csv")
    
    team_list, week_list = initialize_scraping(year_name)
    all_matches = generate_matches(1, 1, 1, 1, num_teams_one, num_weeks_one, num_teams_two, num_weeks_two)
    total_matches = len(all_matches)    
    start_index, previous_time_elapsed, previous_errors = load_progress()
    
    if start_index == 0:
        initialize_results_file(results_file)
        
    remaining_matches = all_matches[start_index:]    
    print_scraping_summary(year_name, total_matches, start_index, remaining_matches, batch_size, max_workers)

    total_time_elapsed = previous_time_elapsed
    total_errors = previous_errors
    
    for batch_start in range(0, len(remaining_matches), batch_size):
        batch_matches = remaining_matches[batch_start:batch_start + batch_size]
        batch_num = (start_index + batch_start) // batch_size + 1
        global_position = start_index + batch_start

        print_batch_header(batch_num, len(batch_matches), global_position, total_matches)
        
        batch_start_time = time.time()
        completed, errors, failed_matches = execute_batch(
            batch_matches, year_index, year_name, team_list, week_list, max_workers
        )

        metrics = calculate_batch_metrics(
            start_index, batch_start, completed, batch_start_time,
            total_time_elapsed, total_errors, errors, total_matches
        )

        total_errors = metrics['total_errors']
        total_time_elapsed = metrics['total_time_elapsed']
        batch_elapsed = metrics['batch_elapsed']
        global_index = metrics['global_index']
        overall_rate = metrics['overall_rate']
        matches_remaining = metrics['matches_remaining']
        
        save_progress(global_index, total_time_elapsed, total_errors)

        print_batch_summary(batch_num, completed, len(batch_matches), batch_elapsed, errors,
                            global_index, total_matches, total_errors, total_time_elapsed, overall_rate)
        yield {
            'batch_num': batch_num,
            'completed': completed,
            'errors': errors,
            'time': batch_elapsed,
            'global_index': global_index,
            'overall_completed': global_index,
            'overall_total': total_matches,
            'overall_remaining': matches_remaining,
            'overall_rate': overall_rate
        }

    print("\n*** ALL BATCHES COMPLETE! ***")
        
# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("NVSL SCRAPER")
    print("="*70)

    year_index = 10
    year_name = '2014'
    num_teams = 102
    num_weeks = 5
    max_workers = 12
    batch_size = 1000

    for batch_result in scrape_in_batches(
        year_index = year_index,
        year_name = year_name,
        num_teams_one = num_teams,
        num_weeks_one = num_weeks,
        num_teams_two = num_teams,
        num_weeks_two = num_weeks,
        max_workers = max_workers,
        batch_size= batch_size):
        
        print("Waiting 3 seconds before next batch...\n")
        time.sleep(3)

    print("\n" + "="*70)
    print("ALL SCRAPING COMPLETE!")
    print("="*70)


