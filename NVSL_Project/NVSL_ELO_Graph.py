#All necessary libraries are imported
import matplotlib.pyplot as plt
import mplcursors as mpl
import pandas as pd
import numpy as np
from collections import defaultdict

#ELO Updater
#This group of functions is designed to do all the ELO calculations

#Because ELO is based on change over time, this will ensure that the data is randomly shuffled
def shuffle_df():
    df = pd.read_csv(r"C:\Users\badba\OneDrive\NVSL_Project\results.csv", header=None)   #Creates a dataframe
    df.columns = ['First Team', 'First Week', 'Second Team', 'Second Week', 'Score']
    df = df.iloc[1:]
    df = df.drop_duplicates()        #Following lines add column names, eliminate the names column from the CSV, and drop any duplicate columns
    df_shuffled = df.sample(frac=1).reset_index(drop=True)      #This is what actually randomizes the dataframe frac=1 is saying 100% of the sample
    return df_shuffled

#Because of the way the score is displayed in the CSV, we need to parse it so we only have the numbers

def score_parser(score_str):
    parts = score_str.split(' - ')         #Splits the score into a list of two elements
    if len(parts) != 2: 
        return None
    part1 = parts[0].split()            
    part2 = parts[1].split()               #Splits each list elemenet of the original list
    if len(part1) < 2 or len(part2) < 2:
        return None
    try:
        score1 = float(part1[0])           
        team_label1 = ' '.join(part1[1:])
        score2 = float(part2[0])
        team_label2 = ' '.join(part2[1:])        #Assigns labels to all the different elements individually
    except ValueError:
        return None
    return score1, team_label1, score2, team_label2    #Returns all the labels for the teams and their scores

#Inititializing every teams starting ELO at 1600

def initialize_Elos(df, initial_elo=1600):
    teams = pd.concat([df['First Team'], df['Second Team']]).dropna().unique()      #Concatenates Dataframe to include all teams
    ELO = {team: initial_elo for team in teams if team not in ['First Team', 'Second Team']}    #Turns dataframe into a dictionary with every team assigned value 1600
    return ELO

#Updating the actual ELO of teams by taking the dictionary, the four labels from the score parser, and an arbitrary k-value

def update_Elo(ELO, team_A, team_B, score_A, score_B, K=8):  
    elo_A = ELO[team_A]              
    elo_B = ELO[team_B]          #Gets ELOs for Team A and Team B

    expected_A = 1 / (1 + 10 ** ((elo_B - elo_A) / 400))
    expected_B = 1 - expected_A               #Formula I found online to calculate ELOs

    if score_A > score_B:
        actual_A, actual_B = 1, 0         
    elif score_A < score_B:
        actual_A, actual_B = 0, 1
    else:
        actual_A, actual_B = 0.5, 0.5        #Checks to see win, lose, draw and assigns each a value

    ELO[team_A] += K * (actual_A - expected_A)
    ELO[team_B] += K * (actual_B - expected_B)      #Using that W/L/D value, we can use that and subtract expected multiplied by K to get the change in ELO
    return ELO

#This function takes the dataframe and applies all the above functions

def process_results(df):
    ELO = initialize_Elos(df)      #Set every team to 1600 ELO
    
    for _, row in df.iterrows():
        csv_team1, csv_team2 = row['First Team'], row['Second Team']     #Takes columns 1 and 3 of the dataframe
        parsed = score_parser(row['Score'])                              #Parses the score
        
        if parsed is None:                                               #Handles if any error occured where a score wasn't scraped which never happened
            print(f"Skipping match between {csv_team1} and {csv_team2} due to invalid score format")
            continue
        
        score1, label1, score2, label2 = parsed                          #Now we have our labels for teams and scores
        
        if label1 == label2:                                    # Skip if the parsed labels are the same (self-match)
            continue
        if csv_team1 == csv_team2:                      # Skip if csv says it's a match between different teams, but labels say same team
            continue
        if csv_team1 == label1 and csv_team2 == label2:            # Determine score order
            score_A, score_B = score1, score2
        elif csv_team1 == label2 and csv_team2 == label1:
            score_A, score_B = score2, score1
        else:
            continue                                       #Skip this row if team names don't match the parsed labels                       
    
        if score_A > score_B:
            ELO = update_Elo(ELO, csv_team1, csv_team2, score_A, score_B)        #If team A wins, use csv_team1 as teamA
        elif score_A < score_B:
            ELO = update_Elo(ELO, csv_team2, csv_team1, score_B, score_A)        #If team B wins, use csv_team2 as teamB
        else:
            ELO = update_Elo(ELO, csv_team1, csv_team2, score_A, score_B)        #If tie, order is irrelevant
            
    ELO = {team: round(elo, 0) for team, elo in ELO.items()}                         #Updates the dictionary to keep the ELOs that were just changed
    return ELO


