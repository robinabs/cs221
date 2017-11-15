from fractions import gcd
import midi
import os.path
import sys

class MusicPattern():
    """
    This class represents a musical pattern and provides
    method to convert it across midi, lisp and prim format
    """
    def __init__(self, midiFile=None):
        if midiFile is not None:
            self.read(midiFile)

    def read(self, midiFile):
        self.midiFile    = midiFile
        self.midiPattern = midi.read_midifile(midiFile)

        self.trackIdx = []
        for trackNum, midiTrack in enumerate(self.midiPattern):
            isTrack = False
            for midiEvent in midiTrack:
                if type(midiEvent) == midi.events.NoteOnEvent:
                    isTrack = True
            if isTrack:
                self.trackIdx.append(trackNum)

        self.numTracks   = len(self.trackIdx)
        self.lispTracks  = []
        print "Loaded %s" % midiFile

        # Do midi -> lisp conversion
        self.lispTracks = self.midiToLisp()
        print "Converted to lisp"
        print self.numTracks

        # Do lisp -> prim conversion
        self.primTracks, self.rythmUnits = self.lispToPrim()
        print "Converted to midi"

    def midiToLisp(self, midiPattern=None):
        if midiPattern is None: midiPattern = self.midiPattern
        lispTracks = []
        for midiTrackId, midiTrack in enumerate(midiPattern):
            if midiTrackId not in self.trackIdx: continue

            lispTrack = []
            for eventNum, event in enumerate(midiTrack):
                if type(event)                 == midi.events.NoteOnEvent and \
                   type(midiTrack[eventNum+1]) == midi.events.NoteOffEvent:
                    # If not a silence, add (pitch, dur)
                    if event.tick == 0:
                        pitch  = event.data[0]
                        dur    = midiTrack[eventNum+1].tick - event.tick
                        notes  = [(pitch, dur)]

                    # Otherwise add silence and next note
                    else:
                        notes = [("silence", event.tick)]
                        pitch = midiTrack[eventNum+1].data[0]
                        dur   = midiTrack[eventNum+1].tick
                        notes += [(pitch, dur)]

                    # Add generated notes to track
                    lispTrack += notes
            lispTracks.append(lispTrack)
        return lispTracks

    def lispToPrim(self, lispTracks=None):
        if lispTracks is None: lispTracks = self.lispTracks
        primTracks, rythmUnits = [], []
        for lispTrackNum, lispTrack in enumerate(lispTracks):
            print "Track %d" % lispTrackNum
            min_duration = 0
            durations = [lispTrack[i][1] for i in range(len(lispTrack))]
            rythmUnits.append(reduce(gcd, durations))
            primTrack = []
            for noteNum, note in enumerate(lispTrack):
                assert(note[1] % rythmUnits[-1] == 0)
                primTrack += [(note[0],True) if (i < note[1]/rythmUnits[-1] - 1) else (note[0],False) \
                              for note in lispTrack for i in range(note[1]/rythmUnits[-1])]
            primTracks.append(primTrack)
        return primTracks, rythmUnits

    def primToLisp(self, primTracks=None):
        if primTracks is None: primTracks = self.primTracks
        lispTracks = []
        for trackNum, primTrack in enumerate(primTracks):
            # @robin: a quoi sert ce if ?
            lispTrack = []
            if primTrack:
                i = 0
                while i < len(primTrack):
                    note = [primTrack[i][0], self.rythmUnits[trackNum]]
                    while primTrack[i][1]:
                        note[1] += self.rythmUnist[trackNum]
                        i += 1
                    i+=1
                    lispTrack.append(tuple(note))
            lispTracks.append(lispTrack)

        return lispTracks

    def write(self, fileName=None, lispTracks=None):
        midiPattern = midi.containers.Pattern()
        if self.midiPattern is not None:
            # copy pattern metadata
            midiPattern.format     = self.midiPattern.format
            midiPattern.resolution = self.midiPattern.resolution
            midiPattern.insert(2, self.midiPattern[0])

        # Create tracks
        if lispTracks is None: lispTracks = self.lispTracks
        midiTracks = []
        for _ in range(len(lispTracks)):
            midiPattern.insert(2, midi.containers.Track())
            midiTracks.append([])

        # Generate tracks' NoteOnEvents and NoteOffEvents
        for lispTrackId, lispTrack in enumerate(lispTracks):
            noteNumAfterSilence = -1
            for noteNum, note in enumerate(lispTrack):
                if note[0] == "silence":
                    NoteOnEvent = midi.events.NoteOnEvent(tick=note[1], \
                                                          channel=lispTrackId, \
                                                          data=[lispTrack[noteNum+1][0], 80])

                    NoteOffEvent = midi.events.NoteOffEvent(tick=lispTrack[noteNum+1][1], \
                                                            channel=lispTrackId, \
                                                            data=[lispTrackId[noteNum+1][0], 0])

                    midiTracks[lispTrackId] += [NoteOnEvent, NoteOffEvent]
                    noteNumAfterSilence = noteNum+1

                elif noteNum != noteNumAfterSilence:
                    NoteOnEvent = midi.events.NoteOnEvent(tick=0, \
                                                          channel=lispTrackId, \
                                                          data=[note[0], 80])
                    NoteOffEvent = midi.events.NoteOffEvent(tick=note[1], \
                                                            channel=lispTrackId, \
                                                            data=[note[0], 0])
                    midiTracks[lispTrackId] += [NoteOnEvent, NoteOffEvent]

        # Add tracks to midiPattern
        if self.midiPattern is not None:
            for midiTrackId, midiTrack in enumerate(self.midiPattern):
                if midiTrackId == 0: continue
                for eventNum, event in enumerate(midiTrack):
                    if type(event) not in [midi.events.NoteOnEvent, midi.events.NoteOffEvent]:
                        midiPattern[midiTrackId].append(event)
                    elif type(midiTrack[eventNum-1]) not in \
                    [midi.events.NoteOnEvent, midi.events.NoteOffEvent]:
                        midiPattern[midiTrackId].extend(midiTracks[midiTrackId-1])
        else:
            for midiTrackId, midiTrack in enumerate(midiTracks):
                midiPattern[midiTrackId].extend(midiTracks[midiTrackId])
            midiPattern[0].append(midi.EndOfTrackEvent(tick=1))


        # Write file
        if fileName is None:
            i = 1
            while os.path.isfile(self.midiFile[0:-4] + str(i) + ".mid"):
                i += 1
            fileName = self.midiFile[0:-4] + str(i) + ".mid"

        midi.write_midifile(fileName, midiPattern)
        print "Wrote %s" % fileName

    def window(self, windowStart, windowEnd, trackNum=0):
        assert(0 <= trackNum and trackNum < self.numTracks)
        primTrack = self.primTracks[trackNum]
        start = max(0, windowStart)
        end = min(len(primTrack),windowEnd)
        windowedTrack = list(primTrack)
        for i in range(start, end):
            windowedTrack[i] = (None,None)
        return windowedTrack

    def getCorrupt(self, windowStart, windowEnd, trackNum=0):
        return self.rythmUnits[trackNum], window(windowStart, windowEnd, trackNum)

