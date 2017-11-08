def Midi_to_Lisp(pattern):
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
