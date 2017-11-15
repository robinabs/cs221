import cspUtil
import dataUtil

midiFile = "../../test/ode.mid"
windowStart, windowEnd = 10, 15
ode = dataUtil.MusicPattern(midiFile)
ode.getCorrupt(windowStart, windowEnd)

def reconstruct(corruptPrimTrack):
    csp_rythm = CSP()
        variables = []
            for r, unit in enumerate(prim_corrupt[1:]):  # Adding variables
                        if unit[1] == None:
                                        csp_rythm.add_variable(r,[(None,True),(None,False)])
                                                    variables.append(r)


                                                                                # Factors based on existing rythm combinations of two untis: Weight of bi-unit rythms depends on occurence
                                                                                    bi_unit = {} # Dictionnary accounting all the bi-unit rythms (either True-False, True-True, False-False or False-True)
                                                                                        for i in range(1,len(prim_corrupt)-1):
                                                                                                    if prim_corrupt[i][1] != None and prim_corrupt[i+1][1]!= None:
                                                                                                                    delta_rythm = (prim_corrupt[i][1], prim_corrupt[i+1][1])
                                                                                                                                if delta_rythm in bi_unit.keys():
                                                                                                                                                    bi_unit[delta_rythm] += 1
                                                                                                                                                                else:
                                                                                                                                                                                    bi_unit[delta_rythm] = 1
                                                                                                                                                                                        for r in variables[0:-1]: # Adding binary factor to csp
                                                                                                                                                                                                    csp_rythm.add_binary_factor(r, r+1, lambda x, y : bi_unit[x[1], y[1]] if (x[1], y[1]) in bi_unit else 0)
                                                                                                                                                                                                        for r in [variables[0]]:
                                                                                                                                                                                                                    csp_rythm.add_unary_factor(r, lambda x : bi_unit[prim_corrupt[r][1], x[1]] if (prim_corrupt[r][1], x[1]) in bi_unit else 0)
                                                                                                                                                                                                                        for r in [variables[-1]]:
                                                                                                                                                                                                                                    csp_rythm.add_unary_factor(r, lambda x : bi_unit[x[1], prim_corrupt[r+2][1]] if (x[1], prim_corrupt[r+2][1]) in bi_unit else 0)

                                                                                                                                                                                                                                        return csp_rythm