class BachChorale(MusicPattern):
    """
    This class represents a choral from the Bach dataset
    (https://archive.ics.uci.edu/ml/datasets/Bach+Chorales)
    It provides methods to read from disk and write as .mid
    """

    def __init__(self, choraleFile, choraleNum):
        """
        This constructor loads the choraleNum th chorale
        from the choraleFile file and stores the pitches
        and durations into the self.notes variable
        """
        self.choraleFile = choraleFile
        self.choraleNum  = ((int(choraleNum)-1) % 100) + 1
        self.features    = ["pitch", "dur"]
        self.numTracks   = 1
        self.lispTracks  = [[]]
        self.midiPattern = None

        with open(self.choraleFile, 'r') as f:
            line = f.readlines()[2*(self.choraleNum-1)]
            choraleIdEndPosition = line.find('(', 1)
            self.choraleId = int(line[1:choraleIdEndPosition-1])

            N = len(self.features)
            featurePosition = line.find(self.features[0], 0)
            valueEndPosition = line.find(')', featurePosition)
            while featurePosition >= 0:
                note = []
                for i, feature in enumerate(self.features):
                    val = int(line[(featurePosition+len(feature)+1):valueEndPosition])
                    if feature == "dur": val *= 64
                    note += [val]

                    featurePosition = line.find(self.features[(i+1) % N], valueEndPosition)
                    valueEndPosition = line.find(')', featurePosition)
                self.lispTracks[0] += [tuple(note)]

    def __repr__(self):
        """
        Displays chorale metadata and notes
        """
        ret = "Bach Chorale %d (line %d in file %s)\n" % \
        (self.choraleId, 2*self.choraleNum + 1, self.choraleFile)
        ret += "pitch   dur\n"
        for note in self.lispTracks[0]:
            ret += "   %2d    %2d\n" % note
        return ret


if __name__ == '__main__':
    #myChorale = BachChorale("../dat/bach-chorales/chorales.lisp", 5)
    #myChorale.write("../dat/bach-chorales/mid/chorale5.mid")
    myOde = MusicPattern("../../test/chor_armure.mid")
    print myOde.lispTracks
    print myOde.primTracks
    print myOde.rythmUnits
