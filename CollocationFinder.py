import csv
import nltk
import re
import inflection
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.snowball import SnowballStemmer


inflectionExceptionList=['feces', 'faeces','sapiens','sus','gallus', 'bos','taurus', 'altus','anis','bitis','chews','pus','lotus','acanthurus']
stemmer = SnowballStemmer('english')

fw = open('enteroBaseCollocation1', 'w')
fw.write("Biosample_Id	Collection_source (Sample)	Tagged-Spacy    Cleaned Sample	Matched_Term	Resource_ID	Match_Status")

#Get all the samples from genomeTracker
genomeTrackeramplesDict={}
genomeTrackerSamplesList=[]
genomeTrackerSamplesSet=[]


def ngrams(input, n):
  input = input.split(' ')
  output = []
  for i in range(len(input)-n+1):
    output.append(input[i:i+n])
  return output



def puncTreatment(thestring,puncList):
    no_punct = ""
    for char in thestring:
        if char in puncList:
            no_punct = no_punct + " "
        else:
            no_punct = no_punct + char
    return no_punct


# Iterating over sample by reducing one token each time
def reduceChunk(thestring, starting):
    if thestring.startswith(starting):
        return thestring[len(starting):]
    return thestring


def rchop(thestring, ending):
  if thestring.endswith(ending):
    return thestring[:-len(ending)]
  return thestring




with open('enteroForFreq.csv') as csvfile:
#with open('genomeTrackerMaster.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    ctr=0
    for row in readCSV:
        if ctr>0 :
            #print(row)
            #print(row[0])
            #print(row[6])
            genomeTrackerSamplesList.append(row[1])
            samid=row[0]
            samp=row[1]
            termFreq=row[2]
            genomeTrackeramplesDict[samid.strip()]=samp.strip()
            #enterobaseSamples={row[0]: row[6]}
            #print(row[0],row[1],row[2],)
        ctr+=1
#print (enterobaseSamplesDict)
enterobaseSamplesSet=set(genomeTrackerSamplesList)
#print (enterobaseSamplesSet)


#Get all terms from resources
resourceTermsDict={}
resourceRevisedTermsDict={}
with open('ResourceTerms.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    ctr1=0
    for row in readCSV:
        #print(row[0])
        #print(row[1])
        resTerm=row[1]
        resTermRevised=resTerm.lower()
        resid=row[0]
        resourceTermsDict[resTerm.strip()] = resid.strip()
        resourceRevisedTermsDict[resTermRevised.strip()] = resid.strip()
        ctr1 += 1


#Get all synonyms from resource
synonymsDict = {}
with open('synonymTerms.csv') as csvfile:
    ctr1 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr1 > 0:
            # print(row[0])
            # print(row[1])
            synTerm = row[0]
            syn = row[1]
            synonymsDict[synTerm.strip()] = syn.strip()
        ctr1+=1


# Get all abbreviation/acronyms from resource
abbreviationDict = {}
with open('abbacroTerms.csv') as csvfile:
    ctr2 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr2 > 0:
            abbTerm = row[0]
            abbExpansion = row[1]
            abbreviationDict[abbTerm.strip()] = abbExpansion.strip()
        ctr2 += 1

# Get all abbreviation/acronyms from resource
spellingDict = {}
with open('spellings.csv') as csvfile:
    ctr7 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr7 > 0:
            term = row[0]
            expansion = row[1]
            spellingDict[term.strip()] = expansion.strip()
        ctr7 += 1



# Get all processes in samples from resource
processDict = {}
with open('processes.csv') as csvfile:
    ctr3 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr3 > 0:  # It gives a first line of headings a skip
            processTerm = row[0]
            processExpansion = row[1]
            processDict[processTerm.strip()] = processExpansion.strip()
        ctr3 += 1



# Get all processes in samples from resource
qualityDict = {}
with open('qualities.csv') as csvfile:
    ctr3 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr3 > 0:  # It gives a first line of headings a skip
            qualityTerm = row[0]
            qualityExpansion = row[1]
            qualityDict[qualityTerm.strip()] = qualityExpansion.strip()
        ctr3 += 1


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#Iterate over Samples for matching
#print (resourceTermsDict.keys())




for k,v in resourceTermsDict.items():
    sampleid1=k
    sample1=v
    #fw.write("\n"+sampleid1+" "+sample1)

pl = ['-', '_','(',')',';','/']
for k,v in genomeTrackeramplesDict.items():
    uniqueTokenList = []
    uniqueTokenSet = []

    sampleid=k
    sample=v
    trigger=False

    fw.write("\n" + sampleid + "	" + sample)

    sample = puncTreatment(sample, pl)
    sample = re.sub(' +', ' ', sample)# Extra innner spaces removed
    sampleTokens = word_tokenize(sample.lower())
    newPhrase = ""
    lemma=""

    for tkn in sampleTokens:
        if (',' in tkn):
            tkn1 = tkn.rstrip(', ')
            tkn = tkn1
        if (tkn not in inflectionExceptionList):
            lemma = inflection.singularize(tkn)
        else:
            lemma=tkn
        if (lemma in spellingDict.keys()):
            lemma = spellingDict[lemma]
        if (lemma in abbreviationDict.keys()):
            lemma = abbreviationDict[lemma]
        if (lemma in synonymsDict.keys()):
            lemma = synonymsDict[lemma]

        if (not newPhrase):
            newPhrase = lemma
        else:
            newPhrase = newPhrase + " " + lemma
    newPhraseTokens = word_tokenize(newPhrase.lower())
    fw.write("	" + newPhrase)
    for tkn2 in newPhraseTokens:
        uniqueTokenList.append(tkn2)
    if(len(uniqueTokenList)==7):
        fw.write("	" + newPhrase)


fw.close()