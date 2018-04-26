'''import sys
import csv

tabin = csv.reader(open('CosmicMutantExport.tsv'), dialect=csv.excel_tab)
commaout = csv.writer(open('sample1.csv', 'w'), dialect=csv.excel)

ctr=0
for row in tabin:
    ctr+=1
    if ctr <500 :
        print("row id :  "+str(ctr))
        if not row:
            continue

        commaout.writerow(row)

tabin.close()
commaout.close()


import re
infile = 'CosmicMutantExport.TSV'
outfile = 'sample1.csv'
ifh = open (infile, 'r')
ofh = open (outfile, 'w+')
ctr=0

for line in ifh:
   ctr += 1


   print("row id :  " + str(ctr))
   line = re.sub('\t', '","', line)
   ofh.write('"' + line + '"')
   ofh.write("\n")

ifh.close()
ofh.close()
'''

import csv

outfile = 'sample1.csv'
ofh = open (outfile, 'w+')

with open('CosmicMutantExport.tsv') as csvfile:
    ctr1 = 0
    readCSV = csv.reader(csvfile, delimiter='\t')
    for row1 in readCSV:
        csrow=( ', '.join(row1))
        print(csrow)
        ofh.write(csrow)

ofh.close()