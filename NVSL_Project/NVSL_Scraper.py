#Importing all the proper libraries needed. Selenium needed for scraping
#time needed to sleep the program
#random needed in all of the sleeps to mimic human interaction to avoid getting banned from the website
#csv needed to input all the scraped data into CSV files

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
import random
import csv

driver = webdriver.Chrome()
driver.get('https://www.mynvsl.com/virtual-meet')    #Link to the website

#Filepaths for both the progress file and the results file
results_file = r"C:\Users\badba\OneDrive\NVSL_Project\results.csv"
progress_file = r"C:\Users\badba\OneDrive\NVSL_Project\progress.csv"

#Function clicks the first team option and scrolls using the arrows to the appropriate team

def get_first_team(team_num):
    team1 = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl08_form_team1"]')))
    team1.click()
    WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="ctl08_form_team1"]/option')))
    time.sleep(random.uniform(.06,.15))      #Brief pause between clicking and scrolling
    for i in range(team_num):
        team1.send_keys(Keys.DOWN)
        time.sleep(random.uniform(.03,.07))  #Wait brief period before pressing down again to wait for loading
    time.sleep(random.uniform(.06,.15))      #Pause before selecting
    team1.send_keys(Keys.RETURN)

#Function clicks the first week option and scrolls using the arrows to the appropriate team
    
def get_first_week(week_num):
    week1 = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl08_form_meetDate1"]')))
    week1.click()
    WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="ctl08_form_meetDate1"]')))
    time.sleep(random.uniform(.06,.15))     #Brief pause between clicking and scrolling
    for i in range(week_num):
        week1.send_keys(Keys.DOWN)
        time.sleep(random.uniform(.03,.07))  #Wait brief period before pressing down again to wait for loading   
    time.sleep(random.uniform(.06,.15))      #Pause before selecting
    week1.send_keys(Keys.RETURN)

#Function clicks the second team option and scrolls using the arrows to the appropriate team
    
def get_second_team(team_num):
    team2 = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl08_form_team2"]')))
    team2.click()
    WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="ctl08_form_team2"]/option')))
    time.sleep(random.uniform(.06,.15))      #Brief pause between clicking and scrolling
    for i in range(team_num):
        team2.send_keys(Keys.DOWN)
        time.sleep(random.uniform(.03,.07))  #Wait brief period before pressing down again to wait for loading
    time.sleep(random.uniform(.06,.15))      #Pause before selecting
    team2.send_keys(Keys.RETURN)

#Function clicks the second week option and scrolls using the arrows to the appropriate team
    
def get_second_week(week_num):
    week2 = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl08_form_meetDate2"]')))
    week2.click()
    WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="ctl08_form_meetDate2"]')))
    time.sleep(random.uniform(.06,.15))      #Brief pause between clicking and scrolling
    for i in range(week_num):
        week2.send_keys(Keys.DOWN)
        time.sleep(random.uniform(.03,.07))  #Wait brief period before pressing down again to wait for loading
    time.sleep(random.uniform(.06,.15))      #Pause before selecting   
    week2.send_keys(Keys.RETURN)

#Function simply presses the submit button after all teams are selected

def press_submit():
    press_submit = driver.find_element('xpath','//*[@id="ctl08_form"]/button')
    press_submit.click()

#After the page loads, this function gets the score from the virtual meet ran

def get_score():
    score1_element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="league_schedules"]/table[3]/tbody/tr/td[1]')))
    score2_element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="league_schedules"]/table[3]/tbody/tr/td[2]')))
    score1 = score1_element.text               #Winning teams score
    score2 = score2_element.text               #Losing teams score
    total_score = score1 + ' - ' + score2      #Both together in one string
    return total_score

#Function to press button to go back to virtual meet page

def return_virtual_meet():
    return_back = driver.find_element('xpath','//*[@id="league_schedules"]/p/a')
    return_back.click()

#Function that gets all the teams available in the dropdown of the virtual meet options

def get_team_list():
    team_list = []
    options = driver.find_elements('xpath','//*[@id="ctl08_form_team1"]/option')
    for option in options:
        team_list.append(option.text.strip())
        
    return team_list

#Manually inputted week_list in an attempt to standardize weeks rather than days

def get_week_list():
    week_list = ['','Week1','Week2','Week3','Week4','Week5']
    return week_list

#Function used at the end of the loop to save how far along in loop the program is
#Takes parameters h, k, i, j which are different parts of the loop

def save_progress(h, k, i, j):
    file_path = progress_file
    with open(file_path, mode='w', newline='', encoding = 'utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow([h, k, i, j])    #Changes the progress file to update with the loop counter

#Function used at start of loop to load the current progress in the loop

def load_progress():
    file_path = progress_file
    try:
        with open(file_path, mode='r', newline='', encoding = 'utf-8-sig') as file:
            reader = csv.reader(file)
            progress = list(reader)
            if progress:
                return [int(val) for val in progress[0]]
            else:
                return [1, 1, 1, 1]  #Default if the file is empty
    except Exception as e:
        print(f"Error loading progress: {e}")
        return [1, 1, 1, 1]

#This function is what performs the main scraping of data and writing into the CSV file

def full_loop(num_teams_one, num_weeks_one, num_teams_two, num_weeks_two):
    with open(results_file, mode='a', newline='') as file:   #Mode in append to not overwrite whats already there
        writer = csv.writer(file)

        team_list = get_team_list()
        week_list = get_week_list()
    
        h, k, i, j = load_progress()         #Reads the progress file to determine where in the loop we are
        
        for h_index in range(h,num_teams_one+1):
            for k_index in range(k if h_index == h else 1,num_teams_two+1):
                for i_index in range(i if h_index == h and k_index == k else 1,num_weeks_one+1):
                    for j_index in range(j if h_index == h and k_index == k and i_index == i else 1,num_weeks_two+1):

                        first_team = team_list[h_index]      #Gets first team from list using loop index
                        first_week = week_list[i_index]      #Gets first week from list using loop index
                        second_team = team_list[k_index]     #Gets second team from list using loop index
                        second_week = week_list[j_index]     #Gets second week from list using loop index
                        
                        get_first_team(h_index)              #Scrolls to the first team
                        get_first_week(i_index)              #Scrolls to the first week
                        get_second_team(k_index)             #Scrolls to the second team
                        get_second_week(j_index)             #Scrolls to the second week
                        press_submit()                       #Presses submit button
                        time.sleep(random.uniform(.3,.7))    #All time.sleep are to wait for webpages to load
                        score = get_score()                  #Scraped the score
                        time.sleep(random.uniform(.3,.7))
                        return_virtual_meet()                #Goes back to original page
                        time.sleep(random.uniform(0.5,1.5))
                        
                        writer.writerow([first_team, first_week, second_team, second_week, score])    #Data is inputted into results.csv

                        save_progress(h_index, k_index, i_index, j_index)      #As loop counter updates, so does progress.csv this shows where in the loop we are
        print('All Done!')


full_loop(102,5,102,5)   #102 teams all 5 weeks each gives 102*5*102*5=260,100 virtual meets to run

driver.close()
