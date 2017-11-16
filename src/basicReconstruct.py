import collections
import copy

import cspUtil
import dataUtil

def countSequences(inputList, N):
    out = collections.defaultdict(float)
    for i in range(len(inputList)-N+1):
        if [inputList[i+k] != None for k in range(N)] == [True for _ in range(N)]:
            seq = tuple([inputList[i+k] for k in range(N)])
        out[seq] += 1

    factor= 1.0 / sum(out.itervalues())
    for k in out:
          out[k] *= 10*factor

    return out

def createRythmCSP(windowedPrimTrack, bi=True, tri=False):
    cspRythm = cspUtil.CSP()

    # Creating "units" variables
    transitions = [note[1] for note in windowedPrimTrack]
    for unitNum in range(windowStart, windowEnd+1):
        unit = windowedPrimTrack[unitNum]
        cspRythm.add_variable(('U', unitNum), [(unit[0],True),(unit[0],False)])

    if bi:
        # Create binary factors proportional to frequence of apparition of pairs
        biSequences = countSequences(transitions, 2)
        print "bi"
        print biSequences
        for varNum in range(windowStart, windowEnd):
            cspRythm.add_binary_factor(('U', varNum), ('U', varNum+1), lambda u1, u2 : biSequences[(u1[1], u2[1])])
        # Add corner cases
        cspRythm.add_unary_factor(('U', windowStart), lambda u : biSequences[(windowedPrimTrack[windowStart-1][1], u[1])])
        cspRythm.add_unary_factor(('U', windowEnd)  , lambda u : biSequences[(u[1], windowedPrimTrack[windowEnd+1][1])])

    if tri:
        # Creating "binary" variables for 3-sequences handling
        domain = [(False, False), (False, True), (True, False), (True, True)]
        for unitNum in range(windowStart, windowEnd+1):
            cspRythm.add_variable(('B', unitNum), copy.deepcopy(domain))

        # Creating binary factors proportional to frequence of apparition of triads
        triSequences = countSequences(transitions, 3)

        for varNum in range(windowStart, windowEnd+1):
            # Add constraint B_i[0] = U_i[1]
            cspRythm.add_binary_factor(('U', varNum), ('B', varNum), lambda u, b: u[1] == b[0])

            if varNum != windowEnd:
                # Add consitency contraints B_i[0] = B_{i+1}[1] and frequency factor
                cspRythm.add_binary_factor(('B', varNum), ('B', varNum+1), \
                                           lambda b1, b2: (b1[0] == b2[1]) * triSequences[(b1[1], b1[0], b2[0])])
        # Add corner cases
        cspRythm.add_unary_factor(('B', windowStart), lambda b: b[1] == windowedPrimTrack[windowStart-1])
        cspRythm.add_unary_factor(('B', windowEnd)  , \
                lambda b: triSequences[(b[1], b[0], windowedPrimTrack[windowEnd+1])] \
                        * triSequences[(b[0], windowedPrimTrack[windowEnd+1], windowedPrimTrack[windowEnd+2])])

    return cspRythm

def createPitchCSP(pitchTrack, triSeq=False):
    cspPitch = cspUtil.CSP()

    # Creating "units" variables #
    # Domains
    minPitch, maxPitch = pitchTrack[0], pitchTrack[0]
    for pitch in pitchTrack:
        if type(pitch) == int:
            minPitch, maxPitch = min(minPitch, pitch), max(maxPitch, pitch)
    domains = tuple(list(range(minPitch, maxPitch+1)) + ['silence'])
    for pitchNum in range(windowStart, windowEnd+1):
        pitch = pitchTrack[pitchNum]
        cspPitch.add_variable(('U', pitchNum), copy.deepcopy(domains))

    # Create binary factors proportional to frequence of apparition of pairs
    biSequences = countSequences(pitchTrack, 2)
    print "bi"
    print biSequences
    for varNum in range(windowStart, windowEnd):
        cspPitch.add_binary_factor(('U', varNum), ('U', varNum+1), lambda p1, p2 : biSequences[(p1, p2)])
    # Add corner cases
    cspPitch.add_unary_factor(('U', windowStart), lambda p : biSequences[(pitchTrack[windowStart-1], p)])
    cspPitch.add_unary_factor(('U', windowEnd)  , lambda p : biSequences[(p, pitchTrack[windowEnd+1])])

    """
    if triSeq:
        # Creating "binary" variables for 3-sequences handling
        domain = [(False, False), (False, True), (True, False), (True, True)]
        for unitNum in range(windowStart, windowEnd+1):
            cspPitch.add_variable(('B', unitNum), copy.deepcopy(domain))

        # Creating binary factors proportional to frequence of apparition of triads
        triSequences = countSequences(windowedPrimTrack, 3)

        for varNum in range(windowStart, windowEnd+1):
            # Add constraint B_i[0] = U_i[1]
            cspPitch.add_binary_factor(('U', varNum), ('B', varNum), lambda u, b: u[1] == b[0])

            if varNum != windowEnd:
                # Add consitency contraints B_i[0] = B_{i+1}[1] and frequency factor
                cspPitch.add_binary_factor(('B', varNum), ('B', varNum+1), \
                                           lambda b1, b2: (b1[0] == b2[1]) * triSequences[(b1[1], b1[0], b2[0])])
        # Add corner cases
        cspPitch.add_unary_factor(('B', windowStart), lambda b: b[1] == windowedPrimTrack[windowStart-1])
        cspPitch.add_unary_factor(('B', windowEnd)  , \
                lambda b: triSequences[(b[1], b[0], windowedPrimTrack[windowEnd+1])] \
                        * triSequences[(b[0], windowedPrimTrack[windowEnd+1], windowedPrimTrack[windowEnd+2])])
        """

    return cspPitch

midiFile = "../../test/ode.mid"
windowStart, windowEnd = 10, 15
ode = dataUtil.MusicPattern(midiFile)
rythmUnit, windowedPrimTrack = ode.getCorrupt(windowStart, windowEnd)
pitchTrack = [note[0] for note in windowedPrimTrack]
CSP = createRythmCSP(windowedPrimTrack, bi=False, tri=True)
print windowedPrimTrack[(windowStart-1):(windowEnd+2)]
print CSP.variables
print CSP.values
print "unary"
print CSP.unaryFactors
print "binary"
print CSP.binaryFactors
search = cspUtil.BacktrackingSearch()
search.solve(CSP)
