# =====Imports from different packages used====LATEST PIPERLINE&&&&&
import csv  # For reading and dealing with comma separated files
import nltk  # For reading and dealing with comma separated files
import re
import inflection
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import pos_tag, ne_chunk
# from nltk.stem.snowball import SnowballStemmer
# from spacy.en import English
import wikipedia
import itertools
from itertools import combinations
from dateutil.parser import parse

'''
words = set(nltk.corpus.words.words())
def deConcatenateString(term):
    output={}
    lastIndex = len(term)
    for i in range(1, lastIndex + 1):
        firstTerm = (term[:i])
        secondTerm = (term[i:])

        if ((firstTerm.lower() in words or not firstTerm.isalpha()) and (
                secondTerm.lower() in words or not secondTerm.isalpha())):
            output.append(firstTerm)
            output.append(secondTerm)
    return output
'''

# Initializations etc.- Not used currently
# parser = English()
# stemmer = SnowballStemmer('english')



# Declaration of the output files
fw = open('Output-AnnotationSamples-Result-VerB.tsv', 'w')  # Main output file
fw1 = open('Output-Entero-Result-Missing-verB.tsv', 'w')  # Supplementary output files

# Output file Column Headings
fw.write(
    "Sample_Id" + "\t" + "Sample_Desc" + "\t" + "Cleaned_Sample" + "\t" + "Phrase_POS_Tagged" + "\t" + "Probable_Candidate_Terms" + "\t" + "Matched_Term" + "\t" + "All_matched_Terms_with_Resource_IDs" + "\t" + "Retained_Terms_with_Resource_IDs" + "\t" + "Number of Components(In case of Component Match)" + "\t" + "Match_Status(Macro Level)" + "\t" + "Match_Status(Micro Level)" + "\t" + "Remaining_Tokens" + "\t" + "Different Components(In case of Component Match)")

##Get all the samples from database

remainingTokenSet = []

# METHODS USED



