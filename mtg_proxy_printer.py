# -*- coding: utf-8 -*-

import sys
import math
import os
import re
import json
import requests
import codecs
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
import settings_default as settings
import time

# In main.py this is the primary job that is being executed
def mtg_proxy_print(input_filename):
    # Looks for the txt file name you input
    input_fullpath = os.path.join(settings.DECKS_FULL_PATH, input_filename)
    # If it doesnt find it, check the spelling
    if not os.path.exists(input_fullpath):
        raise Exception('File with the name "%s" doesn\'t exist.' % input_fullpath)
    # Reads the text file and loads the information into memory    
    deck = read_deck(input_fullpath)
    download_missing_images(deck, settings.IMAGES_FULL_PATH)
    print_pdf(deck, input_filename, settings.OUTPUT_PATH, settings.IMAGES_FULL_PATH)


def read_deck(input_fullpath):
    f = codecs.open(input_fullpath, "r", "utf-8")
    deck = []
    for line in f: # This part is necessary to handle DFCs that are formatted: Front_Card // Back_Card.
        line = line.lstrip(str(codecs.BOM_UTF8, "utf8")).strip()
        if "//" in line: # DFCs are formatted with the front and back separated by //
            quantity, names = line.split(' ', 1)  # Split at the first space to separate the quantity 
            quantity = int(quantity)  # Convert quantity to an integer so we generate the same number of front and back images in the PDF
            names = names.split("//")  # Split the names based on "//" into 2 lines and handle them individually
            for name in names:
                deck.extend([name.strip()] * quantity)  # Replicate the names in the deck list with the same quantity
            # Update deck after processing lines with "//"
    f.seek(0)  # Reset file pointer to the beginning of the file
    for line in f:
        line = line.lstrip(str(codecs.BOM_UTF8, "utf8")).strip()
        if "//" not in line:  # Process lines without "//"
            match = re.match(r'(\d+) ([ \S]+)', line) 
            if match is None:
                continue
            amount = int(match.group(1)) # Convert quantity to an integer so we know how many copies of the card should be on the PDF
            name = match.group(2).strip() # Grabs the card name, removing leading + trailing spaces
            deck.extend([name] * amount)
    f.close()
    return deck


def download_image(card_name, images_full_path):
    scryfall_search = 'https://api.scryfall.com/cards/search'
    spelling_check = {'format': 'json', 'q': '!"%s" game:paper' % card_name} # Searches to see if card exists in the paper format.
    spelling_result = requests.get(scryfall_search, params=spelling_check)
    if spelling_result.status_code != 200:
         print(f"Can not find {card_name} on Scryfall. Check spelling / DFC formatting in the txt and re-run.")
         sys.exit()

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
    for idx, params in enumerate(search_parameters, start=1): # Starting with the first search parameter, it will go down each one till it gets a match
        options = params
        json_result = requests.get(scryfall_search, params=options)

        if json_result.status_code == 200:      
            json_data = json_result.json()['data']
            img_urls = []

            for card_data in json_data:
                if 'image_uris' in card_data and 'border_crop' in card_data['image_uris']: #when a match is found, it will look for the URL in the image_uris string to get the URL
                    img_urls.append(card_data['image_uris']['border_crop'])
                elif 'card_faces' in card_data:
                    for face in card_data['card_faces']: # for DFC the image_uris string is nested under card_faces
                        if face.get('name') == card_name:  # there are also two image_uris strings for DFC. This will match the name to the correct URL
                            if 'image_uris' in face and 'border_crop' in face['image_uris']:
                                img_urls.append(face['image_uris']['border_crop'])
                break  # Break the loop after finding the matching card

            for index, url_result in enumerate(img_urls):
                img_result = requests.get(url_result)
                if img_result.status_code != 200: #It found a match but couldnt get the URL for the card image
                    print('Error getting image for card name %s' % card_name)
                    continue


            img_path = get_image_full_path(card_name, images_full_path)

            with open(img_path, 'wb') as wfile:
                wfile.write(img_result.content)
            found = True
            print(f"{card_name} found in {parameter_messages[idx - 1]} Frame - Scryfall URL {url_result}")
                
        time.sleep(0.1)
        if found:
            break

    return found

def get_image_full_path(card_name, images_full_path):
    return os.path.join(images_full_path, '%s.jpg' % card_name.replace("'", ""))


def download_missing_images(deck, images_full_path):
    # download missing images
    if not os.path.exists(images_full_path):
        os.makedirs(images_full_path)
    for card_name in set(deck):
        path = get_image_full_path(card_name, images_full_path)
        if not os.path.exists(path):
            download_image(card_name, images_full_path)


