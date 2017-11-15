import collections
import copy

import cspUtil
import dataUtil

midiFile = "../../test/ode.mid"
windowStart, windowEnd = 10, 14
ode = dataUtil.MusicPattern(midiFile)
rythmUnit, windowedPrimTrack = ode.getCorrupt(windowStart, windowEnd)
rythmCSP = createRythmCSP(windowedPrimTrack)
search = cspUtil.BacktrackingSearch()
search.solve(rythmCSP)

def countSequences(primTrack, N):
    N_sequences = collections.defaultdict(int)
    for i in range(len(primTrack)-N+1):
        if [primTrack[i+k][1] != None for k in range(N)] == [True for _ in range(N)]:
            seq = tuple([prim_corrupt[i+k][1] for k in range(N)])
        N_sequences[seq] += 1
    return N_sequences

def createRythmCSP(windowedPrimTrack):
    cspRythm = cspUtil.CSP()

    # Creating "units" variables
    for unitNum in range(windowStart, windowEnd+1):
        unit = windowedPrimTrack[unitNum]
        cspRythm.add_variable(('U', unitNum), [(unit[0],True),(unit[0],False)])

    # Create binary factors proportional to frequence of apparition of pairs
    biSequences = countSequences(windowedPrimTrack, 2)
    for varNum in range(windowStart, windowEnd+1):
        cspRythm.add_binary_factor(('U', varNum), ('U', varNum+1), lambda u1, u2 : biSequences[(u1[1], u2[1])])
    # Add corner cases
    cspRythm.add_unary_factor(('U', windowStart), lambda u : biSequences[(windowedPrimTrack[windowStart-1][1], u[1])])
    cspRythm.add_unary_factor(('U', windowEnd)  , lambda u : biSequences[(u[1], windowedPrimTrack[windowEnd-1][1])])

    # Creating "binary" variables for 3-sequences handling
    domain = [[False, False], [False, True], [True, False], [True, True]]
    for unitNum in range(windowStart, windowEnd+1):
        cspRythm.add_variable(('B', unitNum), copy.deepcopy(domain))

    # Creating binary factors proportional to frequence of apparition of triads
    triSequences = countSequences(windowedPrimTrack, 3)

    for varNum in range(windowStart, windowEnd+1):
        # Add constraint B_i[0] = U_i[1]
        cspRythm.add_binary_factor(('U', varNum), ('B', varNum), lambda u, b: u[1] == b[0])

        if varNum != windowEnd+1:
            # Add consitency contraints B_i[0] = B_{i+1}[1] and frequency factor
            cspRythm.add_binary_factor(('B', varNum), ('B', varNum+1), \
                                       lambda b1, b2: (b1[0] == b2[2]) * triSequences[(b1[1], b1[0], b2[0]))
    # Add corner cases
    cspRythm.add_unary_factor(('B', windowStart), lambda b: b[1] == windowedPrimTrack[windowStart-1])
    cspRythm.add_unary_factor(('B', windowEnd)  , \
            lambda b: triSequences[(b[1], b[0], windowedPrimTrack[windowEnd+1])] \
                    * triSequences[(b[0], windowedPrimTrack[windowEnd+1], windowedPrimTrack[windowEnd+2])]

    return cspRythm
