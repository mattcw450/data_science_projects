# -*- coding: utf-8 -*-
"""
Created on Thu Nov 29 07:21:01 2018

@author: Matthew

Task 2 Neat Version

Applied Data Science

Coursework 3: Sentiment Analysis
"""

import pandas as pd
import numpy as np
import re
import time
from sklearn.utils import shuffle



start_time = time.time()


########### 1 ############### read data
print('Reading the Data')
tweetsRaw = pd.read_csv('tweets_sentiment.csv', sep=',', encoding = "ISO-8859-1", error_bad_lines=False, low_memory=False)








########### 2 ############### clean data
# There's a couple of 'bad' tweets (ones that put part of the tweet in columns 3, 4, 5) so I'll get rid of them
print('Removing the unclean tweets')
bad = tweetsRaw['Unnamed: 2'].dropna()
bad.index
# bad.index shows that the index is 8834 and 535880 so we'll drop these rows...
tweets = tweetsRaw.drop([8834, 535880])
# can also drop columns 3, 4, 5 now...
tweets = tweets.drop(['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4'], axis=1)




########### 3 ############## shuffle data
"""
Recommended to shuffle the tweets around to avoid any bias in how they're 
laid out.
 
For purposes of measuring improvement, this has been commented out
"""
#tweets = shuffle(tweets)







############ 4 ############# split into good and bad
# Need to make a good and bad word list
print('Splitting the tweets into good and bad')
tweetsArray = np.array(tweets)
goodTweets = tweetsArray[tweetsArray[:,0]==1,:]
badTweets = tweetsArray[tweetsArray[:,0]==0,:]








############ 5 ############## split into train and test data
"""
I need to have a train and test dataset. I will use an 80:20 split but since 
there are more good tweets than bad tweets, I will make sure we take 80% from
each good and bad
"""
splitGood = int(np.floor(len(goodTweets)*0.8))
splitBad = int(np.floor(len(badTweets)*0.8))

goodTweetsTrain = goodTweets[:splitGood]
goodTweetsTest = goodTweets[splitGood:]
badTweetsTrain = badTweets[:splitBad]
badTweetsTest = badTweets[splitBad:]








############ 6 ############# Make a tokenising function
print('Making a tokenising function')
def CleanStrings(string):
    """    
    Returns a cleaned string
    """
    assert type(string)==str,"Input not a string"
    string = (string).replace(',', '')
    string = (string).replace('.', '')
#    string = (string).replace(':', '')     # Because of emojis
#    string = (string).replace(';', '')     # Because of emojis
    string = (string).replace("'", '')
    string = (string).replace('"', '')
    string = (string).replace('!', '')
    string = (string).replace('?', '')
#    string = (string).replace('(', '')
#    string = (string).replace(')', '')
    string = (string).replace('£', '')
    string = (string).replace('$', '')
    string = (string).replace('%', '')
#    string = (string).replace('/', ' ')
    string = (string).replace("\\", '')    
    string = (string).replace('[', '')
    string = (string).replace(']', '')
    string = (string).replace('{', '')
    string = (string).replace('}', '')
    string = string.lower()
    string = re.sub(r'[0-9]+', '', string)
    return string



# Now I need a tokenising function
def TokeniseInput(item):
    """
    Tokenises and cleans the input
    Outputs a tokenised clean list
    """
    if type(item)!=str:
        item = str(item)
    item = CleanStrings(item)
    item = item.split()
    
    return item






############### 7 ############### now make lists of good and bad words
print('Tokenising the tweets')
# Will take about 7 seconds...
goodWords = []
for i in goodTweetsTrain[:,1]:
    tokenisedTweet = TokeniseInput(i)
    for word in tokenisedTweet:
        goodWords.append(word)

badWords = []
for i in badTweetsTrain[:,1]:
    tokenisedTweet = TokeniseInput(i)
    for word in tokenisedTweet:
        badWords.append(word)
   




"""
This bit is now only going to be included in Task 2
"""
################ 8 #############  make stopwords  
#"""
#Now need a stop words dictionary. All the useless words like 'and' 'that' 'then'
#can be removed from our badUnique and goodUnique lists since we don't want these 
#contributing to the probability that a tweet is good or bad.
#
#e.g. a bad tweet: Then they are a SERIAL KILLER because they are really something. 
#                  (Doesn't make much sense but the only words we really care about
#                  are 'serial killer') all the other words probably appear in both 
#                  good and bad tweets an equal number of times so we can get rid of
#                  them since they don't tell us much. Whereas the words 'serial killer'
#                  probably appear far more frequently in bad tweets than good tweets.
#
#Natural Language Toolkit has a list of these stopwords
#"""
#print('Making the stopwords')
##import nltk
#from nltk.corpus import stopwords
#stopWords = list(set(stopwords.words('english')))
#
## Need to tokenise these as they will match the ones in goodUnique and badUnique
#stopWords = TokeniseInput(stopWords)
#
#
#
#
#
#
#
#
#
#
################# 9 ############### make a dictionary of words that arent stopwords
#"""
#Stopwords will be taken out
#"""
#print('Making dictionary of words that aren\'t stopwords')
#def FreqDict(list_of_words, list_of_stopwords):
#    freqD = {}
#    allWordsNoStop = []
#    for word in list_of_words:
#        if word not in list_of_stopwords:
#            allWordsNoStop.append(word)
#            freqD[word] = 0
#    for word in allWordsNoStop:
#        freqD[word] += 1
#    return freqD, allWordsNoStop    
#
#goodDictFreq, goodWordsNoStop = FreqDict(goodWords, stopWords)
#badDictFreq, badWordsNoStop = FreqDict(badWords, stopWords)





   