#Analysis of Data
#This next half is the analysis of the data and contains limited functions as some mess up the graph so the functions here are limied

#Expected Rankings are what teams should be ranked based on last years results which I manually wrote out
Expected_Rankings = {'Tuckahoe': 1, 'Chesterbrook': 2, 'Overlee': 3, 'Donaldson Run': 4, 'Highlands Swim': 5, 'Old Keene Mill': 6,
                     'Crosspointe': 7, 'Langley': 8, 'Oakton': 9, 'High Point Pool': 10, 'Hunt Valley': 11, 'McLean': 12,
                     'Kent Gardens': 13, 'Wakefield Chapel': 14, 'Fair Oaks': 15, 'Mantua': 16, 'Little Rocky Run': 17, 'Hamlet': 18,
                     'Little Hunting Park': 19, 'Vienna Woods': 20, 'Orange Hunt': 21, 'Hiddenbrook': 22, 'Vienna Aquatic': 23, 'Lee Graham': 24,
                     'Pinecrest': 25, 'Sleepy Hollow Rec': 26, 'Cardinal Hill': 27, 'Virginia Hills': 28, 'Virginia Run': 29, 'South Run': 30,
                     'Fairfax': 31, 'Springboard': 32, 'Poplar Heights': 33, 'Fairfax Station': 34, 'Hunter Mill': 35, 'Dunn Loring': 36,
                     'Rolling Hills': 37, 'Parklawn': 38, 'Sleepy Hollow B & R': 39, 'Canterbury Woods': 40, 'Waynewood': 41, 'Dominion Hills': 42,
                     'Ravensworth Farm': 43, 'Fox Hunt': 44, 'Cottontail': 45, 'Mount Vernon Park': 46, 'Dowden Terrace': 47, 'Lakevale Estates': 48,
                     'Lakeview': 49, 'Camelot': 50, 'Arlington Forest': 51, 'Sully Station': 52, 'Villa Aquatic': 53, 'Mansion House': 54,
                     'Forest Hollow': 55, 'Hollin Meadows': 56, 'Country Club Hills': 57, 'Highland Park': 58, 'Walden Glen': 59, 'Holmes Run Acres': 60,
                     'Kings Ridge': 61, 'Greenbriar': 62, 'Truro': 63, 'Daventry': 64, 'Mosby Woods': 65, 'Brookfield': 66,
                     'Shouse Village': 67, 'Rolling Valley': 68, 'Stratford': 69, 'Poplar Tree': 70, 'Great Falls': 71, 'Rolling Forest': 72,
                     'Sideburn Run': 73, 'Fairfax Club Estates': 74, 'Riverside Gardens': 75, 'Fox Mill Woods': 76, 'Woodley': 77, 'Brandywine': 78,
                     'Commonwealth': 79, 'Hayfield Farm': 80, 'Parliament': 81, 'Somerset-Olde Creek': 82, 'Lincolnia Park': 83, 'Laurel Hill': 84,
                     'Burke Station': 85, 'Fox Mill Estates': 86, 'Sully Station II': 87, 'Hollin Hills': 88, 'Annandale': 89, 'Lake Braddock': 90,
                     'Rutherford': 91, 'Newington Forest': 92, 'Pleasant Valley': 93, 'Herndon': 94, 'Village West': 95, 'Long Branch': 96,
                     'North Springfield': 97, 'Ilda Community': 98, 'Broyhill Crest': 99, 'Springfield': 100, 'Edsall Park': 101, 'Pinewood Lake': 102}

