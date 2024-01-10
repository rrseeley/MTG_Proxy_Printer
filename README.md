## Overview

MTG Proxy Printer's goal is to automate fetching your preferred frame and art for each Magic card in your deck.
There are two primary python scripts that accomplish this task. 

 - Main.py will download an image of each card in your deck and assemble it into a printable PDF for creating proxies
 - set_code.py will capture the MTG set code and collector number of each card. A new text file is created allowing you to copy/paste it into a deck builder site like Moxfield

## Installation
This portion assumes you are new to Python and will walk through each step.

**Install Python 3 (latest version)**: [https://www.python.org/downloads/](https://www.python.org/downloads/)
Check off the two boxes at the bottom and click Install Now
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/53105a71-37a8-4a2e-aca4-2aac5b5d1e31)

**Install Python Packages** 
-  Open a Command prompt: **Start -> Run -> cmd.exe**
- Change your working directory to the root: **cd c:**\ 
- Create a new folder called MTGProxy or whatever name you like: **mkdir MTGProxy**
- Change your working directory to the new folder you created: **cd c:\MTGProxy**
- Verify Python is installed: **py --version**
- Verify PIP is installed: **py -m pip --version**
If you don't see an output similar to this, it likely means python.exe was not added to PATH:
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/4ddc5456-bae6-48ff-b895-63a193b8d4a0)

- Install the Requests package: **py -m pip install requests**
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/70c4ddd8-7cef-4c05-a096-4f8b0cde35ae)

- Install the ReportLab package: **py -m pip install reportlab**
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/5b6a957f-3918-42ec-bbe3-18d2405ae921)

- Download the scripts: **At the top of the page, click the down arrow next to Code and Download ZIP**
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/b13c21bf-cb4d-4dea-ab8a-65664f82029c)

- Open the ZIP and copy the files to MTGProxy or whatever you named the folder. Your folder structure should look something like this:
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/7e461ddc-c2ff-4a96-a5f2-1db45d45912a)

- Setup is complete. Keep the Command prompt open for the next part.

## Using the script
Create a txt file with list of cards with the quantity desired. The format should be like this:

    1 Card_1 
    1 Card_2 
    1 Card_3

Save the list in the directory you created above. 
#### Creating a PDF: 
In the Command Prompt, type in main.py your_decklistname.txt
The first time you run this, it will ask to create a folder called downloaded_images and PDFs. Hit enter to create.
In this example, I am creating a printable PDF of the Power 9. The output lists the frame and the URL of the image:
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/c0441ce6-885d-4848-aaba-5b4c63a5962c)

Navigate to the PDFs directory and you will see the printable PDF 
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/e4b9cc59-dfda-47db-968c-b096ff378c33)

#### Creating a txt with the Set Code + Collector Number of each card

In the Command Prompt, type in set_code.py your_decklistname.txt
The first time you run this, it will ask to create a folder called set_added. Hit enter to create.
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/d0a952a4-cd33-47db-a050-6915e4a48e97)

Navigate to the set_added directory and you will see a new txt that has added the set and collector number to each card

    Ancestral Recall (lea) 47
    Time Walk (lea) 83
    Mox Ruby (lea) 264
    Mox Jet (lea) 262
    Mox Pearl (lea) 263
    Black Lotus (lea) 232
    Timetwister (lea) 84
    Mox Emerald (lea) 261
    Mox Sapphire (lea) 265
![enter image description here](https://github.com/rrseeley/MTG_Proxy_Printer/assets/57955702/7d816ef0-9fc8-472a-ba06-0f6bb1096ed7)



