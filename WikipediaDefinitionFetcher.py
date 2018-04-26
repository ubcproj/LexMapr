import csv

import wikipedia
from bs4 import BeautifulSoup
import sys
import codecs

if sys.stdout.encoding != 'utf-8':
  sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf-8':
  sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

fw = open('NewFoodTypes-Definitions1.tsv', 'w', encoding="utf-8")
fw.write("FoodON Id	Food Type	Definition	Source")


with open('NewFoodTypes.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    ctr=0
    for row in readCSV:
        print(row)
        print(row[0])
        print(row[1])
        fw.write("\n" + row[0] + "	" + row[1])

        try:
            ny = wikipedia.page(row[1])
            pageurl=ny.url
            x = wikipedia.summary(row[1], sentences=1)

        except:
            x = ""
            pageurl=""
        fw.write("	" + x+" "+pageurl)

fw.close()