'''
#Method to get entities using Spacy  - Discarded after poor results with short texts
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


# Method to determine  whether a string is a number (Used for Cardinal-Ordinal Tagging)
def is_number(inputstring):
    try:
        float(inputstring)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(inputstring)
        return True
    except (TypeError, ValueError):
        pass
    return False


# Method to determine  whether a string is a date or day (Used for DateOrDay Tagging)
def is_date(inputstring):
    try:
        parse(inputstring)
        return True
    except ValueError:
        return False


# Method to get ngrams with a given value of n (i.e. n=1 means unigram, n=2 means bigram, n=3 means trigram and so on)
def ngrams(input, n):
    input = input.split(' ')
    output = []
    for i in range(len(input) - n + 1):
        output.append(input[i:i + n])
    return output


# Method to preprocess the string token on some pre-determined parts
def preProcess(stringToken):
    if ('\'s' in stringToken):
        stringToken1 = stringToken.replace("\'s", "")  # for cow's to cow
        stringToken = stringToken1
    if (',' in stringToken):  # comma concatenated in token is get rid of
        stringToken1 = stringToken.rstrip(', ')
        stringToken = stringToken1
    if ('.' in stringToken):  # dot concatenated in token is get rid of
        stringToken1 = stringToken.rstrip('. ')
        stringToken = stringToken1
    return stringToken

def find_between_r( s, first, last ):
    try:
        start = s.rindex( first ) + len( first )
        end = s.rindex( last, start )
        return s[start:end]
    except ValueError:
        return ""

def find_left_r(s, first, last):
    try:
        start = s.rindex(first) + len(first)
        end = s.rindex(last, start)
        return s[0:start - 2]
    except ValueError:
        return ""

# Methods to add suffixes such as food product or product to input phrase to improve Term matching
def addSuffixFoodProduct(inputstring):
    output = inputstring + " " + str("food product")
    return output


def addSuffixProduct(inputstring):
    output = inputstring + " " + str("product")
    return output


def addSuffixFoodSource(inputstring):
    output = inputstring + " " + str("as food source")
    return output


def addSuffixPlantFoodSource(inputstring):
    output = inputstring + " " + str("plant as food source")
    return output


def addSuffixPlantBracketedFoodSource(inputstring):
    output = inputstring + " " + str("(plant) as food source")
    return output


# Methods to get all permutations of input string -has overhead so the size of the phrase has been limited to 4-grams
def allPermutations(inputstring):
    listOfPermutations = inputstring.split()
    setPerm = set(itertools.permutations(listOfPermutations))
    return setPerm


def combi(input, n):
    output=combinations(input, n)
    return output


# Method to get the punctuation treatment - removes some predetermined punctuation and replaces it with a space
def punctuationTreatment(inputstring, punctuationList):
    finalSample = ""
    sampleTokens = word_tokenize(inputstring)
    for token in sampleTokens:
        withoutPunctuation = ""
        number_result = is_number(token)
        date_result = is_date(token)
        if (number_result is True or date_result is True):
            withoutPunctuation = token
        else:
            for char in token:
                if char in punctuationList:
                    withoutPunctuation = withoutPunctuation + " "
                else:
                    withoutPunctuation = withoutPunctuation + char
        if (finalSample):
            finalSample = finalSample + " " + withoutPunctuation
        else:
            finalSample = withoutPunctuation
    return finalSample


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

# Get all Non English Language words mappings from resource in CSV file format
nonEnglishWordsDict = {}
nonEnglishWordsLowerDict = {}
with open('nonEnglishTerms.csv') as csvfile:
    ctr2 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr2 > 0:
            nonEngTerm = row[0]
            nonEngExpansion = row[1]
            nonEnglishWordsDict[nonEngTerm.strip()] = nonEngExpansion.strip()
            nonEnglishWordsLowerDict[nonEngTerm.strip().lower()] = nonEngExpansion.strip()
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
with open('qualities.csv') as csvfile:  # qualities-minimum.csv
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

# Method to get all inflection exception words from resource in CSV file format -Needed to supercede the general inflection treatment
inflectionExceptionList = []
with open('inflection-exceptions.csv') as csvfile:
    ctr2 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr2 > 0:
            abbTerm = row[0]
            inflectionExceptionList.append(abbTerm.strip().lower())
        ctr2 += 1

# Method to Get all stop words from resource in CSV file format -A very constrained lists of stop words is
# used as other stop words are assumed to have some useful semantic meaning
stopWordsList = []
with open('mining-stopwords.csv') as csvfile:
    ctr2 = 0
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if ctr2 > 0:
            abbTerm = row[0]
            stopWordsList.append(abbTerm.strip().lower())
        ctr2 += 1

# Method to read the input data of short textual samples from sample master file in CSV format
samplesDict = {}
samplesList = []
samplesSet = []

#with open('enteroForFreq.csv') as csvfile:
#with open('genomeTrackerMaster.csv') as csvfile:
#with open('GRDI-UniqueSamples.csv') as csvfile:
#with open('bccdcsample.csv') as csvfile:
#with open('nutriFood.csv') as csvfile:
with open('AnnotationSamples.csv') as csvfile:

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



# Get all terms from resources- right now in a CSV file extracted from ontologies using another external script
resourceTermsDict = {}
resourceRevisedTermsDict = {}
resourceTermsIDBasedDict = {}
with open('ResourceTerms-Combined.csv') as csvfile:  # 'ResourceTerms-copy1.csv'   #ResourceTerms-withoutnew.csv
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


    # Method to get the final retained set of matched terms
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
            a = a.replace("=", ",")
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

            if " " not in wrd:
                for othrwrd in wordList:
                    #product egg raw yolk   {'egg yolk (raw):FOODON_03301439', 'egg (raw):FOODON_03301075', 'egg product:zFOODON_BaseTerm_368'}
                    if wrd in retainedSet and wrd in othrwrd and wrd != othrwrd:
                        retainedSet.remove(wrd)
            else:# compound word
                ctr = 0
                for othrwrd in wordList:
                    # product egg raw yolk   {'egg yolk (raw):FOODON_03301439', 'egg (raw):FOODON_03301075', 'egg product:zFOODON_BaseTerm_368'}
                    input = wrd.split(' ')
                    for i in range(len(input)):
                        if othrwrd.find(input[i]) == -1:
                            ctr += 1
                    if wrd in retainedSet and ctr == 0 and wrd != othrwrd:
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


# ===For getting all the permutations of Resource Terms
resourcePermutationTermsDict = {}
# Iterate
for k, v in resourceRevisedTermsDict.items():
    resourceid = v
    resource = k
    if "(" not in resource:
        # fw1.write("\n" + resourceid)
        sampleTokens = word_tokenize(resource.lower())
        # for tkn in sampleTokens:
        if len(sampleTokens) < 5:
            setPerm = allPermutations(resource)
            print("sssssssssssssss=== " + str(setPerm))
            for perm in setPerm:
                permString = ' '.join(perm)
                resourcePermutationTermsDict[permString.strip()] = resourceid.strip()

# ===For getting all the permutations of Bracketed Resource Terms
resourceBracketedPermutationTermsDict={}
# Iterate
for k, v in resourceRevisedTermsDict.items():
    resourceid = v
    resource1 = k
    sampleTokens = word_tokenize(resource1.lower())
    if len(sampleTokens) < 7:
        if "(" in resource1:
            part1 = find_left_r(resource1, "(", ")")
            part2 = find_between_r(resource1, "(", ")")
            candidate = ""

            if "," not in part2:
                candidate = part2 + " " + part1
                setPerm = allPermutations(candidate)
                for perm in setPerm:
                    permString = ' '.join(perm)
                    resourceBracketedPermutationTermsDict[permString.strip()] = resourceid.strip()
            elif "," in part2:
                lst = part2.split(",")
                bracketedPart = ""
                for x in lst:
                    if not bracketedPart:
                        bracketedPart = x.strip()
                    else:
                        bracketedPart = bracketedPart + " " + x.strip()
                candidate = bracketedPart + " " + part1
                setPerm = allPermutations(candidate)
                for perm in setPerm:
                    permString = ' '.join(perm)
                    resourceBracketedPermutationTermsDict[permString.strip()] = resourceid.strip()



                # ++++++++++++++++++++++++++++++++ MAIN TEXT MINING PIPELINE ++++++++++++++++++++++++++++++++++++++++++++++



# This is the punctuationsList which is used for basic treatment
punctuationsList = ['-', '_', '(', ')', ';', '/', ':', '%']  # Current punctuationsList for basic treatment

# ===Here the main Iteration starts over input data short textual samples for matching to resource (ontology) terms

# Iterate over samples for matching to ontology terms
coveredAllTokensSet = []
remainingAllTokensSet = []
for k, v in samplesDict.items():
    sampleid = k
    sample = v
    trigger = False
    status = ""  # variable reflecting status of Matching to be displayed for evry rule/section
    statusAddendum = ""
    statusAddendumSet = []
    statusAddendumSetFinal = []
    statusAddendumSetFinal.clear()

    # tg = entities(sample.lower()) #From Spacy General Tagger  - No need as the NER for Shorter textual information fares poorly
    fw.write("\n" + sampleid + "	" + sample)  # + "	" +str(tg))

    sample = punctuationTreatment(sample, punctuationsList)
    sample = re.sub(' +', ' ', sample)  # Extra innner spaces are removed
    sampleTokens = word_tokenize(sample.lower())
    newPhrase = ""  # Phrase that will be used for cleaned sample
    lemma = ""

    # ===Few preliminary things- Inflection,spelling mistakes, Abbreviations, acronyms, foreign words, Synonyms taken care of
    for tkn in sampleTokens:

        # Some preprocessing (controlled) Steps
        tkn = preProcess(tkn)

        # Plurals are converted to singulars with exceptions
        if (tkn.endswith("us")):  # for inflection exception-takes into account both lower and upper case
            lemma = tkn
        elif (tkn not in inflectionExceptionList):  # Further Inflection Exception list is taken into account
            lemma = inflection.singularize(tkn)
            if (tkn != lemma):
                statusAddendum = "Inflection Treatment"
                statusAddendumSet.append("Inflection Treatment")
        else:
            lemma = tkn

        # Misspellings are dealt with  here
        if (lemma in spellingDict.keys()):  # spelling mistakes taken care of
            lemma = spellingDict[lemma]
            statusAddendum = statusAddendum + "Spelling Correction Treatment"
            statusAddendumSet.append("Spelling Correction Treatment")
        elif (lemma.lower() in spellingLowerDict.keys()):
            lemma = spellingLowerDict[lemma.lower()]
            statusAddendum = statusAddendum + "Spelling Correction Treatment"
            statusAddendumSet.append("Spelling Correction Treatment")
        if (
            lemma in abbreviationDict.keys()):  # Abbreviations, acronyms, foreign language words taken care of- need rule for abbreviation e.g. if lemma is Abbreviation
            lemma = abbreviationDict[lemma]
            statusAddendum = "Abbreviation-Acronym Treatment"
            statusAddendumSet.append("Abbreviation-Acronym Treatment")
        elif (lemma.lower() in abbreviationLowerDict.keys()):
            lemma = abbreviationLowerDict[lemma.lower()]
            statusAddendum = "Abbreviation-Acronym Treatment"
            statusAddendumSet.append("Abbreviation-Acronym Treatment")

        if (lemma in nonEnglishWordsDict.keys()):  # Non English language words taken care of
            lemma = nonEnglishWordsDict[lemma]
            statusAddendum = statusAddendum + "Non English Language Words Treatment"
            statusAddendumSet.append("Non English Language Words Treatment")
        elif (lemma.lower() in nonEnglishWordsLowerDict.keys()):
            lemma = nonEnglishWordsLowerDict[lemma.lower()]
            statusAddendum = statusAddendum + "Non English Language Words Treatment"
            statusAddendumSet.append("Non English Language Words Treatment")

            # if (lemma in synonymsDict.keys()):      ## Synonyms taken care of- need more synonyms
            #   lemma = synonymsDict[lemma]
        # deConcatenateString(lemma)


        # ===This will create a cleaned sample after above treatments [Here we are making new phrase now in lower case]
        if (
            not newPhrase and lemma.lower() not in stopWordsList):  # if newphrase is empty and lemma is in not in stopwordlist (abridged according to domain)
            newPhrase = lemma.lower()
        elif (
            lemma.lower() not in stopWordsList):  # if newphrase is not empty and lemma is in not in stopwordlist (abridged according to domain)
            newPhrase = newPhrase + " " + lemma.lower()
        newPhrase = re.sub(' +', ' ', newPhrase)  # Extra innner spaces removed from cleaned sample

        if (
            newPhrase in abbreviationDict.keys()):  # NEED HERE AGAIN ? Abbreviations, acronyms, non English words taken care of- need rule for abbreviation
            newPhrase = abbreviationDict[newPhrase]
            statusAddendum = statusAddendum + "Abbreviation-Acronym Treatment"
            statusAddendumSet.append("Abbreviation-Acronym Treatment")
        elif (newPhrase in abbreviationLowerDict.keys()):
            newPhrase = abbreviationLowerDict[newPhrase]
            statusAddendum = statusAddendum + "Abbreviation-Acronym Treatment"
            statusAddendumSet.append("Abbreviation-Acronym Treatment")

        if (
            newPhrase in nonEnglishWordsDict.keys()):  # NEED HERE AGAIN ? Abbreviations, acronyms, non English words taken care of- need rule for abbreviation
            newPhrase = nonEnglishWordsDict[newPhrase]
            # statusAddendum = statusAddendum + "Non English Language Words Treatment"
            statusAddendum = statusAddendum + "Non English Language Words Treatment"
            statusAddendumSet.append("Non English Language Words Treatment")
        elif (newPhrase in nonEnglishWordsLowerDict.keys()):
            newPhrase = nonEnglishWordsLowerDict[newPhrase]
            statusAddendum = statusAddendum + "Non English Language Words Treatment"
            statusAddendumSet.append("Non English Language Words Treatment")
            # statusAddendum = statusAddendum + "Non English Language Words Treatment"
            # if (newPhrase in synonymsDict.keys()):  ## NEED HERE ? Synonyms taken care of- need more synonyms
            # newPhrase = synonymsDict[newPhrase]

    # Here we are making the tokens of cleaned sample phrase
    newSampleTokens = word_tokenize(newPhrase.lower())
    tokens_pos = pos_tag(newSampleTokens)
    fw.write("	" + newPhrase + "\t" + str(tokens_pos))

    # This part works for getting the Candidate phrase based on POS tagging and applied rule [To check whether a major contributor]
    qualityList = []
    phraseStr = ""
    prevPhraseStr = ""
    prevTag = "X"
    for tkp in tokens_pos:
        # print(tkp)
        currentTag = tkp[1]
        # qualityListForSet.append(tkp[1])
        if ((tkp[1] == 'NN' or tkp[1] == 'NNS') and (prevTag == "X" or prevTag == "NN" or prevTag == "NNS")):
            phraseStr = tkp[0]
            if not prevPhraseStr:
                prevPhraseStr = phraseStr
            else:
                prevPhraseStr = prevPhraseStr + " " + phraseStr
            prevTag = currentTag
    fw.write("	" + str(prevPhraseStr))

    # Rule1: Annotate all the empty samples
    if not sample:
        status = "Empty Sample"
        fw.write("	--" + "	--" + "\t" + "\t" + "\t" + status)
        trigger = True

    # Rule2: Annotate all the Full Term Matches of Terms without any treatment
    if (sample in resourceTermsDict.keys() and not trigger):
        resourceId = resourceTermsDict[sample]  # Gets the id of the resource for matched term
        status = "Full Term Match"
        statusAddendum = "[A DirectMatch]"
        statusAddendumSet.append("A Direct Match")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write("	" + sample + "	" + "[" + (sample + ":" + resourceId) + "]" + "\t" + "[" + (
        sample + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sample.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True
    # Comment- Above section is OK -validated


    # Rule3: Annotate all the Full Term Matches of Terms with change of case  resourceRevisedTermsDict

    # Here we check all the suffices that can be applied to input term to make it comparable with resource terms
    sampleRevised1 = addSuffixFoodProduct(sample)
    sampleRevised2 = addSuffixProduct(sample)
    sampleRevised3 = addSuffixFoodSource(sample)
    sampleRevised4 = addSuffixPlantFoodSource(sample)
    sampleRevised5 = addSuffixPlantBracketedFoodSource(sample)


    if (sample.lower() in resourceTermsDict.keys() and not trigger):
        resourceId = resourceTermsDict[sample.lower()]
        status = "Full Term Match"
        statusAddendum = "[Change of Case in Input Data]"
        statusAddendumSet.append("Change of Case in Input Data")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write("	" + sample.lower() + "	" + "[" + (sample.lower() + ":" + resourceId) + "]" + "\t" + "[" + (
        sample.lower() + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sample.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True  # resourcePermutationTermsDict

    elif (sample.lower() in resourceRevisedTermsDict.keys() and not trigger):
        resourceId = resourceRevisedTermsDict[sample.lower()]
        status = "Full Term Match"
        statusAddendum = "[Change of Case in Input or Resource Data]"
        statusAddendumSet.append("Change of Case in Resource Data")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write("	" + sample.lower() + "	" + "[" + (sample.lower() + ":" + resourceId) + "]" + "\t" + "[" + (
        sample.lower() + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sample.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True

    elif (sample.lower() in resourcePermutationTermsDict.keys() and not trigger):
        resourceId = resourcePermutationTermsDict[sample.lower()]
        # here need to do the actualResourceTerm=resourceTermsDict.get(resourceId)
        resourceOriginalTerm = resourceTermsIDBasedDict[resourceId]
        status = "Full Term Match"
        statusAddendum = "[Permutation of Tokens in Resource Term]"
        statusAddendumSet.append("Permutation of Tokens in Resource Term")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write(
            "	" + sample.lower() + "	" + "[" + (resourceOriginalTerm + ":" + resourceId) + "]" + "\t" + "[" + (
            resourceOriginalTerm + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sample.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True


    elif (sample.lower() in resourceBracketedPermutationTermsDict.keys() and not trigger):
        resourceId = resourceBracketedPermutationTermsDict[sample.lower()]
        # here need to do the actualResourceTerm=resourceTermsDict.get(resourceId)
        resourceOriginalTerm = resourceTermsIDBasedDict[resourceId]
        status = "Full Term Match"
        statusAddendum = "[Permutation of Tokens in Bracketed Resource Term]"
        statusAddendumSet.append("Permutation of Tokens in Bracketed Resource Term")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write(
            "	" + sample.lower() + "	" + "[" + (resourceOriginalTerm + ":" + resourceId) + "]" + "\t" + "[" + (
            resourceOriginalTerm + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sample.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True


    elif (sampleRevised1 in resourceRevisedTermsDict.keys() and not trigger):
        resourceId = resourceRevisedTermsDict[sampleRevised1]
        status = "Full Term Match"
        statusAddendum = "[Change of Case of Resource and Suffix Treatment (Food Product) to Input]"
        statusAddendumSet.append("Change of Case of Resource and Suffix Treatment (Food Product) to Input")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised1 + ":" + resourceId) + "]" + "\t" + "[" + (
        sampleRevised1 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sampleRevised1.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True

    elif (sampleRevised2 in resourceRevisedTermsDict.keys() and not trigger):
        resourceId = resourceRevisedTermsDict[sampleRevised2]
        status = "Full Term Match"
        statusAddendum = "[Change of Case of Resource and Suffix Treatment (Product) to Input]"
        statusAddendumSet.append("Change of Case of Resource and Suffix Treatment (Product) to Input")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised2 + ":" + resourceId) + "]" + "\t" + "[" + (
        sampleRevised2 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sampleRevised2.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True

    elif (sampleRevised3 in resourceRevisedTermsDict.keys() and not trigger):
        resourceId = resourceRevisedTermsDict[sampleRevised3]
        status = "Full Term Match"
        statusAddendum = "[Change of Case of Resource and Suffix Treatment (as food source) to Input]"
        statusAddendumSet.append("Change of Case of Resource and Suffix Treatment (as food source) to Input")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised3 + ":" + resourceId) + "]" + "\t" + "[" + (
            sampleRevised3 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sampleRevised3.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True

    elif (sampleRevised4 in resourceRevisedTermsDict.keys() and not trigger):
        resourceId = resourceRevisedTermsDict[sampleRevised4]
        status = "Full Term Match"
        statusAddendum = "[Change of Case of Resource and Suffix Treatment (plant as food source) to Input]"
        statusAddendumSet.append("Change of Case of Resource and Suffix Treatment (plant as food source) to Input")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised4 + ":" + resourceId) + "]" + "\t" + "[" + (
            sampleRevised4 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sampleRevised4.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True

    elif (sampleRevised5 in resourceRevisedTermsDict.keys() and not trigger):
        resourceId = resourceRevisedTermsDict[sampleRevised5]
        status = "Full Term Match"
        statusAddendum = "[Change of Case of Resource and Suffix Treatment ((plant)as food source) to Input]"
        statusAddendumSet.append("Change of Case of Resource and Suffix Treatment ((plant)as food source) to Input")
        statusAddendumSetFinal = set(statusAddendumSet)
        fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised3 + ":" + resourceId) + "]" + "\t" + "[" + (
            sampleRevised5 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
        # To Count the Covered Tokens(words)
        thisSampleTokens = word_tokenize(sampleRevised5.lower())
        for thisSampleIndvToken in thisSampleTokens:
            coveredAllTokensSet.append(thisSampleIndvToken)
        trigger = True




    # Rule4: This will open now the cleaned sample to the test of Full Term Matching
    if (not trigger):
        print("We will go further with other rules")
        sampleTokens = word_tokenize(sample.lower())
        print("==============" + sample.lower())
        print("--------------" + newPhrase.lower())

        # Here we check all the suffices that can be applied to input term to make it comparable with resource terms
        sampleRevised1 = addSuffixFoodProduct(newPhrase.lower())
        sampleRevised2 = addSuffixProduct(newPhrase.lower())
        sampleRevised3 = addSuffixFoodSource(newPhrase.lower())
        sampleRevised4 = addSuffixPlantFoodSource(newPhrase.lower())
        sampleRevised5 = addSuffixPlantBracketedFoodSource(newPhrase.lower())


        if (newPhrase.lower() in resourceTermsDict.keys()):
            resourceId = resourceTermsDict[newPhrase.lower()]
            status = "Full Term Match"  # -Inflection, Synonym, Spelling Correction, Foreign Language Treatment "
            statusAddendum = statusAddendum + "[A Direct Match with Cleaned Sample]"
            statusAddendumSet.append("A Direct Match with Cleaned Sample")
            statusAddendumSetFinal = set(statusAddendumSet)
            fw.write("	" + newPhrase.lower() + "	" + "[" + (
            newPhrase.lower() + ":" + resourceId) + "]" + "\t" + "[" + (
                     newPhrase.lower() + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(
                statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(newPhrase.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True

        elif (
            newPhrase.lower() in resourceRevisedTermsDict.keys()):  # NEED SOME RULE- resourceRevisedTermsDict.keys()  is with change case treatment
            resourceId = resourceRevisedTermsDict[newPhrase.lower()]
            status = "Full Term Match"
            statusAddendum = statusAddendum + "[Change of Case of Resource Terms]"
            statusAddendumSet.append("Change of Case of Resource Terms")
            statusAddendumSetFinal = set(statusAddendumSet)
            fw.write("	" + newPhrase.lower() + "	" + "[" + (
            newPhrase.lower() + ":" + resourceId) + "]" + "\t" + "[" + (
                     newPhrase.lower() + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(
                statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(newPhrase.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True
        elif (newPhrase.lower() in resourcePermutationTermsDict.keys() and not trigger):
            resourceId = resourcePermutationTermsDict[newPhrase.lower()]
            status = "Full Term Match"
            statusAddendum = statusAddendum + "[Permutation of Tokens in Resource Term]"
            statusAddendumSet.append("Permutation of Tokens in Resource Term")
            statusAddendumSetFinal = set(statusAddendumSet)
            resourceOriginalTerm = resourceTermsIDBasedDict[resourceId]
            fw.write("	" + newPhrase.lower() + "	" + "[" + (
            resourceOriginalTerm + ":" + resourceId) + "]" + "\t" + "[" + (
                     resourceOriginalTerm + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(
                statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(newPhrase.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True

        elif (newPhrase.lower() in resourceBracketedPermutationTermsDict.keys() and not trigger):
            resourceId = resourceBracketedPermutationTermsDict[newPhrase.lower()]
            status = "Full Term Match"
            statusAddendum = statusAddendum + "[Permutation of Tokens in Bracketed Resource Term]"
            statusAddendumSet.append("Permutation of Tokens in Bracketed Resource Term")
            statusAddendumSetFinal = set(statusAddendumSet)
            resourceOriginalTerm = resourceTermsIDBasedDict[resourceId]
            fw.write("	" + newPhrase.lower() + "	" + "[" + (
            resourceOriginalTerm + ":" + resourceId) + "]" + "\t" + "[" + (
                     resourceOriginalTerm + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(
                statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(newPhrase.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True

        elif (sampleRevised1 in resourceRevisedTermsDict.keys() and not trigger):
            resourceId = resourceRevisedTermsDict[sampleRevised1]
            status = "Full Term Match"
            statusAddendum = "[CleanedSample-Change of Case of Resource and Suffix Treatment (Food Product) to Input]"
            statusAddendumSet.append("CleanedSample-Change of Case of Resource and Suffix Treatment (Food Product) to Input")
            statusAddendumSetFinal = set(statusAddendumSet)
            fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised1 + ":" + resourceId) + "]" + "\t" + "[" + (
                sampleRevised1 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(sampleRevised1.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True

        elif (sampleRevised2 in resourceRevisedTermsDict.keys() and not trigger):
            resourceId = resourceRevisedTermsDict[sampleRevised2]
            status = "Full Term Match"
            statusAddendum = "[CleanedSample-Change of Case of Resource and Suffix Treatment (Product) to Input]"
            statusAddendumSet.append("CleanedSample-Change of Case of Resource and Suffix Treatment (Product) to Input")
            statusAddendumSetFinal = set(statusAddendumSet)
            fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised2 + ":" + resourceId) + "]" + "\t" + "[" + (
                sampleRevised2 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(sampleRevised2.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True

        elif (sampleRevised3 in resourceRevisedTermsDict.keys() and not trigger):
            resourceId = resourceRevisedTermsDict[sampleRevised3]
            status = "Full Term Match"
            statusAddendum = "[CleanedSample-Change of Case of Resource and Suffix Treatment (as food source) to Input]"
            statusAddendumSet.append("CleanedSample-Change of Case of Resource and Suffix Treatment (as food source) to Input")
            statusAddendumSetFinal = set(statusAddendumSet)
            fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised3 + ":" + resourceId) + "]" + "\t" + "[" + (
                sampleRevised3 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(sampleRevised3.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True

        elif (sampleRevised4 in resourceRevisedTermsDict.keys() and not trigger):
            resourceId = resourceRevisedTermsDict[sampleRevised4]
            status = "Full Term Match"
            statusAddendum = "[CleanedSample-Change of Case of Resource and Suffix Treatment (plant as food source) to Input]"
            statusAddendumSet.append("CleanedSample-Change of Case of Resource and Suffix Treatment (plant as food source) to Input")
            statusAddendumSetFinal = set(statusAddendumSet)
            fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised4 + ":" + resourceId) + "]" + "\t" + "[" + (
                sampleRevised4 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(sampleRevised4.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True

        elif (sampleRevised5 in resourceRevisedTermsDict.keys() and not trigger):
            resourceId = resourceRevisedTermsDict[sampleRevised5]
            status = "Full Term Match"
            statusAddendum = "[CleanedSample-Change of Case of Resource and Suffix Treatment ((plant)as food source) to Input]"
            statusAddendumSet.append("CleanedSample-Change of Case of Resource and Suffix Treatment ((plant)as food source) to Input")
            statusAddendumSetFinal = set(statusAddendumSet)
            fw.write("	" + sample.lower() + "	" + "[" + (sampleRevised3 + ":" + resourceId) + "]" + "\t" + "[" + (
                sampleRevised5 + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(sampleRevised5.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True








    # Rule5: Full Term Match if possible from multi-word collocations -e.g. from Wikipedia
    if (not trigger):
        print("We will go further with other rules")
        sampleTokens = word_tokenize(sample.lower())

        print("==============" + sample.lower())
        print("--------------" + newPhrase.lower())
        if (newPhrase.lower() in collocationDict.keys()):
            resourceId = collocationDict[newPhrase.lower()]
            status = "Full Term Match"
            statusAddendum = statusAddendum + "[Matching with Wikipedia Based Collocation Resource]"
            statusAddendumSet.append("Matching with Wikipedia Based Collocation Resource")
            statusAddendumSetFinal = set(statusAddendumSet)
            fw.write("	" + newPhrase.lower() + "	" + "[" + (
            newPhrase.lower() + ":" + resourceId) + "]" + "\t" + "[" + (
                     newPhrase.lower() + ":" + resourceId) + "]" + "\t" + "\t" + status + "\t" + str(
                statusAddendumSetFinal))
            # To Count the Covered Tokens(words)
            thisSampleTokens = word_tokenize(newPhrase.lower())
            for thisSampleIndvToken in thisSampleTokens:
                coveredAllTokensSet.append(thisSampleIndvToken)
            trigger = True

    if (not trigger):
        print("We will go further with other rules")

        # Some DEclarations for component match cases
        partialMatchedList = []
        partialMatchedResourceList = []
        partialMatchedSet = []

        newChunk = newPhrase.lower()
        newChunkTokens = word_tokenize(newChunk.lower())
        # This is the case of making 5-gram chunks and subsequent processing for cleaned samples
        #  newChunk = reduceChunk(newChunk, tkn + " ")
        #newChunk5Grams = ngrams(newChunk, 5)
        newChunk5Grams = combi(newChunkTokens, 5)
        for nc in newChunk5Grams:
            grm1 = ' '.join(nc)
            setPerm = allPermutations(grm1)  # Gets the set of all possible permutations for this gram type chunks
            for perm in setPerm:
                grm = ' '.join(perm)
                if (grm in abbreviationDict.keys()):  # rule for abbreviation
                    grm = abbreviationDict[grm]
                    statusAddendum = statusAddendum + "[Abbreviation-Acronym Treatment]"
                    statusAddendumSet.append("Abbreviation-Acronym Treatment")
                if (grm in nonEnglishWordsDict.keys()):  # rule for abbreviation
                    grm = nonEnglishWordsDict[grm]
                    statusAddendum = statusAddendum + "[Non English Language Words Treatment]"
                    statusAddendumSet.append("Non English Language Words Treatment")
                if (grm in synonymsDict.keys()):  ## Synonyms taken care of- need more synonyms
                    grm = synonymsDict[grm]
                    statusAddendum = statusAddendum + "[Synonym Usage]"
                    statusAddendumSet.append("Synonym Usage")
                grmRevised1 = addSuffixFoodProduct(grm)
                grmRevised2 = addSuffixProduct(grm)
                grmRevised3 = addSuffixFoodSource(grm)
                grmRevised4 = addSuffixPlantFoodSource(grm)
                grmRevised5 = addSuffixPlantBracketedFoodSource(grm)

                # Matching Test for 5-gram chunk
                if (grm in resourceTermsDict.keys()):
                    partialMatchedList.append(grm)
                    # statusAddendum="Match with 5-Gram Chunk"+statusAddendum
                elif (grm in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grm)
                    # statusAddendum = "Match with 5-Gram Chunk"+statusAddendum
                elif (grm in resourceBracketedPermutationTermsDict.keys() ):
                    resourceId = resourceBracketedPermutationTermsDict[grm]
                    partialMatchedList.append(grm)
                    statusAddendum = "[Permutation of Tokens in Bracketed Resource Term]"
                    statusAddendumSet.append("Permutation of Tokens in Bracketed Resource Term")
                elif (grmRevised1 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised1)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (Food Product) Treatment to Input")
                elif (grmRevised2 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised2)
                    statusAddendum = statusAddendum + "[Another Suffix Treatment]"
                    statusAddendumSet.append("Suffix (Product) Treatment to Input")
                elif (grmRevised3 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised3)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (as food source) Treatment to Input")
                elif (grmRevised4 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised4)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (plant as food source) Treatment to Input")
                elif (grmRevised5 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised5)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix ((plant) as food source) Treatment to Input")

        # This is the case of making 4-gram chunks and subsequent processing for cleaned samples
        #newChunk4Grams = ngrams(newChunk, 4)
        newChunk4Grams = combi(newChunkTokens, 4)
        for nc in newChunk4Grams:
            grm1 = ' '.join(nc)
            setPerm = allPermutations(grm1)
            for perm in setPerm:
                grm = ' '.join(perm)
                if (grm in abbreviationDict.keys()):  # rule for abbreviation
                    grm = abbreviationDict[grm]
                    statusAddendum = statusAddendum + "[Abbreviation-Acronym Treatment]"
                    statusAddendumSet.append("Abbreviation-Acronym Treatment")
                if (grm in nonEnglishWordsDict.keys()):  # rule for abbreviation
                    grm = nonEnglishWordsDict[grm]
                    statusAddendum = statusAddendum + "[Non English Language Words Treatment]"
                    statusAddendumSet.append("Non English Language Words Treatment")
                if (grm in synonymsDict.keys()):  ## Synonyms taken care of- need more synonyms
                    grm = synonymsDict[grm]
                    statusAddendum = statusAddendum + "[Synonym Usage]"
                    statusAddendumSet.append("Synonym Usage")

                grmRevised1 = addSuffixFoodProduct(grm)
                grmRevised2 = addSuffixProduct(grm)
                grmRevised3 = addSuffixFoodSource(grm)
                grmRevised4 = addSuffixPlantFoodSource(grm)
                grmRevised5 = addSuffixPlantBracketedFoodSource(grm)
                # Matching Test for 4-gram chunk
                if (grm in resourceTermsDict.keys()):
                    partialMatchedList.append(grm)
                    # statusAddendum = "Match with 4-Gram Chunk"+statusAddendum
                elif (grm in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grm)
                    # statusAddendum = "Match with 4-Gram Chunk"+statusAddendum
                elif (grm in resourceBracketedPermutationTermsDict.keys()):
                    resourceId = resourceBracketedPermutationTermsDict[grm]
                    partialMatchedList.append(grm)
                    statusAddendum = "[Permutation of Tokens in Bracketed Resource Term]"
                    statusAddendumSet.append("Permutation of Tokens in Bracketed Resource Term")
                elif (grmRevised1 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised1)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (Food Product) Treatment to Input")
                elif (grmRevised2 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised2)
                    statusAddendum = statusAddendum + "[Another Suffix Treatment]"
                    statusAddendumSet.append("Suffix (Product) Treatment to Input")
                elif (grmRevised3 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised3)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (as food source) Treatment to Input")
                elif (grmRevised4 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised4)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (plant as food source) Treatment to Input")
                elif (grmRevised5 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised5)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix ((plant) as food source) Treatment to Input")

        # This is the case of making 3-gram (trigram) chunks and subsequent processing for cleaned samples
        #newChunk3Grams = ngrams(newChunk, 3)
        newChunk3Grams = combi(newChunkTokens, 3)
        for nc in newChunk3Grams:
            grm1 = ' '.join(nc)
            setPerm = allPermutations(grm1)
            for perm in setPerm:
                grm = ' '.join(perm)
                if (grm in abbreviationDict.keys()):  # rule for abbreviation
                    grm = abbreviationDict[grm]
                    statusAddendum = statusAddendum + "[Abbreviation-Acronym Treatment]"
                    statusAddendumSet.append("Abbreviation-Acronym Treatment")
                if (grm in nonEnglishWordsDict.keys()):  # rule for abbreviation
                    grm = nonEnglishWordsDict[grm]
                    statusAddendum = statusAddendum + "[Non English Language Words Treatment]"
                    statusAddendumSet.append("Non English Language Words Treatment")
                if (grm in synonymsDict.keys()):  ## Synonyms taken care of- need more synonyms
                    grm = synonymsDict[grm]
                    statusAddendum = statusAddendum + "[Synonym Usage]"
                    statusAddendumSet.append("Synonym Usage")

                grmRevised1 = addSuffixFoodProduct(grm)
                grmRevised2 = addSuffixProduct(grm)
                grmRevised3 = addSuffixFoodSource(grm)
                grmRevised4 = addSuffixPlantFoodSource(grm)
                grmRevised5 = addSuffixPlantBracketedFoodSource(grm)
                # Matching Test for 3-gram chunk
                if (grm in resourceTermsDict.keys()):
                    partialMatchedList.append(grm)
                    # statusAddendum = "Match with 3-Gram Chunk"+statusAddendum
                elif (grm in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grm)
                    # statusAddendum = "Match with 3-Gram Chunk"+statusAddendum
                elif (grm in resourceBracketedPermutationTermsDict.keys()):
                    resourceId = resourceBracketedPermutationTermsDict[grm]
                    partialMatchedList.append(grm)
                    statusAddendum = "[Permutation of Tokens in Bracketed Resource Term]"
                    statusAddendumSet.append("Permutation of Tokens in Bracketed Resource Term")
                elif (grmRevised1 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised1)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (Food Product) Treatment to Input")
                elif (grmRevised2 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised2)
                    statusAddendum = statusAddendum + "[Another Suffix Treatment]"
                    statusAddendumSet.append("Suffix (Product) Treatment to Input")
                elif (grmRevised3 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised3)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (as food source) Treatment to Input")
                elif (grmRevised4 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised4)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (plant as food source) Treatment to Input")
                elif (grmRevised5 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised5)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix ((plant) as food source) Treatment to Input")

        # This is the case of making 2-gram (bigram) chunks and subsequent processing for cleaned samples
        newChunk2Grams = ngrams(newChunk, 2)
        newChunk2Grams = combi(newChunkTokens, 2)
        for nc in newChunk2Grams:
            grm1 = ' '.join(nc)
            setPerm = allPermutations(grm1)
            for perm in setPerm:
                grm = ' '.join(perm)
                if (grm in abbreviationDict.keys()):  # rule for abbreviation
                    grm = abbreviationDict[grm]
                    statusAddendum = statusAddendum + "[Abbreviation-Acronym Treatment]"
                    statusAddendumSet.append("Abbreviation-Acronym Treatment")
                if (grm in nonEnglishWordsDict.keys()):  # rule for abbreviation
                    grm = nonEnglishWordsDict[grm]
                    statusAddendum = statusAddendum + "[Non English Language Words Treatment]"
                    statusAddendumSet.append("Non English Language Words Treatment")
                if (grm in synonymsDict.keys()):  ## Synonyms taken care of- need more synonyms
                    grm = synonymsDict[grm]
                    statusAddendum = statusAddendum + "[Synonym Usage]"
                    statusAddendumSet.append("Synonym Usage")

                grmRevised1 = addSuffixFoodProduct(grm)
                grmRevised2 = addSuffixProduct(grm)
                grmRevised3 = addSuffixFoodSource(grm)
                grmRevised4 = addSuffixPlantFoodSource(grm)
                grmRevised5 = addSuffixPlantBracketedFoodSource(grm)
                # Matching Test for 2-gram chunk
                if (grm in resourceTermsDict.keys()):
                    partialMatchedList.append(grm)
                    # statusAddendum = "Match with 2-Gram Chunk"+statusAddendum
                elif (grm in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grm)
                    # statusAddendum = "Match with 2-Gram Chunk"+statusAddendum
                elif (grm in resourceBracketedPermutationTermsDict.keys()):
                    resourceId = resourceBracketedPermutationTermsDict[grm]
                    partialMatchedList.append(grm)
                    statusAddendum = "[Permutation of Tokens in Bracketed Resource Term]"
                    statusAddendumSet.append("Permutation of Tokens in Bracketed Resource Term")
                elif (grmRevised1 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised1)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (Food Product) Treatment to Input")
                elif (grmRevised2 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised2)
                    statusAddendum = statusAddendum + "[Another Suffix Treatment]"
                    statusAddendumSet.append("Suffix (Product) Treatment to Input")
                elif (grmRevised3 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised3)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (as food source) Treatment to Input")
                elif (grmRevised4 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised4)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix (plant as food source) Treatment to Input")
                elif (grmRevised5 in resourceRevisedTermsDict.keys()):
                    partialMatchedList.append(grmRevised5)
                    statusAddendum = statusAddendum + "[Suffix Treatment]"
                    statusAddendumSet.append("Suffix ((plant) as food source) Treatment to Input")

                # Here the qualities are used for semantic taggings --- change elif to if for qualities in addition to
                elif (grm in qualityLowerDict.keys()):
                    quality = qualityLowerDict[grm]
                    partialMatchedList.append(grm)
                    statusAddendum = statusAddendum + "[Using Semantic Tagging Resources]"
                    statusAddendumSet.append("Using Semantic Tagging Resources")

        # resourcePermutationTermsDict.keys()
        # This is the case of making 1-gram (unigram) chunks and subsequent processing for cleaned samples
        #newChunk1Grams = ngrams(newChunk, 1)
        newChunk1Grams = combi(newChunkTokens, 1)
        for nc in newChunk1Grams:
            grm = ' '.join(nc)
            if (grm in synonymsDict.keys()):  ## Synonyms taken care of- need more synonyms
                grm = synonymsDict[grm]
                statusAddendum = statusAddendum + "[Synonym Usage]"
                statusAddendumSet.append("Synonym Usage")

            grmRevised1 = addSuffixFoodProduct(grm)
            grmRevised2 = addSuffixProduct(grm)
            grmRevised3 = addSuffixFoodSource(grm)
            grmRevised4 = addSuffixPlantFoodSource(grm)
            grmRevised5 = addSuffixPlantBracketedFoodSource(grm)
            # Matching Test for 1-gram chunk
            if (grm in resourceTermsDict.keys()):
                partialMatchedList.append(grm)
                # statusAddendum = "Match with 1-Gram Chunk"+statusAddendum

            elif (grm in resourceRevisedTermsDict.keys()):
                partialMatchedList.append(grm)
                # statusAddendum = "Match with 1-Gram Chunk"+statusAddendum
            elif (grm in resourceBracketedPermutationTermsDict.keys()):
                resourceId = resourceBracketedPermutationTermsDict[grm]
                partialMatchedList.append(grm)
                statusAddendum = "[Permutation of Tokens in Bracketed Resource Term]"
                statusAddendumSet.append("Permutation of Tokens in Bracketed Resource Term")

            elif (grmRevised1 in resourceRevisedTermsDict.keys()):
                partialMatchedList.append(grmRevised1)
                statusAddendum = statusAddendum + "[Suffix Treatment]"
                statusAddendumSet.append("Suffix (Food Product) Treatment to Input")
            elif (grmRevised2 in resourceRevisedTermsDict.keys()):
                partialMatchedList.append(grmRevised2)
                statusAddendum = statusAddendum + "[Another Suffix Treatment]"
                statusAddendumSet.append("Suffix (Product) Treatment to Input")
            elif (grmRevised3 in resourceRevisedTermsDict.keys()):
                partialMatchedList.append(grmRevised3)
                statusAddendum = statusAddendum + "[Suffix Treatment]"
                statusAddendumSet.append("Suffix (as food source) Treatment to Input")
            elif (grmRevised4 in resourceRevisedTermsDict.keys()):
                partialMatchedList.append(grmRevised4)
                statusAddendum = statusAddendum + "[Suffix Treatment]"
                statusAddendumSet.append("Suffix (plant as food source) Treatment to Input")
            elif (grmRevised5 in resourceRevisedTermsDict.keys()):
                partialMatchedList.append(grmRevised5)
                statusAddendum = statusAddendum + "[Suffix Treatment]"
                statusAddendumSet.append("Suffix ((plant) as food source) Treatment to Input")
            elif (grm in qualityLowerDict.keys()):
                quality = qualityLowerDict[grm]
                partialMatchedList.append(grm)
                statusAddendum = statusAddendum + "[Using Semantic Tagging Resources]"
                statusAddendumSet.append("Using Semantic Tagging Resources")

        partialMatchedSet = set(partialMatchedList)  # Makes the set of all matched components from the above processing
        status = "GComponent Match"

        # This adds to the component matching by looking for the matches of Chunks created based on POS Tagging rule
        if (prevPhraseStr in abbreviationDict.keys()):  # rule for abbreviation
            prevPhraseStr = abbreviationDict[prevPhraseStr]
        if (prevPhraseStr in nonEnglishWordsDict.keys()):  # rule for abbreviation
            prevPhraseStr = nonEnglishWordsDict[prevPhraseStr]
            statusAddendum = statusAddendum + "[Non English Language Words Treatment]"
            statusAddendumSet.append("Non English Language Words Treatment")

        if (prevPhraseStr in resourceTermsDict.keys() and prevPhraseStr not in partialMatchedSet):
            if (len(partialMatchedSet) > 0):
                status = "GComponent Match"
                statusAddendum = statusAddendum + "[Additional Match From POS Tagging Rule]"
                statusAddendumSet.append("Additional Match From POS Tagging Rule")
            else:
                status = "GComponent Match"
                statusAddendum = statusAddendum + "[Match with POS Tagging Rule]"
                statusAddendumSet.append("Match with POS Tagging Rule")
            partialMatchedSet.add(prevPhraseStr)
        elif (prevPhraseStr in resourceRevisedTermsDict.keys() and prevPhraseStr not in partialMatchedSet):
            if (len(partialMatchedSet) > 0):
                status = "GComponent Match"
                statusAddendum = statusAddendum + "[Additional Match from POS Tagging Rule using also Resource Treatment]"
                statusAddendumSet.append("Additional Match From POS Tagging Rule using also Resource Treatment")
            else:
                status = "GComponent Match"
                statusAddendum = statusAddendum + "[Match with POS Tagging Rule using also Resource Treatment]"
                statusAddendumSet.append("Match with POS Tagging Rule using also Resource Treatment")
            partialMatchedSet.add(prevPhraseStr)

        if (prevPhraseStr in resourceTermsDict.keys() and prevPhraseStr not in partialMatchedSet):
            if (len(partialMatchedSet) > 0):
                status = "GComponent Match"
                statusAddendum = statusAddendum + "[Additional Match From POS Tagging Rule]"
                statusAddendumSet.append("Additional Match From POS Tagging Rule")
            else:
                status = "GComponent Match"
                statusAddendum = statusAddendum + "[Match with POS Tagging Rule]"
                statusAddendumSet.append("Match with POS Tagging Rule")
            partialMatchedSet.add(prevPhraseStr)

        elif (prevPhraseStr in resourceBracketedPermutationTermsDict.keys() and prevPhraseStr not in partialMatchedSet):
            if (len(partialMatchedSet) > 0):
                status = "GComponent Match"
                statusAddendum = statusAddendum + "[Additional Match from POS Tagging Rule using also Bracketed Resource Permutation  Treatment]"
                statusAddendumSet.append("Additional Match From POS Tagging Rule using also Bracketed Resource Permutation  Treatment")
            else:
                status = "GComponent Match"
                statusAddendum = statusAddendum + "[Match with POS Tagging Rule using also Bracketed Resource Permutation  Treatment]"
                statusAddendumSet.append("Match with POS Tagging Rule using also Bracketed Resource Permutation  Treatment")
            partialMatchedSet.add(prevPhraseStr)




        sampleTokens = word_tokenize(newPhrase.lower())
        for tkn in sampleTokens:

            if (tkn in processDict.keys()):
                if (len(
                        sampleTokens) >= 2):  # Only one word and that is process only- skipped  and tkn.lower() != "ground"
                    proc = processDict[tkn]
                    partialMatchedSet.add(tkn)
                    statusAddendumSet.append("Using Semantic Tagging Resources for Processes")
                if (tkn.lower() == "frozen"):
                    proc = processDict[tkn]
                    print("---------------------------------pppppppppppppppp    " + str(proc))

            date_result = False
            if len(tkn) > 6 and ("/" in tkn or "-" in tkn):
                date_result = is_date(tkn)
            number_result = is_number(tkn)
            if (date_result is True):  # DID change here elif to if - evaluate
                dateTag = "[DateOrDay]"
                partialMatchedSet.add(tkn + "==" + dateTag)
                statusAddendumSet.append("Using Semantic Tagging -[DateOrDay]")

            if (number_result is True):  # DID change here elif to if - evaluate
                numberTag = "[CARDINAL-ORDINAL]"
                partialMatchedSet.add(tkn + "==" + numberTag)
                statusAddendumSet.append("Using Semantic Tagging -[CARDINAL-ORDINAL]")

        # Checking of coverage of tokens for sample as well overall dataset
        coveredTSet = []
        remainingTSet = []
        for tknstr in partialMatchedSet:
            strTokens = word_tokenize(tknstr.lower())
            for eachTkn in strTokens:
                if ("==" in eachTkn):
                    resList = eachTkn.split("==")
                    entityPart = resList[0]
                    entityTag = resList[1]
                    coveredTSet.append(entityPart)
                    coveredAllTokensSet.append(entityPart)
                else:
                    coveredTSet.append(eachTkn)
                    coveredAllTokensSet.append(eachTkn)

        for chktkn in sampleTokens:
            if (chktkn not in coveredTSet):
                remainingTSet.append(chktkn)
            if (chktkn not in coveredAllTokensSet):
                remainingTokenSet.append(chktkn)

        for matchstring in partialMatchedSet:
            if (matchstring in resourceTermsDict.keys()):
                resourceId = resourceTermsDict[matchstring]
                partialMatchedResourceList.append(matchstring + ":" + resourceId)
            elif (matchstring in resourceRevisedTermsDict.keys()):
                resourceId = resourceRevisedTermsDict[matchstring]
                partialMatchedResourceList.append(matchstring + ":" + resourceId)
            elif (matchstring in resourcePermutationTermsDict.keys()):
                resourceId = resourcePermutationTermsDict[matchstring]
                resourceOriginalTerm = resourceTermsIDBasedDict[resourceId]
                partialMatchedResourceList.append(resourceOriginalTerm.lower() + ":" + resourceId)
            elif (matchstring in resourceBracketedPermutationTermsDict.keys()):
                resourceId = resourceBracketedPermutationTermsDict[matchstring]
                resourceOriginalTerm = resourceTermsIDBasedDict[resourceId]
                resourceOriginalTerm = resourceOriginalTerm.replace(",", "=")
                partialMatchedResourceList.append(resourceOriginalTerm.lower() + ":" + resourceId)
            elif (matchstring in processDict.keys()):
                resourceId = processDict[matchstring]
                partialMatchedResourceList.append(matchstring + ":" + resourceId)
            elif (matchstring in qualityDict.keys()):
                resourceId = qualityDict[matchstring]
                partialMatchedResourceList.append(matchstring + ":" + resourceId)
            elif (matchstring in qualityLowerDict.keys()):
                resourceId = qualityLowerDict[matchstring]
                partialMatchedResourceList.append(matchstring + ":" + resourceId)
            elif ("==" in matchstring):
                resList = matchstring.split("==")
                entityPart = resList[0]
                entityTag = resList[1]
                partialMatchedResourceList.append(entityPart + ":" + entityTag)

        partialMatchedResourceListSet = set(partialMatchedResourceList)
        retainedSet = []

        if (len(partialMatchedResourceListSet) > 0):
            retainedSet = retainedPhrase(str(partialMatchedResourceListSet))
            print("retainedSetretainedSetretainedSetretainedSet " + str(retainedSet))
            # HERE SHOULD HAVE ANOTHER RETAING SET

        statusAddendumSetFinal = set(statusAddendumSet)
        if (len(partialMatchedSet) > 0):
            fw.write("	" + str(partialMatchedSet) + "	" + str(
                partialMatchedResourceListSet) + "\t" + str(retainedSet) + "\t" + str(
                len(retainedSet)) + "\t" + status + "\t" + str(statusAddendumSetFinal) + "	" + str(
                remainingTSet))
            compctr = 0
            fw.write("\t")
            for comp in retainedSet:
                compctr += 1
                if (compctr == 1):
                    fw.write("Component" + str(compctr) + "-> " + str(comp))
                else:
                    fw.write(", Component" + str(compctr) + "-> " + str(comp))
            trigger = True
        else:
            fw.write("	" + str(partialMatchedSet) + "	" + str(
                partialMatchedResourceList) + "	\t" + "\t" + "Sorry No Match" + "\t" + str(
                remainingTSet))

        fw1.write("\n" + sampleid + "	" + sample + "	" + str(remainingTSet))

remainingTokenSet1 = set(remainingTokenSet)
fw.write("	xxxxxxxxxxxx\n" + str(len(remainingTokenSet1)))

fw.write("	\n\n\n" + str(
    remainingTokenSet1))

fw.close()
fw1.close()

# ======================================EXTRA - NOT USED Stuff=====================================================


'''


