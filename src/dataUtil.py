import midi
import os.path

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
        self.numTracks   = len(self.midiPattern)-1
        self.lispTracks  = []

        for midiTrackId, midiTrack in enumerate(self.midiPattern):
            if midiTrackId == 0: continue

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
                        notes += [(pitch,duration)]

                    # Add generated notes to track
                    lispTrack += notes
            self.lispTracks.append(lispTrack)

    def write(self, lispTracks=None):
        # copy pattern metadata
        midiPattern            = midi.containers.Pattern()
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
        for midiTrackId, midiTrack in enumerate(self.midiPattern):
            if midiTrackId == 0: continue
            for eventNum, event in enumerate(midiTrack):
                if type(event) not in [midi.events.NoteOnEvent, midi.events.NoteOffEvent]:
                    midiPattern[midiTrackId].append(event)
                elif type(midiTrack[eventNum-1]) not in \
                [midi.events.NoteOnEvent, midi.events.NoteOffEvent]:
                    midiPattern[midiTrackId].extend(midiTracks[midiTrackId-1])

        print(midiPattern)
        print(self.midiPattern)
        # Write file
        i = 1
        while os.path.isfile(self.midiFile[0:-4] + str(i) + ".mid"):
            i += 1
        fileName = self.midiFile[0:-4] + str(i) + ".mid"
        midi.write_midifile(fileName, midiPattern)
        print "Wrote %s" % fileName


class LispBachChorale(MusicPattern):
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
        self.lispTrack   = []

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
                    note += [val]

                    featurePosition = line.find(self.features[(i+1) % N], valueEndPosition)
                    valueEndPosition = line.find(')', featurePosition)
                self.lispTrack += [tuple(note)]

    def __repr__(self):
        """
        Displays chorale metadata and notes
        """
        ret = "Bach Chorale %d (line %d in file %s)\n" % \
        (self.choraleId, 2*self.choraleNum + 1, self.choraleFile)
        ret += "pitch   dur\n"
        for note in self.lispTrack:
            ret += "   %2d    %2d\n" % note
        return ret


if __name__ == '__main__':
    myOde = MusicPattern("../../test/ode.mid")
    myOde.lispTracks[0][0] = (77, 960)
    myOde.write()
