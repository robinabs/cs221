
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

featuresSet = {'keysig', 'pitch'}
chorals = read_data(featuresSet)
print(chorals)
