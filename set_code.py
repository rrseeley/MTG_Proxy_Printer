
import sys
import os
import re
import json
import requests
import codecs
import time 



def mtg_proxy_print(input_filename):
    ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
    output_repository = "%s/set_added" % ROOT_PATH
    DECKS_FULL_PATH = ROOT_PATH
    input_fullpath = os.path.join(DECKS_FULL_PATH, input_filename)
    output_fullpath = os.path.join(output_repository, input_filename)
    if not os.path.exists(input_fullpath):
        raise Exception('File with the name "%s" doesn\'t exist.' % input_fullpath)
        sys.exit(1)
    if os.path.exists(output_fullpath):
        user_input = input(f"Directory '{output_fullpath}' already exists. Hit Enter to overwrite or N to exit: ")
        if user_input.lower() in ('yes', '', 'y'):
            with open(output_fullpath, 'w', encoding='utf-8') as wfile:
                wfile.close() 
        else:
            print("Exiting the script")
            sys.exit()
    deck = read_deck(input_fullpath)
    magic_set_code(deck, output_fullpath, output_repository)
        
def read_deck(input_fullpath):
    f = codecs.open(input_fullpath, "r", "utf-8")
    # parse file into deck list
    deck = []
    for line in f:
        # remove BOM (Byte Order Mark) if present and strip
        line = line.lstrip(str(codecs.BOM_UTF8, "utf8")).strip()
        # an update to re? needed to add a raw string in front of '(\d+) in order to properly escape
        match = re.match(r'(\d+) ([ \S]+)', line)
        if match is None:
            continue
        amount = int(match.group(1))
        name = match.group(2).strip()
        deck.extend([name] * amount)
    f.close()
    return deck

def magic_set_code(deck, output_fullpath, output_repository):
    
    if not os.path.exists(output_repository):
        user_input = input(f"Directory '{output_repository}' doesn't exist. Hit Enter to create it or N to exit: ")
        if user_input.lower() in ('yes', '', 'y'):
            os.makedirs(output_repository)
            print(f"Directory '{output_repository}' created.") 
        else:
            print("Exiting the script")
            sys.exit()
        
    for card_name in set(deck):
        get_set_code(card_name, output_fullpath)
        

def get_set_code(card_name, output_fullpath): 
    scryfall_search = 'https://api.scryfall.com/cards/search'
    search_parameters = [
            # Search for 1993 / 1997 frame
            {'format': 'json', 'q': '!"%s" game:paper (frame:1993 or frame:1997) prefer:oldest (not:promo or s:phpr) unique:cards not:judge_gift not:boosterfun -set:sld lang:en' % card_name},
            # Search for Retro frame
            {'format': 'json', 'q': '!"%s" game:paper frame:1997 prefer:oldest unique:cards (is:boosterfun or is:judge_gift or is:promo or set:sld) -a:malone lang:en' % card_name},
            # Search for 2003 / Future frame
            {'format': 'json', 'q': '!"%s" game:paper (frame:2003 or frame:future) prefer:oldest not:promo unique:cards not:judge_gift not:boosterfun lang:en' % card_name},
            # Search for 2015 Frame Extended art
            {'format': 'json', 'q': '!"%s" game:paper prefer:oldest unique:cards is:extended lang:en' % card_name},
            # Take whatever is available
            {'format': 'json', 'q': '!"%s" game:paper prefer:oldest unique:cards not:promo not:boosterfun not:showcase not:etched -frame:inverted lang:en' % card_name},    
    ]

            # Message for each parameter set
    parameter_messages = [
            "93/97",
            "Retro",
            "03/Future",
            "Extended",
            "Basic Bitch",
    ]
    found = False
    for idx, params in enumerate(search_parameters, start=1):
        options = params
        json_result = requests.get(scryfall_search, params=options)
        
        if json_result.status_code == 200:
            data = json_result.json()
            if data.get('data'):
                set_result = data['data'][0]["set"]
                card_number = data['data'][0]["collector_number"]
                card_set = '%s (%s) %s\n' % (card_name, set_result, card_number)
                
                with open(output_fullpath, 'a', encoding='utf-8') as wfile:
                    wfile.write(card_set)
                    wfile.close()
                found = True
                print(f"{card_name} found in {parameter_messages[idx - 1]} Frame")  # Adjust index to match parameter numbering
                break  # Exit the loop if a card is found
        
        # Print the custom message for the current parameter set
        
        
        # Introduce a delay before retrying to avoid hitting API rate limits
        time.sleep(0.1)  # Adjust the delay time as needed
        
    if not found:
        print(f"Card '{card_name}' not found with any of the provided parameters.")
     
    
try:
    input_filename = os.path.basename(sys.argv[1])
    
except IndexError:
    print('Missing parameter! First parameter needs to be the txt filename in format deckname.txt')
    print('Example: mtg_proxy_printer.py goblin.txt')
    sys.exit(1)

try:
    mtg_proxy_print(input_filename)
    print('My work is done.')
except Exception as msg:
    print(msg)