#Initializing some variables here that are used shortly
num_iterations = 100
all_rankings = []
all_elos = []

#This loop takes the number of iterations and performs an ELO update of the CSV for the number of iterations
for _ in range(num_iterations):
    shuffled_df = shuffle_df()        #New shuffled dataframe for each iteration
    elo = process_results(shuffled_df)          #Process the results each time
    sorted_elo = dict(sorted(elo.items(), key=lambda x: x[1], reverse=True))    #Sort the ELOs from Highest to Lowest
    rankings = {team: rank + 1 for rank, (team, _) in enumerate(sorted_elo.items())}     #Assigns ranks to each team based on their ELO
    
    all_rankings.append(rankings)
    all_elos.append(sorted_elo)           #Takes these dictionaries and appends them to the initialized lists from earlier


avg_rankings = defaultdict(list)
avg_elos = defaultdict(list)             #Creates two dictionaries who contain lists that will be used later

#This loop builds a history of rankings and ELOs to be able to compute the average over several iterations
for ranking_dict, elo_dict in zip(all_rankings, all_elos):      
    for team in ranking_dict:
        avg_rankings[team].append(ranking_dict[team])
        avg_elos[team].append(elo_dict[team])

final_avg_rankings = {team: float(round(np.mean(ranks), 2)) for team, ranks in avg_rankings.items()}
final_avg_elos = {team: float(round(np.mean(elos), 2)) for team, elos in avg_elos.items()}        #Calculates the average ranking and ELO of each team over the number of iterations

final_avg_rankings_sorted = dict(sorted(final_avg_rankings.items(), key=lambda x: x[1]))
final_avg_elos_sorted = dict(sorted(final_avg_elos.items(), key=lambda x: x[1], reverse=True))    #Sorts them into alphabetical order

sorted_teams = sorted(final_avg_elos_sorted.items(), key=lambda x: x[1], reverse=True)          #Sorts into tuples of team and average ELO
actual_rankings = {team: rank + 1 for rank, (team, _) in enumerate(sorted_teams)}               #Turns everything into a dictionary with team name and ranking

ER_Alpha = dict(sorted(Expected_Rankings.items()))                      #Alphabatizes the Expected_Rankings dictionary

teams = list(Expected_Rankings.keys())                              #Lists the teams
Rankings_Value = np.array([Expected_Rankings[team] for team in teams])           #Creats a numpy array of teams and their expected ratings
ELO_Value = np.array([final_avg_elos_sorted[team] for team in teams])            #Creats a numpy array of teams and their ELOs

slope, intercept = np.polyfit(Rankings_Value, ELO_Value, 1)                      #Calculates a line of best fit using two numpy arrays

correlation_matrix = np.corrcoef(Rankings_Value, ELO_Value)                 #Uses numpy to find the correlation of the data         
r_value = round(correlation_matrix[0, 1],3)
r_squared = round(r_value ** 2,4)                                           #Finds the r and R^2 values for the data

fit_x = np.array(Rankings_Value)              
fit_y = slope * fit_x + intercept                                            #Gives the dimensions for the X and Y on the scatterplot so everything fits and is visible

predicted_elo = slope * np.array(Rankings_Value) + intercept                 #Calculates what a teams ELO should be given the line of best fit


colors = ['green' if actual > predicted else 'red' for actual, predicted in zip(ELO_Value, predicted_elo)]   #Assigns colors to teams who perform above or below expected

fig, ax = plt.subplots()
scatter = ax.scatter(Rankings_Value, ELO_Value, c = colors, alpha = 0.7)
ax.plot(fit_x, fit_y, color='blue', alpha=0.4, label=f'R-value = {r_value}\n$R^2$ = {r_squared}')
ax.set_xlabel("Expected Ranking")
ax.set_ylabel("Actual ELO")
ax.set_title("ELO vs Expected Ranking")
ax.legend()                               #Highlighting the graph that is created using MatPlotLib with our axes and title labels, line of best fit shown, and legend