def print_pdf(deck, input_filename, output_path, images_full_path):
    # card size in mm
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    CARD_WIDTH = settings.CARD_WIDTH
    CARD_HEIGHT = settings.CARD_HEIGHT
    CARD_HORIZONTAL_SPACING = settings.CARD_HORIZONTAL_SPACING
    CARD_VERTICAL_SPACING = settings.CARD_VERTICAL_SPACING
    padding_left = (settings.SCALED_PAGE[0] - (3*CARD_WIDTH + (4*CARD_HORIZONTAL_SPACING))*mm)/2
    padding_bottom = (settings.SCALED_PAGE[1] - (3*CARD_HEIGHT)*mm)/2

    def make_page(cards, canvas):
        canvas.translate(padding_left, padding_bottom)
        col, row = 0, 3
        for card_name in cards:
            image = get_image_full_path(card_name, settings.IMAGES_FULL_PATH)
            if col % 3 == 0:
                row -= 1
                col = 0
            # x and y define the lower left corner of the image you wish to
            # draw (or of its bounding box, if using preserveAspectRation below).
            canvas.drawImage(image, x=(col*CARD_WIDTH+((2*col)*CARD_HORIZONTAL_SPACING))*mm, y=(row*CARD_HEIGHT+((2*row-2)*CARD_VERTICAL_SPACING))*mm, width=CARD_WIDTH*mm, height=CARD_HEIGHT*mm)
            col += 1
        canvas.showPage()
    output_filename = '%s_print.pdf' % input_filename[:-4]
    output_fullpath = os.path.join(settings.OUTPUT_PATH, output_filename)
    canvas = Canvas(output_fullpath, pagesize=settings.SCALED_PAGE)
    CARDS_ON_PAGE = 9

    def number_of_pages(deck):
        return int(math.ceil(1.0 * len(deck) / CARDS_ON_PAGE))
    for index in range(number_of_pages(deck)):
        cards = deck[(index * CARDS_ON_PAGE):(index * CARDS_ON_PAGE + CARDS_ON_PAGE)]
        canvas.setFillColor(settings.PAGE_FILL_COLOR)
        canvas.rect(x=0, y=0, width=settings.SCALED_PAGE[0], height=settings.SCALED_PAGE[1], fill=True)
        make_page(cards, canvas)
    try:
        canvas.save()
    except IOError as e:
        print('error: ', e)
        print('Save of the file %s failed. If you have the PDF file opened, close it.' % output_filename)
        sys.exit(1)
    print('%s saved.' % output_filename)
    # sheet for pack quick overview
    output_filename = '%s_overview.pdf' % input_filename[:-4]
    output_fullpath = os.path.join(settings.OUTPUT_PATH, output_filename)
    canvas = Canvas(output_fullpath, pagesize=settings.SCALED_PAGE)
    canvas.translate(padding_left, padding_bottom)
    # making list unique but maintain the order
    cards = list(set(deck))
    # cards.sort(cmp=lambda x, y: cmp(deck.index(x), deck.index(y)))
    cards.sort(key=deck.index)
    multiplicator = int(math.ceil(math.sqrt(len(cards))))
    CARD_WIDTH = 3.0 * CARD_WIDTH / multiplicator
    CARD_HEIGHT = 3.0 * CARD_HEIGHT / multiplicator
    x, y = 0, multiplicator
    for card_name in cards:
        image = get_image_full_path(card_name, settings.IMAGES_FULL_PATH)
        if x % multiplicator == 0:
            y -= 1
            x = 0
        # x and y define the lower left corner of the image you wish to
        # draw (or of its bounding box, if using preserveAspectRation below).
        canvas.drawImage(image,
                         x=x*CARD_WIDTH*mm,
                         y=y*CARD_HEIGHT*mm,
                         width=CARD_WIDTH*mm,
                         height=CARD_HEIGHT*mm)
        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(x=x*CARD_WIDTH*mm + CARD_WIDTH*mm/10,
                    y=y*CARD_HEIGHT*mm + CARD_HEIGHT*mm/1.5,
                    width=CARD_WIDTH*mm/4,
                    height=CARD_HEIGHT*mm/6,
                    stroke=1, fill=1)
        canvas.setFillColorRGB(0, 0, 0)
        canvas.drawString(x=x*CARD_WIDTH*mm + CARD_WIDTH*mm/10 + CARD_WIDTH*mm/20,
                          y=y*CARD_HEIGHT*mm + CARD_HEIGHT*mm/1.5 + CARD_HEIGHT*mm/20,
                          text="%dx" % deck.count(card_name))
        x += 1
    canvas.showPage()
    try:
        canvas.save()
    except IOError:
        print('Save of the file %s failed. If you have the PDF file opened, close it.' % output_filename)
        sys.exit(1)
    print('%s saved.' % output_filename)