############### 10 ################# Find frequency of each word (or tuple of words)     
"""
We will make dictionaries for good and bad words. The words are keys and the 
values are the frequency that each word appears.
"""
def FreqDict(list_of_words):
    freqD = {}
    for word in list_of_words:
        freqD[word] = 0
    for word in list_of_words:
        freqD[word] += 1
    return freqD        

goodDictFreq = FreqDict(goodWords)
badDictFreq = FreqDict(badWords)







############### 11 ################# remove the words with low freqencies
print('Testing the accuracy')
bestK = np.nan
bestAccuracy = 0.0

"""
BetterDic is just a way to convert our original dictionaries of frequencies
into dictionaries containing only the words with probabilities greater than 
a given value. This value can be changed (at the moment it is 1).

If the runtime gets significanly impacted, we can change this to only look at 
words that appear more than X times.
"""
def BetterDic(dic):
    betterDic = {}
    tot = 0
    for word in dic.keys():
        if dic[word] >= 1:                             # Here we can change this number (can call k and loop if wanted)
            betterDic[word] = dic[word]
            tot += dic[word]
    return betterDic, tot

betterGoodDict, totGoodWords = BetterDic(goodDictFreq)
betterBadDict, totBadWords = BetterDic(badDictFreq)

total = totGoodWords + totBadWords











############ 12 ############ make a dictionary of probabilities
"""
ProbDic is just a dictionary that converted the previous frequency dictionary 
into a dictionary that has words as keys and probabilities that that word appears
as the value.
"""
def ProbDict(dic, tot):
    probDic = {}
    for word in dic.keys():
        probDic[word] = dic[word] / tot
    return probDic

goodProb = ProbDict(betterGoodDict, totGoodWords)
badProb = ProbDict(betterBadDict, totBadWords)











############## 13 ############## give a prediction for a tweet
"""
Note: this doesn't give the actual probabilities (haven't normalised) but it lets
us pick the biggest (more likely) outcome
"""
def Predict_Tweet(tweet):
    clean_tweet = TokeniseInput(tweet)
    prob_good = 0
    prob_bad = 0 
    for word in clean_tweet:
        if word in goodProb.keys() and word in badProb.keys():
            prob_good += np.log(goodProb[word])
            prob_bad += np.log(badProb[word])
    # Need to add the log of prob good and bad  (in naive bayes formula this is like * by prob good)
    prob_good += np.log(len(goodTweetsTrain)/(len(goodTweetsTrain)+len(badTweetsTrain)))
    prob_bad += np.log(len(badTweetsTrain)/(len(goodTweetsTrain)+len(badTweetsTrain)))
    return prob_good, prob_bad










############## 14 ############## now see the accuracy on our test set
"""
Test_Good and Test_Bad are functions that compare the outcomes of the calculated
probabilities (above) and then depending on which test set we're looking at will 
return a 1 or a 0. 
When tesing good tweets, 
            if P(Good) > P(Bad): will return 1
When tesing bad tweets, 
            if P(Good) < P(Bad): will return 1
"""
def Test_Good(logGood, logBad):
    maxi = np.max([logGood, logBad])
    if logGood == maxi:
        return 1
    if logBad == maxi:
        return 0
    
    
def Test_Bad(logGood, logBad):
    maxi = np.max([logGood, logBad])
    if logGood == maxi:
        return 0
    if logBad == maxi:
        return 1
    




############## 15 ############## Now lets see the accuracy

# Just setting some parameters first
y = 0
x = len(goodTweetsTest)
z = 0
w = len(badTweetsTest)


for i in goodTweetsTest:
    lg, lb = Predict_Tweet(i)
    y += Test_Good(lg, lb)

for i in badTweetsTest:
    lg, lb = Predict_Tweet(i)
    z += Test_Bad(lg, lb)
    
total_accuracy = (y+z)/(x+w)
print('Accuracy =', total_accuracy)
print('Good Accuracy =', y/x)
print('Bad Accuracy =', z/w)


if total_accuracy > bestAccuracy:
    bestAccuracy = total_accuracy
#    bestK = k


end_time = time.time()

print('Runtime was', end_time - start_time, 'seconds')


