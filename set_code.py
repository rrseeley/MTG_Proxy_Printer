# -*- coding: utf-8 -*-
"""
Input csv format: Amount Name
10 Swamp
1 Mountain of Doom
Images in images/Mountain of Doom.jpg
Write decks in UTF-8 to manage cards like Æther Vial
"""
import sys
import os
import re
import json
import requests
import codecs



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
        raise Exception('File with the name "%s" already exists.' % output_fullpath)
        sys.exit(1)
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
    # download missing images
    if not os.path.exists(output_repository):
        os.makedirs(output_repository)
    for card_name in set(deck):
        get_set_code(card_name, output_fullpath)

def get_set_code(card_name, output_fullpath): 
    scryfall_search = 'https://api.scryfall.com/cards/search'
    # Next lines allows to pass parameters to whittle down the version of the card we are looking for.
    # 'format': 'json': defines how we want the data returned. Important for finding the set code.
    # 'q': '!"%s": query the first string. In this case card_name
    # game:paper: lets us choose which version of magic we which to search, mtgo, arena and paper are supported. We only care about paper
    # (not:promo or s:phpr): the nested parameter tells it we are not looking for any promo cards unless the set code matched phpr (HarperPrism Book Promos). This is specifically to capture the correct set for Mana Crypt and the other book promos from the mid-90s
    # unique:cards: will return 1 card for each unique art printing
    # not:judge_gift: Initially had is:nonfoil due to Gaea's Cradle judge foil having an earlier release date than the Urza's Saga version. This worked fine until you search for a card and the only printing was a foil commander in a precon
    # not:boosterfun: Boosterfun is a catchall term WotC uses to define any card with an alternate art treatment. ie: extended art, showcase, inverted, etched, borderless etc


    options = {'format': 'json', 'q': '!"%s" game:paper prefer:oldest (not:promo or s:phpr) unique:cards not:judge_gift not:boosterfun' % card_name}
    json_result = requests.get(scryfall_search, params=options)
    # 
    set_result = json_result.json()['data'][0]["set"]
    card_set = ('%s (%s) \n' % (card_name, set_result))
    with open(output_fullpath, 'a') as wfile:
        wfile.write(card_set)
        wfile.close()
    
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