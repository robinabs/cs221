import midi
"""
# Instantiate a MIDI Pattern (contains a list of tracks)
pattern = midi.Pattern()
# Instantiate a MIDI Track (contains a list of MIDI events)
track = midi.Track()
# Append the track to the pattern
pattern.append(track)
# Instantiate a MIDI note on event, append it to the track
on = midi.NoteOnEvent(tick=0, velocity=20, pitch=midi.G_3)
track.append(on)
# Instantiate a MIDI note off event, append it to the track
off = midi.NoteOffEvent(tick=100, pitch=midi.G_3)
track.append(off)
# Add the end of track event, append it to the track
eot = midi.EndOfTrackEvent(tick=1)
track.append(eot)
# Print out the pattern
print pattern
# Save the pattern to disk
midi.write_midifile("example.mid", pattern)
"""

class BasicTrack():
    """
    This class represents a muscial track and provides
    method to convert it to a midi format
    """
    def Lisp_to_Midi(pattern_in, tracks_lisp):
        pattern_out = midi.containers.Pattern() # Create new pattern
        pattern_out.format = pattern_in.format # Copy format from original MIDI file
        pattern_out.resolution = pattern_in.resolution # Copy resolution from original MIDI file
        pattern_out.insert(2, pattern_in[0]) # Copy track[0] of Metadata from original MIDI file

        # Create as many tracks as original MIDI file in new pattern
        for i, track_in in enumerate(pattern_in):
            if i > 0:
                new_track = midi.containers.Track()
                pattern_out.insert(2, new_track)

        # Copy metadata from melodic tracks inside the melodic tracks of the new pattern
        End_index = []
        for i, track in enumerate(pattern_in):
            if i > 0:
                index_note = 0
                for j, event in enumerate(track):
                    if type(event) not in [midi.events.NoteOnEvent, midi.events.NoteOffEvent]:
                        pattern_out[i].append(event)
                    else:
                        index_note = j
                End_index.append(len(track) - index_note - 1) # keeps the meta of the tracks in the new pattern at the same place as the original MIDI file

        # Create new events inside each melodic track of new pattern from lisp
        for i, track in enumerate(tracks_lisp):
            end_index = End_index[i]
            indicator_silence = -1
            for j, note in enumerate(track):
                if note[0] == 'silence':
                    NoteOnEvent = midi.events.NoteOnEvent(tick=note[1], channel=i, data=[track[j+1][0], 80])
                    NoteOffEvent = midi.events.NoteOffEvent(tick=track[j+1][1], channel=i, data=[track[j+1][0], 0])
                    pattern_out[i+1].insert(-end_index,NoteOnEvent)
                    pattern_out[i+1].insert(-end_index,NoteOffEvent)
                    indicator_silence = j+1
                if (note[0] != 'silence') & (indicator_silence != j):
                    NoteOnEvent = midi.events.NoteOnEvent(tick=0, channel=i, data=[note[0], 80])
                    NoteOffEvent = midi.events.NoteOffEvent(tick=note[1], channel=i, data=[note[0], 0])
                    pattern_out[i+1].insert(-end_index,NoteOnEvent)
                    pattern_out[i+1].insert(-end_index,NoteOffEvent)

        return pattern_out

    def Midi_to_Lisp(self, pattern):
        tracks = []
        for i, track in enumerate(pattern): # Enumerate all the tracks
            if i > 0: # Don't take into account the first track of metadata
                liste_track = [] # Create an empty list for the output desired track in the right format
                for j, event in enumerate(track):
                    if type(event) == midi.events.NoteOnEvent:
                        if type(track[j+1]) == midi.events.NoteOffEvent: # Get (pitch, duration) for notes that are not silence
                            if event.tick == 0:
                                pitch = event.data[0]
                                duration = track[j+1].tick - event.tick
                                note = (pitch,duration)
                                liste_track.append(note)
                            else: # If there is a silence, then we need to extract both the silence and the following note
                                pitch = 'silence' # extract the silence and its duration
                                duration = event.tick
                                silence = (pitch, duration)
                                liste_track.append(silence)
                                pitch = track[j+1].data[0] # extract the following note
                                duration = track[j+1].tick
                                note = (pitch,duration)
                                liste_track.append(note)
                tracks.append(liste_track)
        return tracks

class BachChoraleTrack(BasicTrack):
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
        self.notes       = []

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
                self.notes += [tuple(note)]

    def __repr__(self):
        """
        Displays chorale metadata and notes
        """
        ret = "Bach Chorale %d (line %d in file %s)\n" % \
        (self.choraleId, 2*self.choraleNum + 1, self.choraleFile)
        ret += "pitch   dur\n"
        for note in self.notes:
            ret += "   %2d    %2d\n" % note
        return ret

if __name__ == '__main__':
    myChorale = BachChoraleTrack("../dat/bach-chorales/chorales.lisp", 2)
    print(myChorale)
