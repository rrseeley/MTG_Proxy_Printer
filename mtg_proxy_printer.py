# -*- coding: utf-8 -*-
"""
Input csv format: Amount Name
10 Swamp
1 Mountain of Doom
Images in images/Mountain of Doom.jpg
Write decks in UTF-8 to manage cards like Æther Vial
"""
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
    # Loads the deck txt file and reads it
    deck = []
    for line in f:
        # remove BOM if present and strip
        line = line.lstrip(str(codecs.BOM_UTF8, "utf8")).strip()
        # In the next step we are downloading any images we dont already have saved to c:\*\downloaded_images
        # We need to first remove the quantity from the line before the card name
        match = re.match('(\d+) ([ \S]+)', line)
        if match is None:
            continue
        amount = int(match.group(1))
        name = match.group(2).strip()
        deck.extend([name] * amount)
    f.close()
    return deck


def download_image(card_name, images_full_path):
    scryfall_search = 'https://api.scryfall.com/cards/search'

    # Scryfall API search reference https://scryfall.com/docs/syntax
    # The options I set are personal preference. Looks for only 1 image of a card and will pick the oldest one. 
    # Some cards release dates have promos (prerelease, judge foils etc) that will turn up first. The parameters exclude those. 
    options = {'format': 'json', 'q': '!"%s" game:paper prefer:oldest not:promo unique:cards is:nonfoil' % card_name}
    json_result = requests.get(scryfall_search, params=options)
    # When troubleshooting, uncomment the line below to get all the data that is returned from Scryfall
    # print('json content: %s' % json_result.content)
    # Once we have the card image identified, we can choose what image to download. For this script, we are using the border_crop version
    # Refer to https://scryfall.com/docs/api/images for all options
    url_result = json_result.json()['data'][0]["image_uris"]["border_crop"]
    # This gives us the URL for the exact image we are downloading
    img_result = requests.get(url_result)
    # Could be a bad name, or something else
    if img_result.status_code != 200:
        print('Error getting image for card name %s: %s' % (card_name, img_result.content))
        return False

    img_path = get_image_full_path(card_name, images_full_path)
    with open(img_path, 'wb') as wfile:
        wfile.write(img_result.content)
    print('Downloaded image of %s - Scryfall URL %s' % (card_name, url_result))


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