# Imports from different packages used
import csv
import nltk
import re
import inflection
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import pos_tag, ne_chunk
# from nltk.stem.snowball import SnowballStemmer
# from spacy.en import English
import wikipedia
import itertools
from dateutil.parser import parse

words = set(nltk.corpus.words.words())

# Initializations etc.
# parser = English()
# stemmer = SnowballStemmer('english')

# Declaring output files
fw = open('GenepioGazMatched-Ver1.tsv', 'w')
fw1 = open('GenepioGazMatched-Missing-Ver1.tsv', 'w')
# fw = open('genomeTrakerTermMatcherVer7.tsv', 'w')
fw.write(
    "Sample_Id" + "\t" + "Sample_Desc" + "\t" + "Cleaned_Sample" + "\t" + "Phrase_POS_Tagged" + "\t" + "Probable_Candidate_Terms" + "\t" + "Matched_Term" + "\t" + "All_matched_Terms_with_Resource_IDs" + "\t" + "Retained_Terms_with_Resource_IDs" + "\t" + "Match_Status" + "\t" + "Remaining_Tokens")

##Get all the samples from database
samplesDict = {}
samplesList = []
samplesSet = []
remainingTokenSet = []

# METHODS USED
'''
#Method to get entities using Spacy
def entities(example, show=False):
    if show: print(example)
    parsedEx = parser(example)
    #print("-------------- entities only ---------------")
    # if you just want the entities and nothing else, you can do access the parsed examples "ents" property like this:
    ents = list(parsedEx.ents)
    tags = {}
    for entity in ents:
        # print(entity.label, entity.label_, ' '.join(t.orth_ for t in entity))
        term = ' '.join(t.orth_ for t in entity)
        if ' '.join(term) not in tags:
            tags[term] = [(entity.label, entity.label_)]
        else:
            tags[term].append((entity.label, entity.label_))
    return tags

'''


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


def is_date(string):
    try:
        parse(string)
        return True
    except ValueError:
        return False


# Method to get ngrams with a given value of n
def ngrams(input, n):
    input = input.split(' ')
    output = []
    for i in range(len(input) - n + 1):
        output.append(input[i:i + n])
    return output


def deConcatenateString(term):
    output = {}
    lastIndex = len(term)
    for i in range(1, lastIndex + 1):
        firstTerm = (term[:i])
        secondTerm = (term[i:])

        if ((firstTerm.lower() in words or not firstTerm.isalpha()) and (
                        secondTerm.lower() in words or not secondTerm.isalpha())):
            output.append(firstTerm)
            output.append(secondTerm)
    return output


def preProcess(tkn):
    if ('\'s' in tkn):
        tkn1 = tkn.replace("\'s", "")
        tkn = tkn1
    if (',' in tkn):  # comma concatenated in token is get rid of
        tkn1 = tkn.rstrip(', ')
        tkn = tkn1
    if ('.' in tkn):  # dot concatenated in token is get rid of
        tkn1 = tkn.rstrip('. ')
        tkn = tkn1
    return tkn


def addSuffixFoodProduct(input):
    output = input + " " + str("food product")
    return output


def addSuffixProduct(input):
    output = input + " " + str("product")
    return output


def allPermutations(input):
    lst = input.split()
    setPerm = set(itertools.permutations(lst))
    return setPerm


