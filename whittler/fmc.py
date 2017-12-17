
# Increments the Fuck Me Counter. If a numeric argument is given, then it sets the counter to that
# value. Only mods can set the value.
fuck_me_counter = 0
def fmc(user_data, message):
    global fuck_me_counter
    
    # Check if an argument was given.
    if len(message):
    
        # If the caller was not a mod, put them in their place.
        if not user_data["mod"]:
            return "Only mods can directly set the Fuck Me Counter."
        
        # Try to parse the value that was given, and report if it is not a valid number.
        try:
            new_val = int(message)
            fuck_me_counter = new_val
            return "Fuck Me Counter set to " + message
        except:
            return message + " isn't a number..."
    else:
        # On success, increment and print the Fuck Me Counter.
        fuck_me_counter += 1
        return "Fuck Me Counter: " + str(fuck_me_counter)
