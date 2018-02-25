# Copyright (c) 2017 AlaskanEmily
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random
import math

# This handles the rename in Python 3
try:
    import httplib as http_client
except:
    import http.client as http_client

try:
    import urllib.parse.urlencode as urlencode
except:
    from urllib import urlencode

# To make the guestlist work:
# Create a pastebin account and go to https://pastebin.com/api#1
# Enter your developer key below:
pastebin_key = "65fa91203e65620bc5ecb2b9a6790743"

# NESParty actions:
# Add Game
# Remove Game
# Next Game
# Random Game
# Next Sub Game
# Random Sub Game
# Remove your own submission
# Remove all submissions from a certain user
# Undo to put the last Next Game back in the list
# Game to display the last game chosen

# Params:
# Make older games more likely
# Add limit based on the one who set it

# This is the maximum number of games per user. If it's -1, then it's infinite.
max_per_user = 1

# You can give subs a different max than regular users.
max_per_sub = 2

# This is the chance multiplier for the age of an entry. Increasing this increases the liklihood
# that games that were added earlier will be picked.
# For instance, if it is set to 2.0, then the oldest game is twice as likely to be picked than the
# newest game.
# Setting it to 1.0 means that all games are the same chance.
time_multiplier = 1

games = []

guest_list_url = ""

# The list of all picked games. An undo will pull from here and put back on to the games list
picked_games = []

# Private function. Picks a game for the given user. If user is empty, then any user is OK.
# If sub_only, then only subs can be chosen.
def pick(games, user, sub_only):
    
    num_games = len(games)
    
    if num_games == 1:
        return games[0]
    
    # Generate a weighted random number.
    rnd = random.random()
    r = rnd
    
    # math.pow is expensive, avoid it if it's not necessary.
    if time_multiplier != 1.0:
        r = math.pow(r, 1.0 / time_multiplier)
    
    if r >= 1.0 or r <= 0.0:
        print ("Error in math: Random value " + str(rnd) + " ended up as " + str(r))
    
    # R should now be in the range of 0.0 to 1.0.
    if r >= 1.0:
        r = 1.0
    elif r <= 0.0:
        r = 0.0
    
    # The inverse-exponent function above has an inverted chance to what we want.
    r = 1.0 - r
    
    print ("R is " + str(r))
    
    # Now that we have a random number, use it to pick a game.
    
    # Find out how many values we can actually use.
    if sub_only or len(user) != 0:
        for game in games:
            use_game = True
            if sub_only and not game["sub"]:
                use_game = False
            elif len(user) != 0 and game["user"] != user:
                use_game = False
            if not use_game:
                num_games -= 1
    
    game_num = math.floor((r * num_games) + 0.5)
    
    i = 0
    for game in games:
            use_game = True
            if sub_only and not game["sub"]:
                use_game = False
            elif len(user) != 0 and game["user"] != user:
                use_game = False
            if use_game:
                if i == game_num:
                    return game
                else:
                    i += 1
    
    # Should not have gotten here...
    return games[0]

def add_game(user_data, message):
    global guest_list_url
    print (len(message))
    if len(message) == 0:
        return "You need to enter a game name"
    
    sub = user_data["sub"]
    user = user_data["user"]
    
    if sub:
        max = max_per_sub
    elif user_data["owner"]:
        max = -1
    else:
        max = max_per_user
    
    if max != -1:
        # Count the number of entries this user already has.
        count = 0
        for game in games:
            if game["user"] == user:
                count += 1
                if count == max:
                    return user + " already has " + str(max) + " games in the list!"
    
    game = {
        "sub":sub,
        "user":user,
        "game":message
    }
    games.append(game)
    
    num_games = len(games)
    
    guest_list_url = ""
    # This is kind of pointless, but it's fun.
    return user + " added " + message + " as game #" + str(num_games)

def remove_game(user_data, message):
    global guest_list_url
    game_num = 0
    try:
        game_num = int(message) -1
    except:
        return "games are removed by number"