def retainedPhrase(termList):
    returnedSetFinal = []
    print(termList)
    termDict = {}
    termDictAdd = {}
    wordList = []
    retainedSet = []
    returnedSet = []
    termList = termList.replace("{", "")
    termList = termList.replace("}", "")
    termList = termList.replace("'", "")
    lst = termList.split(",")
    # print("ddddddddddddddddeeeee   " + str(lst))
    for x in lst:
        lst2 = x.split(":")
        a = lst2[0]
        b = lst2[1]
        if a.strip() not in termDict.keys():
            termDict[a.strip()] = b.strip()
            wordList.append(a.strip())
            retainedSet.append(a.strip())
        if a.strip() in termDict.keys():
            termDictAdd[a.strip()] = b.strip()
            wordList.append(a.strip())
            retainedSet.append(a.strip())

    for wrd in wordList:
        for othrwrd in wordList:
            if wrd in retainedSet and wrd in othrwrd and wrd != othrwrd:
                retainedSet.remove(wrd)

    for item in retainedSet:
        if item in termDict.keys():
            ky = termDict[item]
            returnItem = item + ":" + ky
            returnedSet.append(returnItem)
        if item in termDictAdd.keys():
            ky = termDictAdd[item]
            returnItem = item + ":" + ky
            returnedSet.append(returnItem)

        returnedSetFinal = set(returnedSet)
    return returnedSetFinal


def wikiDefinition(term):
    output = ""
    try:
        defi = wikipedia.page(term)
        # defi = wikipedia.summary(resTerm, sentences=1)
        defititle = (str(defi.title)).lower()
        defiurl = (str(defi.url))
    except:
        defi = None
        defititle = ""
    if defi and defititle == term:
        summ = wikipedia.summary(term, sentences=1)
        output = term + ": (" + defiurl + "):" + str(summ.encode('utf-8'))
    return output


# Method to get the punctuation treatment -only removes a punctuation and replaces it with space
def puncTreatment(thestring, puncList):
    finalSample = ""
    sampleTokens = word_tokenize(thestring)
    for token in sampleTokens:
        no_punct = ""
        number_result = is_number(token)
        date_result = is_date(token)
        if (number_result is True or date_result is True):
            no_punct = token
        else:
            for char in token:
                if char in puncList:
                    no_punct = no_punct + " "
                else:
                    no_punct = no_punct + char
        if (finalSample):
            finalSample = finalSample + " " + no_punct
        else:
            finalSample = no_punct

    return finalSample


# Method- Iterating over string of multitokens by reducing one token each time
def reduceChunk(thestring, starting):
    if thestring.startswith(starting):
        return thestring[len(starting):]
    return thestring


# Method- Iterating over string of multitokens by reducing one token each time staring from end
def rchop(thestring, ending):
    if thestring.endswith(ending):
        return thestring[:-len(ending)]
    return thestring


# Get all inflection exception words from resource in CSV file format
# inflectionExceptionList=['fraenata','sepsis','salta','livia','lacertilia','kofta','horchata','georgia','feaces','excreta','enteritis','gastroenteritis','dhania','clarias','chinemys', 'nigricans','chalpata','chanos','bettongia','mississippiensis','acanthurus','alces','altus','anas','anis','anoles','','anolis','bitis','bos','canis','catus','cecal','chews','dasyurus','debris','domesticus','esomus','faeces','fecal','feces','felis','gallus','leucophaeus','lotus','lupus','ovis','puntius','pus','sapiens','sus','taurus','varanus','viverrinus']

inflectionExceptionList = []
with open('inflection-exceptions.csv') as csvfile:
    ctr2 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr2 > 0:
            abbTerm = row[0]
            inflectionExceptionList.append(abbTerm.strip().lower())
        ctr2 += 1

stopWordsList = []
with open('mining-stopwords.csv') as csvfile:
    ctr2 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr2 > 0:
            abbTerm = row[0]
            stopWordsList.append(abbTerm.strip().lower())
        ctr2 += 1

