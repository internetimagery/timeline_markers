# Intuitively select keys

# Priority:
# 1) Individual keyframes selected in graph
# 2) Channels selected in graph
# 3) Channels selected in channelBox
# 4) All animated channels

import maya.cmds as cmds
import maya.mel as mel

def get_channelbox():
    """ Get any channels highlighted in the channelbox """
    channels = cmds.channelBox("mainChannelBox", sma=True, q=True)
    if channels:
        objs = cmds.channelBox("mainChannelBox", mol=True, q=True) or []
        for obj in objs:
            for channel in channels:
                try:
                    for key in cmds.keyframe(obj, at=channel, q=True, tc=True) or []:
                        yield key
                except Exception:
                    print "Some channels couldn't be found."

def get_graph():
    """ Get any channels highlighted in the graph editor """
    panel = "graphEditor1FromOutliner" #cmds.getPanel(scriptType="graphEditor")[0] + "FromOutliner"
    graph_sel = [sel.split(".") for sel in cmds.selectionConnection(panel, q=True, obj=True) or []]
    if graph_sel:
        full_selection = set(cmds.ls(sl=True) or []) # Cross reference with actual selection, as graph might not have updated recently
        selection = [sel for sel in graph_sel if sel[0] in full_selection and len(sel) is 2]
        if selection: # if we still have a selection after checking, continue
            for obj, channel in selection:
                for key in cmds.keyframe(obj, at=channel, q=True, tc=True) or []:
                    yield key

def get_keys():
    """ Get any highlighted keyframes """
    for key in cmds.keyframe(q=True, sl=True, tc=True) or []:
        yield key

def get_range():
    """ Get range. Either full timeline, or highlighted section. """
    slider = mel.eval("$tmpvar = $gPlayBackSlider")
    if cmds.timeControl(slider, rv=True, q=True):
        return cmds.timeControl(slider, q=True, ra=True)
    else:
        return cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)
