import wikipedia
from bs4 import BeautifulSoup
import csv




#Declaring output files
fw = open('AllFoodonTerms-Definitions.tsv', 'w', encoding="utf-8")

#Get all terms from resources- right now in a CSV file extracted from ontologies using another script
resourceTermsDict={}
resourceRevisedTermsDict={}
with open('AllFoodonTerms.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    ctr1=0
    for row in readCSV:
        if ctr1>-1:
            miscTerm=row[2]
            resTerm=row[1]
            resTermRevised=resTerm.lower().strip()
            resid=row[0]
            resourceTermsDict[resTerm.strip()] = resid.strip()
            resourceRevisedTermsDict[resTermRevised.strip()] = resid.strip()
            ctr1 += 1
            print("ctrrrrrrrrrrr    "+str(ctr1))
            defi = None
            defititle = ""
            pageurl=""
            try:
                defi=wikipedia.page(resTerm)
                #defi = wikipedia.summary(resTerm, sentences=1)
                defititle=(str(defi.title)).lower()
                pageurl = defi.url
                print("============"+resTermRevised)
                print("==vvvvv==========" + defititle)

            except:
               defi = None
               defititle=""
               pageurl=""

            if defi and defititle == resTermRevised:
                summ = (wikipedia.summary(resTerm, sentences=2) ).encode('utf-8')   #.encode('utf-8')
                summutf=summ.decode('utf-8')
                print(str(summutf))
                fw.write("\n" + resid + "	" + miscTerm+ "	"+ resTermRevised+ "	" + str(pageurl )+ "	" + defititle+ "	" + str(summutf))
            elif defi==None:
                fw.write("\n" + resid + "	" + miscTerm+ "	"+ resTermRevised+ "	" + str(pageurl )+ "	" + defititle+ "	Missed")
        else:
            ctr1+=1

print("The task is complete now")
fw.close()
#drug=BeautifulSoup("Orange", 'lxml')





'''
import urllib
import urllib2
from beautifulsoup4 import BeautifulSoup

article= "Albert Einstein"
article = urllib.quote(article)

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this

resource = opener.open("http://en.wikipedia.org/wiki/" + article)
data = resource.read()
resource.close()
soup = BeautifulSoup(data)
print soup.find('div',id="bodyContent").p






from wikipedia import Wikipedia
from wiki2plain import Wiki2Plain

lang = 'simple'
wiki = Wikipedia(lang)

try:
    raw = wiki.article('Uruguay')
except:
    raw = None

if raw:
    wiki2plain = Wiki2Plain(raw)
    content = wiki2plain.text

'''