# Method to read from sample master file in CSV format
# with open('enteroForFreq.csv') as csvfile:
# with open('genomeTrackerMaster.csv') as csvfile:
# with open('GRDI-UniqueSamples.csv') as csvfile:
# with open('bccdcsample.csv') as csvfile:
with open('genepioConutry.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    ctr = 0
    for row in readCSV:
        if ctr > 0:  # skips the first row in CSV file as header row
            samplesList.append(row[1])
            samid = row[0]
            samp = row[1]
            # termFreq=row[2]
            samplesDict[samid.strip()] = samp.strip()
        ctr += 1
enterobaseSamplesSet = set(samplesList)
# print (enterobaseSamplesSet)



# Get all terms from resources- right now in a CSV file extracted from ontologies using another script
resourceTermsDict = {}
resourceRevisedTermsDict = {}
resourceTermsIDBasedDict = {}
with open('ResourceTerms-Gaz.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    ctr1 = 0
    for row in readCSV:
        resTerm = row[1]
        resTermRevised = resTerm.lower()

        resid = row[0]
        resourceTermsDict[resTerm.strip()] = resid.strip()
        resourceTermsIDBasedDict[resid.strip()] = resTerm.strip()
        resourceRevisedTermsDict[resTermRevised.strip()] = resid.strip()
        ctr1 += 1
print(str(resourceTermsDict))
# Get all synonyms from resource in CSV file format
synonymsDict = {}
with open('synonymTerms.csv') as csvfile:
    ctr1 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr1 > 0:  # skips the first row in CSV file as header row
            synTerm = row[0]
            syn = row[1]
            synonymsDict[synTerm.strip()] = syn.strip()
        ctr1 += 1

# Get all abbreviation/acronyms from resource in CSV file format
abbreviationDict = {}
abbreviationLowerDict = {}
with open('abbacroTerms.csv') as csvfile:
    ctr2 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr2 > 0:
            abbTerm = row[0]
            abbExpansion = row[1]
            abbreviationDict[abbTerm.strip()] = abbExpansion.strip()
            abbreviationLowerDict[abbTerm.strip().lower()] = abbExpansion.strip()
        ctr2 += 1

# Get all spelling mistake examples from resource
spellingDict = {}
spellingLowerDict = {}
with open('spellings.csv') as csvfile:
    ctr7 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr7 > 0:
            term = row[0]
            expansion = row[1]
            spellingDict[term.strip()] = expansion.strip()
            spellingLowerDict[term.strip().lower()] = expansion.strip()
        ctr7 += 1

# Get all processes from resource
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

# Get all qualities in samples from resource
qualityDict = {}
qualityLowerDict = {}
with open('qualities.csv') as csvfile:
    ctr3 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr3 > 0:  # It gives a first line of headings a skip
            qualityTerm = row[0]
            qualityExpansion = row[1]
            qualityDict[qualityTerm.strip()] = qualityExpansion.strip()
            qualityLowerDict[qualityTerm.strip().lower()] = qualityExpansion.strip()
        ctr3 += 1

# Get all collocations from resource
collocationDict = {}
with open('collocations.csv') as csvfile:
    ctr = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr > 0:  # It gives a first line of headings a skip
            collocationTerm = row[0]
            collocationId = row[1]
            collocationDict[collocationTerm.strip()] = collocationId.strip()
        ctr += 1
        #

# ++++++++++++++++++++++++++++++++ MAIN TEXT MINING PIPELINE ++++++++++++++++++++++++++++++++++++++++++++++

# ===For getting all the permutations of Resource Terms
resourcePermutationTermsDict = {}
# Iterate over samples for matching to ontology terms
for k, v in resourceRevisedTermsDict.items():
    resourceid = v
    resource = k
    # fw1.write("\n" + resourceid)
    sampleTokens = word_tokenize(resource.lower())
    # for tkn in sampleTokens:
    if len(sampleTokens) < 5:
        setPerm = allPermutations(resource)
        print("sssssssssssssss=== " + str(setPerm))
        for perm in setPerm:
            permString = ' '.join(perm)
            resourcePermutationTermsDict[permString.strip()] = resourceid.strip()

status = ""  # Status of Matching to be displayed for evry rule/section

# some declarations needed
pl = ['-', '_', '(', ')', ';', '/', ':', '%']  # Current punctuationList for basic treatment

# ===Here the main Iteration starts
# Iterate over samples for matching to ontology terms

coveredAllTokensSet = []
remainingAllTokensSet = []
for k, v in samplesDict.items():
    sampleid = k
    sample = v

    trigger = False
    # tg = entities(sample.lower()) #From Spacy General Tagger
    fw.write("\n" + sampleid + "	" + sample)  # + "	" +str(tg))

    sample = puncTreatment(sample, pl)
    sample = re.sub(' +', ' ', sample)  # Extra innner spaces removed
    sampleTokens = word_tokenize(sample.lower())
    newPhrase = ""
    lemma = ""

    # ===Few preliminary thigs- Inflection,spelling mistakes, Abbreviations, acronyms, foreign words, Synonyms taken care of
    for tkn in sampleTokens:

        lemma = preProcess(tkn)  # Some preprocessing Steps

        # ===This will create a cleaned sample after above treatments [Here we are making new phrase now in lower case]
        if (not newPhrase and lemma.lower() not in stopWordsList):
            newPhrase = lemma.lower()
        elif (lemma.lower() not in stopWordsList):
            newPhrase = newPhrase + " " + lemma.lower()
        newPhrase = re.sub(' +', ' ', newPhrase)  # Extra innner spaces removed


    newSampleTokens = word_tokenize(newPhrase.lower())

    fw.write("	" + newPhrase )

    # This part works for getting the Candidate phrase based on POS tagging and applied rule
    qualityList = []
    phraseStr = ""
    prevPhraseStr = ""
    prevTag = "X"


    # Rule1: Annotate all the empty samples
    if not sample:
        status = "Sample is Empty"
        fw.write("	--" + "	--" + "\t" + "\t" + status)
        trigger = True

    # Rule2: Annotate all the Full Term Matches of Terms without any treatment
    if (sample in resourceTermsDict.keys() and not trigger):
        resourceId = resourceTermsDict[sample]
        status = "Full Term Match-ADirectMatch"
        fw.write("	" + sample + "	" + "[" + (sample + ":" + resourceId) + "]" + "\t" + "[" + (
        sample + ":" + resourceId) + "]" + "\t" + status)
        trigger = True
    # Comment- Above section is OK -validated


    if (sample.lower() in resourceTermsDict.keys() and not trigger):
        resourceId = resourceTermsDict[sample.lower()]
        status = "Full Term Match-Change of Case"
        fw.write("	" + sample.lower() + "	" + "[" + (sample.lower() + ":" + resourceId) + "]" + "\t" + "[" + (
        sample.lower() + ":" + resourceId) + "]" + "\t" + status)
        trigger = True  # resourcePermutationTermsDict
    elif (sample.lower() in resourceRevisedTermsDict.keys() and not trigger):
        resourceId = resourceRevisedTermsDict[sample.lower()]
        status = "Full Term Match-Change of Case of Resource"
        fw.write("	" + sample.lower() + "	" + "[" + (sample.lower() + ":" + resourceId) + "]" + "\t" + "[" + (
        sample.lower() + ":" + resourceId) + "]" + "\t" + status)
        trigger = True
    elif (sample.lower() in resourcePermutationTermsDict.keys() and not trigger):
        resourceId = resourcePermutationTermsDict[sample.lower()]
        status = "Full Term Match-Permutation of Resource"
        fw.write("	" + sample.lower() + "	" + "[" + (sample.lower() + ":" + resourceId) + "]" + "\t" + "[" + (
        sample.lower() + ":" + resourceId) + "]" + "\t" + status)
        trigger = True



fw.close()
fw1.close()

'''
for tkn in sampleTokens:

    if (tkn in processDict.keys()):
        proc = processDict[tkn]
        partialMatchedList.append(tkn)
    if (tkn in qualityDict.keys()):
        quality = qualityDict[tkn]
        partialMatchedList.append(tkn)
    if (tkn in resourceTermsDict.keys()):
        # quality = qualityDict[tkn]
        partialMatchedList.append(tkn)
    elif (tkn in resourceRevisedTermsDict.keys()):
        partialMatchedList.append(tkn)



           for matchstring in partialMatchedSet:
            if( matchstring in processDict.keys()):
                resourceId=processDict[matchstring]
            elif (matchstring in qualityDict.keys()):
                resourceId = qualityDict[matchstring]
            elif (matchstring in resourceTermsDict.keys()):
                resourceId = resourceTermsDict[matchstring]
            elif (matchstring in resourceRevisedTermsDict.keys()):
                resourceId = resourceRevisedTermsDict[matchstring]

            partialMatchedResourceList.append(matchstring +":"+resourceId)









             # newChunk = reduceChunk(newChunk, tkn + " ")
            newChunk1 = ngrams(newChunk, 1)
            # print("mmmmmmmmm 2222222222222" + str(newChunk2))
            for nc in newChunk1:
                grm = ' '.join(nc)
                # print("llllllll22222222222 " + grm)
                if (grm in resourceTermsDict.keys()):
                    # resourceId = resourceTermsDict[newChunk]
                    partialMatchedList.append(grm)
                elif (grm in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grm)
'''
'''
#print (resourceTermsDict.keys())
for k,v in resourceTermsDict.items():
    sampleid1=k
    sample1=v
    #fw.write("\n"+sampleid1+" "+sample1)





    if ( not trigger):
        print("We will go further with other rules More")
        sampleTokens1 = word_tokenize(newPhrase.lower())
        sampleTokens  =sampleTokens1[::-1]

        partialMatchedList = []
        partialMatchedResourceList = []
        partialMatchedSet=[]
        newChunk=newPhrase.lower()

        for tkn in sampleTokens:
            newChunk = rchop(newChunk, " "+tkn)
            if (newChunk in resourceTermsDict.keys()):
                #resourceId = resourceTermsDict[newChunk]
                partialMatchedList.append(newChunk)

        partialMatchedSet = set(partialMatchedList)
        for matchstring in partialMatchedSet:
            resourceId = resourceTermsDict[matchstring]
            partialMatchedResourceList.append(resourceId)
        if (len(partialMatchedSet) > 0):
            fw.write("	" + str(partialMatchedSet) + "	" + str(
                partialMatchedResourceList) + "	GComponent Match from End")
            trigger = True


1. Remove all the brackets,
    else:
        fw.write("	--" + "	--" + "	No Match")

L[::-1]


    if (not trigger):
        print("We will go further with other rules")
        sampleTokens = word_tokenize(sample.lower())
        newPhrase = ""
        for tkn in sampleTokens:
            if (tkn in abbreviationDict.keys()):
                lemma = abbreviationDict[tkn]
            else:
                lemma = tkn

            if (not newPhrase):
                newPhrase = lemma
            else:
                newPhrase = newPhrase + " " + lemma
        sampleTokens1 = word_tokenize(newPhrase.lower())
        partialMatchedList = []
        partialMatchedResourceList = []
        partialMatchedSet = []
        newChunk = newPhrase.lower()
        for tkn1 in sampleTokens1:
            newChunk = reduceChunk(newChunk, tkn1 + " ")
            if (newChunk in resourceTermsDict.keys()):
                # resourceId = resourceTermsDict[newChunk]
                partialMatchedList.append(newChunk)

        partialMatchedSet = set(partialMatchedList)
        for matchstring in partialMatchedSet:
            resourceId = resourceTermsDict[matchstring]
            partialMatchedResourceList.append(resourceId)
        if (len(partialMatchedSet) > 0):
            fw.write("	" + str(partialMatchedSet) + "	" + str(
                partialMatchedResourceList) + "	GComponent Match from Start -using abbre")
            trigger = True


'''

'''


 if (not trigger):
                print("We will go further with other rules")
                sampleTokens = word_tokenize(newPhrase.lower())
                partialMatchedList = []
                partialMatchedResourceList = []
                partialMatchedSet = []
                print("=======333=======" + sample.lower())
                print("---3333-----------" + newPhrase.lower())
                newChunk = newPhrase.lower()
                for tkn in sampleTokens:
                    if (tkn in processDict.keys()):
                        proc = processDict[tkn]
                        partialMatchedList.append(tkn)
                    if (tkn in qualityDict.keys()):
                        quality = qualityDict[tkn]
                        partialMatchedList.append(tkn)
                    if (tkn in resourceTermsDict.keys()):
                        # quality = qualityDict[tkn]
                        partialMatchedList.append(tkn)

                    # newChunk = reduceChunk(newChunk, tkn + " ")
                    newChunk1 = ngrams(newChunk, 5)
                    print("mmmmmmmmm 55555555" + str(newChunk1))
                    for nc in newChunk1:
                        grm = ' '.join(nc)
                        print("llllllll5555555 " + grm)
                        if (grm in resourceTermsDict.keys()):
                            # resourceId = resourceTermsDict[newChunk]
                            partialMatchedList.append(grm)

                    # newChunk = reduceChunk(newChunk, tkn + " ")
                    newChunk1 = ngrams(newChunk, 4)
                    print("mmmmmmmmm 444444444" + str(newChunk1))
                    for nc in newChunk1:
                        grm = ' '.join(nc)
                        print("llllllll 444444444" + grm)
                        if (grm in resourceTermsDict.keys()):
                            # resourceId = resourceTermsDict[newChunk]
                            partialMatchedList.append(grm)

                    # newChunk = reduceChunk(newChunk, tkn + " ")
                    newChunk1 = ngrams(newChunk, 3)
                    print("mmmmmmmmm 3333333333" + str(newChunk1))
                    for nc in newChunk1:
                        grm = ' '.join(nc)
                        print("llllllll 33333333333" + grm)
                        if (grm in resourceTermsDict.keys()):
                            # resourceId = resourceTermsDict[newChunk]
                            partialMatchedList.append(grm)

                    # newChunk = reduceChunk(newChunk, tkn + " ")
                    newChunk1 = ngrams(newChunk, 2)
                    print("mmmmmmmmm 2222222222222" + str(newChunk1))
                    for nc in newChunk1:
                        grm = ' '.join(nc)
                        print("llllllll22222222222 " + grm)
                        if (grm in resourceTermsDict.keys()):
                            # resourceId = resourceTermsDict[newChunk]
                            partialMatchedList.append(grm)


                partialMatchedSet = set(partialMatchedList)
                for matchstring in partialMatchedSet:
                    if (matchstring in processDict.keys()):
                        resourceId = processDict[matchstring]
                    elif (matchstring in qualityDict.keys()):
                        resourceId = qualityDict[matchstring]
                    else:
                        resourceId = resourceTermsDict[matchstring]
                    partialMatchedResourceList.append(resourceId)
                if (len(partialMatchedSet) > 0):
                    fw.write("	" + str(partialMatchedSet) + "	" + str(
                        partialMatchedResourceList) + "	GComponent Match from Start ")
                    trigger = True

  if (tkn in processDict.keys()):
                proc = processDict[tkn]
                partialMatchedList.append(tkn)
            if (tkn in qualityDict.keys()):
                quality = qualityDict[tkn]
                partialMatchedList.append(tkn)

    if "ground:" in termList and "FOODON" not in termList:
        termList = termList.replace("ground:[GROUNDING PROCESS]", "")
        termList = termList.replace(",ground:[GROUNDING PROCESS]", "")
        termList = termList.replace(", ground:[GROUNDING PROCESS]", "")
        termList = termList.replace("ground:[GROUNDING PROCESS],", "")
        termList = termList.replace(", ' '", "")
        termList = termList.replace("'',", "")
        termList = termList.replace(", ''", "")
        termList = termList.replace("' ',", "")
        print("hhhhhhheeeeeeeeeee   "+termList)




    # Rule4: Annotate all the Full Term Matches of Terms with plural treatment
    elif (sample.lower() in resourceTermsDict.keys()):
        resourceId = resourceTermsDict[sample.lower()]
        # print(sample + "	" + resourceId + "	Full Term Match")
        fw.write("	" + sample.lower() + "	" + resourceId + "	Full Term Match but with treatment of singular plural")'''


