BlackJack-ACEFive | Card Counting | Betting Strategies | Custom Scripting
==============================================
The Simulator takes a given basic strategy(BS) as input (defined in a .csv-file) and simulates the win/loss against a random shoe with user entered number of decks.   Custom Scripting, Card Counting, Progressive Betting, ACEFive, Real-Life "Walk Away" scenarios.
<br><br>Using the Custom Scripting Tracker you can measure any data metric - Example - What happens to the House Edge when player exceeds standard deviation of maximum expected loss over a fixed number of hands/shoes

Capable of Tracking Card counts in ALL possible card counting strategies | Winn and Loss Streaks | House Edge vs Actual Edge | Load from file the same set of hands using different betting strategies and measure the differences
Simulates REAL LIFE playing environment - user can define a "WALK_AWAY" logic to end the simulation


Counting Rules and Probabilities Courtesy of wizardofodds.com
For explanation of counting card values see wizardofodds.com

### Written using python 3
User can Enable or Disable card counting in GAME_OPTIONS 

### Definition of Terms

Class definitions:
* *Hand* is a single hand of Blackjack, consisting of two or more cards - it might include a split
* *Round* is single round of Blackjack, which simulates your hand(s) against the dealer's hand
* *Shoe* is multiple decks of cards equal to SHOE_SIZE ** 52 card decks (typically BJ is played with 2, 6 or 8 decks)
* *Game* is all hands played in a total number of SHOES
* *Master* stores data and metrics across all Game(s)
* *Tracker* allows custom scripting to measure data points set by user

### Example of User Set Variables / Global Configuration
| Variable        | Description         |
| ------------- |-------------|
| *DEBUG_PRINT* | Prints to console details of every hand
| *CSV_SUMMARY* | Exports summary of results to CSV 
| *CSV_DETAILS* | Export hand DETAILS to CSV  use exported file in PLAY_FROM_FILE option 
| *DETAIL_SUMMARY* | Prints to console additional details about each simulation 
| *DB_ENABLE* | Insert results to SQLlite3 DB
| SIMULATIONS = 5 | #Simulation ends when # Shoes is reached OR Player_Bank <=BANK_RUIN OR def GetBL_WA() WALKAWAY returns True
| SHOES = 12 | #No. of shoes(games) to simulate in each simulation
| SHOE_SIZE = 5 | # No. of Decks per shoe
| SHOE_PENETRATION = 0.25 | # Remaining % of cards before shuffle 

| NO_HANDS = 2 | # No of hands(players) played each round | Set to any # of hands 1 or higher
| BET_MINIMUM = 100  | # Minimum Bet / hand -- MIN Bet over all hands should be 1-2 % of bank to avoid Ruin --
| BET_INCREMENT = 50 | # Progressive Bets - Increment wager after each win | set to 0 to disable Progressive betting
| USE212 = False | # Modified Progressive 
| BET_MAX =  BET_MINIMUM * 15 | #1500 #Max amount to bet on any one hand (pre split/double)
| RESET_BETS = True|  # Reset Bets to BET_MIN and Streaks after each shoe
| EXPECTED_LOSS_RATE = 1 | # In percent / divided by 100 at execution | Casino Expected Loss  Theo Loss / For Comps

| BANK_START = 10000 | # Player Bank
| BANK_RUIN =  0 | #0 # bank amount below for RUIN
| WA_ON_STREAK = 6 | # 0 to disable | Times player reaches WIN_STREAK to trigger automatic WALK_AWAY (WA) | uses CT_Streak[WIN_STREAK[1]] to count
| WALK_AWAY =  4000 | #BET_MINIMUM * NO_HANDS * 10 # PL before Ending Game = WA walkaway
| WALK_AWAY_TRIGGER =  12000 | #used in conjunction with TRAILING_STOP
| TRAILING_STOP = 0 | # % of PL to use as trailing stop once WALK_AWAY_TRIGGER is reached when PL is positve | set to 0 to disable
| LOSS_STOP = 0 | #trailing amount from PlrBnk MIN to earn in event of WA Cut Losses | set to 0 to disable
| LOSS_TRIGGER = 2500 | # Loss trigger point overrides LOSS_STOP to WA if PL is back to >= 0 after falling below LossTrigger | LOSS_STOP must be > 0 to enable this feature
| WALK_AWAY_BREAK = False | # True # SET TO TRUE TO BREAK SIMULATION ON WALK AWAY - if False, simulation runs ALL shoes regardless of player PL or WalkAway logic(but tracks PL independently)

| WIN_STREAK = [5,5,5]  | # [neg count,neutral count, pos count]- dflt WIN_STREAK[1]| when progessive betting the number of consecutive hands to win before resetting to BET_MINIMUM |use inconjunction with COUNT_TIER[0] 
| MAX_WIN_STREAK = 7 # MAXIMUM | # of wins streak before lowering bet / #setting bet to minimum / overrides other streak settings
| WIN_STREAK_RESET = False | # Reset progressive after streak is reached - eg. if true hand is no. 7 bet as if 2nd win, etc | when false after win streak consecutive wins are BET_MIN until a loss


### HOUSE_RULES

SIM can enable/disable the following HOUSE_RULES:

* triple7 | 3 7's counted as a blackjack *
* hitsoft17 | house hits soft 17's *
* allowsurr | house allows Late Surrender *
* 65BJ | Pay 6-5 odds on Black Jack

These House Rules are Hard Coded:

* Double down after splitting hands on any 2 cards permitted
* No BlackJack after splitting hands
* Split aces only once
    
### Strategy

6Deck_Strategies.xlsx included
Strategy is passed into the simulator as a .csv file. 

* The first column shows both player's cards added up
* The first row shows the dealers up-card
* S ... Stand
* H ... Hit
* Sr ... Surrender otherwise Hit
* RS ... Surrender; otherwise Stand
* D ... Double Down
* P ... Split

### Sample Output (short summary)

####### SIMULATION no. 1 ########<br>
PnL: $ 975.00 -- FINAL Bank: 10975.00<br>
Max Bank: $11325 at 109 | Min Bank: $8875 at 73<br>
Range: $2450 | Max Loss: $1125<br>
Avg bet/hnd: 155.88  Total bets: 18550.00<br>
<br>
House Edge: -5.882<br>
Actual Edge: 8.193<br>
Win Rate: 12.771<br>
win/bet = 5.256 %)<br>
Theo PnL: $ 1091.16<br>
Casino Exp Loss: $ -185.50<br>
<br>
######## SIMULATION no. 2 ########<br>
PnL: $ -775.00 -- FINAL Bank: 9225.00<br>
Max Bank: $11100 at 63 | Min Bank: $8125 at 37<br>
Range: $2975 | Max Loss: $1875<br>
Avg bet/hnd: 149.19  Total bets: 18350.00<br>
<br>
House Edge: 8.943<br>
Actual Edge: -6.301<br>
Win Rate: -9.400<br>
win/bet = -4.223 %)<br>
Theo PnL: $ -1641.09<br>
Casino Exp Loss: $ -183.50<br>

<<<SUMMARY OF 2 SIMULATIONS>>><br>
Total Hands : 242<br>
WalkAways: 0.0 Reason:WinStreak 0, Profit 0, TrailStop 0, Cutloss 0, RUIN 0 <br>
TotPL: $ 200.00  WA_PnL: $ 200.00 <br>
