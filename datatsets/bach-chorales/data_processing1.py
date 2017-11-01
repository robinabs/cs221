import numpy as np
import random

def read_data(featuresSet):
    fileName = "chorales.lisp"
    featL = ['st', 'pitch', 'dur', 'keysig', 'timesig', 'fermata']
    n = len(featL)
    features = list()

    # creating ordered list of desired features
    for i in range(n):
        if featL[i] in featuresSet:
            features.append(featL[i])
    n = len(features)
    choralInd = 0
    chorals = dict()
    with open(fileName, 'r') as f:
        for l in f:
            # if empty line, go to next iteration
            if len(l.strip())==0:
                continue

            # setting up dictionary chorals for choralInd
            choralInd += 1
            chorals[choralInd] = dict()
            for i in range(n):
                chorals[choralInd][features[i]] = list()

            posFeature = 0
            posVal = 0
            featureInd = 0
            feature = features[featureInd]

            # find feature name, then feature value then switches feature
            posFeature = l.find(feature, posVal)
            while posFeature >= 0:
                posVal = l.find(')', posFeature)
                val = int(l[(posFeature+len(feature)+1):posVal])
                chorals[choralInd][feature].append(val)
                featureInd += 1
                feature = features[featureInd%n]
                posFeature = l.find(feature, posVal)

    return chorals

featuresSet = {'pitch'}
chorals = read_data(featuresSet)
#print(chorals)

m = 0
pitches_list = []
for key in chorals:
    m += len(chorals[key]['pitch'])
    for p in chorals[key]['pitch']:
        if p in pitches_list:
            continue
        else:
            pitches_list.append(p)

pitches_list = sorted(pitches_list)
p = len(pitches_list)
#print(pitches_list)

pitches = [] #One long list of pitches to train.
for key in chorals:
    for pit in chorals[key]['pitch']:
        pitches.append(pit)

markov = {}
for pitch in pitches_list:
    markov[pitch] = {}
for key in markov:
    for pitch in pitches_list:
        markov[key][pitch] = {}

def smoothing(three_dim_dict,factor):
    for key1 in three_dim_dict:
        for key2 in three_dim_dict[key1]:
            for pitch in pitches_list:
                three_dim_dict[key1][key2][pitch] = 1/factor
    return(0)

def no_smoothing(three_dim_dict):
    for key1 in three_dim_dict:
        for key2 in three_dim_dict[key1]:
            for pitch in pitches_list:
                three_dim_dict[key1][key2][pitch] = 0
    return(0)

#smoothing(markov,p) #Run this line if you'd like to smooth.
no_smoothing(markov) #Run this line if you would not like to smooth.

def create_markovestimate(number):
    if number == 1:
        markovestimate = {}
        for pitch in pitches_list:
            markovestimate[pitch] = {}
        for key in markovestimate:
            for pitch in pitches_list:
                markovestimate[key][pitch] = 0
    if number == 0:
        markovestimate = {}
        for pitch in pitches:
            if pitch in markovestimate:
                markovestimate[pitch] += 1/m
            else:
                markovestimate[pitch] = 1/m
    return(markovestimate)

mrk1e = create_markovestimate(1)
mrk0e = create_markovestimate(0)
sum1=np.zeros((20,1))


for first, second in zip(pitches, pitches[1:]):
    mrk1e[first][second] += 1

for key1 in mrk1e:
    total_sum = 0
    for key2 in mrk1e[key1]:
        total_sum += mrk1e[key1][key2]
    for key2 in mrk1e[key1]:
        if total_sum != 0:
            mrk1e[key1][key2] /= total_sum


#print(markov)
#markov is a big dictionary, which stores the probability of obtaining
#a certain pitch, having seen two pitches beforehand. We initialize every
#entry at 0.
#We will divide by number of examples at the end.

for first, second, third in zip(pitches, pitches[1:], pitches[2:]):
    markov[first][second][third] += 1

for key1 in markov:
    for key2 in markov[key1]:
        total_sum = 0
        for key3 in markov[key1][key2]:
            total_sum += markov[key1][key2][key3]
        for key3 in markov[key1][key2]:
            if total_sum != 0:
                markov[key1][key2][key3] /= total_sum

#The above normalizes the probability. I.e., we want that given the two
#previous pitches, the sum of the probabilities of the next pitch equal 1.


# with open('pitches_io.txt','r') as f:
#     for line in f:
#         l = line.split()
#         for word in l:
#             song.append(int(word))

#Run below in the case of only looking at 2-estimates.

song_length = 45
song = [67,67]

# for i in range(song_length):
#     first = song[i]
#     second = song[i+1]
#     random_no = random.uniform(0,1)
#     sum_comp = 0
#     for third in markov[first][second]:
#         sum_comp += markov[first][second][third]
#         if (sum_comp > random_no):
#             new_note = third
#             sum_comp = -2
#     song.append(new_note)

for i in range(song_length):
    first = song[i]
    second = song[i+1]
    random_no = random.uniform(0,1)
    sum_comp = 0
    for third in markov[first][second]:
        sum_comp += (1/2)*markov[first][second][third] + (1/3)*mrk1e[second][third] + (1/6)*mrk0e[third]
        if (sum_comp > random_no):
            new_note = third
            sum_comp = -2
    song.append(new_note)

print(song)

with open('pitches_io.txt','a') as f:
    for note in song:
        f.write(' ')
        f.write(str(note))