# Method- Iterating over string of multitokens by reducing one token each time   (Not Used Currently)
def reduceChunk(thestring, starting):
    if thestring.startswith(starting):
        return thestring[len(starting):]
    return thestring

# Method- Iterating over string of multitokens by reducing one token each time staring from end  (Not Used Currently)
def rchop(thestring, ending):
  if thestring.endswith(ending):
    return thestring[:-len(ending)]
  return thestring


#Method to get the definition for an input term - (Currently Not Used)
def wikiDefinition(term):
    output=""
    try:
        defi = wikipedia.page(term)
        # defi = wikipedia.summary(resTerm, sentences=1)
        defititle = (str(defi.title)).lower()
        defiurl = (str(defi.url))
    except:
        defi = None
        defititle = ""
    if defi and defititle == term:
        summ = (wikipedia.summary(term, sentences=1)).encode('utf-8')   #.encode('utf-8')
        summutf = summ.decode('utf-8')
        output=term+": ("+defiurl+"):"+str(summutf)
    return output





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




         actualResourceTerm = ""
            for k1, v1 in resourceTermsDict.items():
                if v1 == resourceId:
                    actualResourceTerm = k1
                    break





    # Rule4: Annotate all the Full Term Matches of Terms with plural treatment
    elif (sample.lower() in resourceTermsDict.keys()):
        resourceId = resourceTermsDict[sample.lower()]
        # print(sample + "	" + resourceId + "	Full Term Match")
        fw.write("	" + sample.lower() + "	" + resourceId + "	Full Term Match but with treatment of singular plural")'''