#        i = 0
#        while i < len(games):
#            if games[i]["game"].startswith(message):
#                game_num = i
#                break
#            i += 1
    
    try:
        if not user_data["mod"]:
#            if games[game_num]["user"] != user_data["user"]:
            return "Only a mod can remove individual games"
        
        del games[game_num]
        # Clear the guest list URL so it will have to be regenerated.
        guest_list_url = ""
        return "Removed game number " + str(game_num + 1 )
    except:
        pass
    
    return "Could not find game " + message

def remove_user(user_data, message):
    global guest_list_url
    user = user_data["user"]
    print (user)
    print (user_data['user'])
    if user_data["user"] != user:
        return "Only mods can remove another user"
    
    i = 0
    removed = 0
    while i < len(games):
        if games[i]["user"] == user:
            del games[i]
            removed += 1
        else:
            i += 1
    
    if removed != 0:
        # Clear the guest list URL so it will have to be regenerated.
        guest_list_url = ""
    
    return "Removed " + str(removed) + " game(s) for user " + user

def clear(user_data, message):
    global guest_list_url
    global games
    if not user_data["mod"]:
        return "Only mods can end the party"
    guest_list_url = ""
    games = []
    return ""

def get_game(user_data, message):
    global guest_list_url
    global games
    global picked_games
    if not user_data["mod"]:
        return "Only mods can get the next game"
    
    if len(games) == 0:
        return "No games yet!"
    
    lower_message = message.lower()
    subs_only = lower_message.find("sub") != -1
    
    game = pick(games, "", subs_only)
    
    picked_games.append(game)
    
    if lower_message.find("keep") == -1:
        games.remove(game)
    
    guest_list_url = ""
    return "The game was " + game["game"] + ", invited by " + game["user"]

def current_game(user_data, message):
    if len(picked_games) == 0:
        return "No current game"
    else:
        return "Current game is " + picked_games[-1]["game"]

def set_game(user_data, message):
    if not user_data["mod"]:
        return "Only modes can set the game"
    # Add a dummy game.
    picked_games.append({
        "sub":False,
        "user":False,
        "game":message
    })

def undo(user_data, message):
    global guest_list_url
    
    if not user_data["mod"]:
        return "Only modes can undo"
    if len(picked_games) == 0:
        return "No game to undo"
    
    # Pop the last picked game.
    game = picked_games.pop()
    
    if game["user"]:
        # If the game was "real", that is not added using set_game, put it back on the queue
        games.append(game)
        guest_list_url = ""
        return "Put game " + game["game"] + " back onto the queue"
    else:
        if len(picked_games):
            return "Reset the current game to " + picked_games[-1]["game"]
        else:
            return "Unset the current game"

def guestlist(user_data, message):
    global guest_list_url
    if len(pastebin_key) == 0:
        return ""
    if len(games) == 0:
        return "No games yet!"
    elif len(guest_list_url):
        return guest_list_url
    else:
        # Create a new pastebin with the games list.
        game_body = ""
        
        for game in games:
            game_body += game["game"] + ", invited by " + game["user"] + "\n"
        
        postfields = {
            "api_dev_key":pastebin_key,
            "api_option":"paste",
            "api_paste_private":"1",
            "api_paste_expire_date":"1H",
            "api_paste_code":game_body
        }
        headers = {
            "Content-Type":"application/x-www-form-urlencoded"
        }
        
        connection = http_client.HTTPConnection("pastebin.com", 80)
        params = urlencode(postfields)
        print (params)
        connection.request("POST", "/api/api_post.php", params, headers)
        
        response = connection.getresponse()
        
        print (str(response.status) + " " + response.reason)
        
        guest_list_url = response.read()
        
        print (guest_list_url)
        if guest_list_url[0] == '<':
            guest_list_url = ""
        
        connection.close()
        return guest_list_url
