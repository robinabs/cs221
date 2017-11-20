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
        self.channels = []
        for trackNum, midiTrack in enumerate(self.midiPattern):
            isTrack = False
            for midiEvent in midiTrack:
                if type(midiEvent) == midi.events.NoteOnEvent:
                    isTrack = True
                    self.channels.append(midiEvent.channel)
                    break

            if isTrack:
                self.trackIdx.append(trackNum)

        self.numTracks   = len(self.trackIdx)
        self.lispTracks  = []
        print "Loaded %s" % midiFile

    def midiToLisp(self):
        lispTracks = []
        for midiTrackId, midiTrack in enumerate(self.midiPattern):
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
        self.lispTracks = lispTracks

    def lispToPrim(self):
        self.primTracks, self.rythmUnits = [], []
        for lispTrackNum, lispTrack in enumerate(self.lispTracks):
            min_duration = 0
            durations = [lispTrack[i][1] for i in range(len(lispTrack))]
            self.rythmUnits.append(reduce(gcd, durations))

            for noteNum, note in enumerate(lispTrack):
                assert(note[1] % self.rythmUnits[-1] == 0)

            primTrack = [(note[0],True) if (i < note[1]/self.rythmUnits[-1] - 1) else (note[0],False) \
                              for note in lispTrack for i in range(note[1]/self.rythmUnits[-1])]
            self.primTracks.append(primTrack)

    def primToLisp(self):
        lispTracks = []
        for trackNum, primTrack in enumerate(self.primTracks):
            lispTrack = []
            if primTrack:
                i = 0
                while i < len(primTrack):
                    note = [primTrack[i][0], self.rythmUnits[trackNum]]
                    while primTrack[i][1]:
                        note[1] += self.rythmUnits[trackNum]
                        i += 1
                    i+=1
                    lispTrack.append(tuple(note))
            lispTracks.append(lispTrack)

        self.reconstructedTracks = lispTracks

    def lispToMidi(self, lispTracks=None):
        midiPatternOut = midi.containers.Pattern()
        if self.midiPattern is not None:
            # copy pattern metadata
            midiPatternOut.format     = self.midiPattern.format
            midiPatternOut.resolution = self.midiPattern.resolution

        # Create tracks
        if lispTracks is None: lispTracks = self.reconstructedTracks
        midiTracksOut = []
        for trackNum, _ in enumerate(self.midiPattern):
            if trackNum in self.trackIdx:
                midiPatternOut.append(midi.containers.Track())
                midiTracksOut.append([])
            else:
                midiPatternOut.append(self.midiPattern[trackNum])


        # Generate tracks' NoteOnEvents and NoteOffEvents
        for lispTrackId, lispTrack in enumerate(lispTracks):
            noteNumAfterSilence = -1
            for noteNum, note in enumerate(lispTrack):
                if note[0] == "silence":
                    NoteOnEvent = midi.events.NoteOnEvent(tick=note[1], \
                                                          channel=self.channels[lispTrackId], \
                                                          data=[lispTrack[noteNum+1][0], 80])

                    NoteOffEvent = midi.events.NoteOffEvent(tick=lispTrack[noteNum+1][1], \
                                                            channel=self.channels[lispTrackId], \
                                                            data=[lispTrack[noteNum+1][0], 0])

                    midiTracksOut[lispTrackId] += [NoteOnEvent, NoteOffEvent]
                    noteNumAfterSilence = noteNum+1

                elif noteNum != noteNumAfterSilence:
                    NoteOnEvent = midi.events.NoteOnEvent(tick=0, \
                                                          channel=self.channels[lispTrackId], \
                                                          data=[note[0], 80])
                    NoteOffEvent = midi.events.NoteOffEvent(tick=note[1], \
                                                            channel=self.channels[lispTrackId], \
                                                            data=[note[0], 0])
                    midiTracksOut[lispTrackId] += [NoteOnEvent, NoteOffEvent]

        # Add tracks to midiPattern
        realTrackIdx = -1
        if self.midiPattern is not None:
            for midiTrackId, midiTrack in enumerate(self.midiPattern):
                if midiTrackId not in self.trackIdx: continue
                realTrackIdx+= 1
                for eventNum, event in enumerate(midiTrack):
                    if type(event) not in [midi.events.NoteOnEvent, midi.events.NoteOffEvent]:
                        midiPatternOut[midiTrackId].append(event)
                    elif type(midiTrack[eventNum-1]) not in \
                    [midi.events.NoteOnEvent, midi.events.NoteOffEvent]:
                        midiPatternOut[midiTrackId].extend(midiTracksOut[realTrackIdx])
        else:
            for midiTrackId, midiTrack in enumerate(midiTracksOut):
                midiPatternOut[midiTrackId].extend(midiTracksOut[midiTrackId])
            midiPatternOut[0].append(midi.EndOfTrackEvent(tick=1))


        self.midiPatternOut = midiPatternOut


    def write(self, fileName=None):
        # Write file
        if fileName is None:
            i = 1
            while os.path.isfile(self.midiFile[0:-4] + str(i) + ".mid"):
                i += 1
            fileName = self.midiFile[0:-4] + str(i) + ".mid"

        midi.write_midifile(fileName, self.midiPatternOut)
        print "Wrote %s" % fileName

    def window(self, windowStart, windowEnd, trackNum=0):
        assert(0 <= trackNum and trackNum < self.numTracks)
        primTrack = self.primTracks[trackNum]
        assert (2 <= windowStart and windowEnd < len(primTrack)-2)

        windowedTrack = list(primTrack)
        for i in range(windowStart, windowEnd+1):
            windowedTrack[i] = (None, None)
        return windowedTrack

    def getCorrupt(self, windowStart, windowEnd, trackNum=0):
        return self.rythmUnits[trackNum], self.window(windowStart, windowEnd, trackNum)

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