elo_differences = ELO_Value - predicted_elo                                  #Sees how far away a team is from their predicted ELO
ranking_differences = {team: Expected_Rankings[team] - final_avg_rankings_sorted[team] for team in Expected_Rankings}   #Dictionary showing how far a teams actual ranking is from expected ranking

#This function gives some fun insight into the highest and lowest performing teams based on expectations with our elo_differences and ranking_differences dictionaries

def compute_biggest_changes(teams, elo_differences, ranking_differences):
    biggest_improvement_index = np.argmax(elo_differences)
    biggest_drop_index = np.argmin(elo_differences)                   #Gets index of team with lowest ELO_difference

    biggest_improvement_team = teams[biggest_improvement_index]
    biggest_improvement_value = round(elo_differences[biggest_improvement_index], 0)    #Gets the team that improved the most and how much ELO they beat their expected by

    biggest_drop_team = teams[biggest_drop_index]
    biggest_drop_value = round(elo_differences[biggest_drop_index], 0)   #Similarly, gets the team that had the largest fall and how much below expected ELO they are

    biggest_jump_up_team = max(ranking_differences, key=ranking_differences.get)
    biggest_jump_up_value = ranking_differences[biggest_jump_up_team]           #Gets the team that had the highest jump in rankings and gets how many places they beat it by

    biggest_jump_down_team = min(ranking_differences, key=ranking_differences.get)
    biggest_jump_down_value = ranking_differences[biggest_jump_down_team]  #Gets the team with the farthest decline in rankings and how many places they dropped

    print(f"Biggest Improvement in ELO: {biggest_improvement_team} with an ELO {biggest_improvement_value} above expected")
    print(f"Biggest Drop in ELO: {biggest_drop_team} with an ELO {biggest_drop_value} below expected")
    print(f"Biggest Improvement in ranking: {biggest_jump_up_team} with a ranking {biggest_jump_up_value} places higher than expected")
    print(f"Biggest Drop in ranking: {biggest_jump_down_team} with a ranking {biggest_jump_down_value} places lower than expected")    #Printing out all the values

#This function takes all the teams based on their rankings and splits them into 17 divisions

def assign_divisions(final_avg_rankings_sorted, teams_per_division=6):
    divisions = {f'Division {i+1}': [] for i in range(17)}   #Creates a dictionary of divisions named 1-17
    
    for i, (team, rank) in enumerate(final_avg_rankings_sorted.items()):
        division_number = int((int(round(rank)) - 1) // teams_per_division + 1) #Groups teams into division_numbers based on rounded average rank
        if division_number > 17:
            break  
        divisions[f'Division {division_number}'].append(team)             #Add teams to their assigned division number
    
    return divisions

#This below adds interactivity to the graph allowing you to hover over a point on the graph and see data about it
cursor = mpl.cursor(scatter, hover=True)

@cursor.connect("add")
def on_hover(select):
    index = select.index
    team = teams[index]  
    expected_rank = Rankings_Value[index]
    elo_score = ELO_Value[index]
    actual_rank = final_avg_rankings_sorted.get(team, "Unknown")
    select.annotation.set_text(f"{team}\nExpected Rank: {expected_rank}\nActual Rank: {actual_rank}\nELO: {elo_score}")
    select.annotation.get_bbox_patch().set(fc='white', alpha=1.0)            #Essentially on hovering you are able to see a teams name, expected_rank, actual_rank, and ELO



compute_biggest_changes(teams, elo_differences, ranking_differences)    #Calls the function from above
divisions = assign_divisions(final_avg_rankings_sorted)      #Calls the function from above and assigns it value

print('\n')
print(f'Here are the true ratings of all the teams:\n{final_avg_rankings_sorted}')      #Show raw dictionary of the final rankings
print('\n')
print(f'Here are all the teams ELOS:\n{final_avg_elos_sorted}')                        #Show raw dictionary of the final ELOs
print('\n')
print(f'These are what the divisions should be for the upcoming season:\n')
for division, division_teams in divisions.items():
    print(f"{division}: {', '.join(division_teams)}")                                 #Show how the divisions should be split up
    
plt.show()                                                                             #Graphs the scatterplot

