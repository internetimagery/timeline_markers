# Create markers on the timeline.

LANGUAGE = {
    "english" : {
        "current" : "Add current time.",
        "selected" : "Add selected time."
    },
    "pirate" : {
        "current" : "Yarr",
        "selected" : "avast!"
    }
}
DEFAULT_LANGUAGE = "english"


import maya.mel as mel
import maya.cmds as cmds
try:
    import cPickle as pickle
except ImportError:
    import pickle

class Node(object):
    """ Store Data in Object """
    def __init__(s, name):
        s.name = name
        s._data = {}
    @property
    def data(s):
        try:
            s._data = pickle.loads(str(cmds.getAttr("%s.notes" % s.name)))
        except (ValueError, pickle.UnpicklingError):
            s._data = {}
        return s._data
    def check(s):
        if not cmds.objExists(s.name):
            sel = cmds.ls(sl=True)
            s.name = cmds.group(n=s.name, em=True)
            cmds.select(sel, r=True)
        if not cmds.attributeQuery("notes", n=s.name, ex=True):
            cmds.addAttr(s.name, ln="notes", sn="nts", dt="string", s=True)
    def save(s):
        s.check()
        cmds.setAttr("%s.notes" % s.name, l=False) # unlock attribute
        cmds.setAttr("%s.notes" % s.name, pickle.dumps(s._data, 0), type="string", l=True)

class MainWindow(object):
    """
    Display markers
    """
    def __init__(s):
        # Build window
        name = "TimelineMarkersMainWindow"
        s.store = Node("Timeline_Markers_Data")

        if cmds.window(name, ex=True):
            cmds.deleteUI(name)
        s.window = cmds.window(name, t="Timeline Markers", rtf=True)

        # Add language changer
        cmds.columnLayout(adj=True)
        s.language_box = cmds.optionMenu(cc=s.build_gui)
        for lang in LANGUAGE:
            cmds.menuItem(l=lang)
        s.outer = cmds.columnLayout(adj=True)
        s.inner = cmds.scrollLayout(cr=True)

        # Lets go!
        s.load_data()

        cmds.showWindow(s.window)

        cmds.scriptJob(e=["PostSceneRead", s.load_data], p=s.window)
        cmds.scriptJob(e=["NewSceneOpened", s.load_data], p=s.window)
        cmds.scriptJob(e=["timeChanged", s.update_current], p=s.window)

    def load_data(s):
        """ Load up any stored data """
        s.save_data = s.store.data
        language = s.save_data.get("lang", DEFAULT_LANGUAGE)
        s.build_gui(language if language in LANGUAGE else DEFAULT_LANGUAGE)

    def build_gui(s, language):
        """ build out buttons etc """
        s.save_data["lang"] = language
        s.language = LANGUAGE[language]
        s.store.save()

        cmds.optionMenu(s.language_box, e=True, v=language)
        for item in cmds.layout(s.outer, ca=True, q=True) or []:
            cmds.deleteUI(item)
        # Buttons
        s.current_button = cmds.button(p=s.outer, c=lambda _: s.add_current(cmds.currentTime(q=True)))
        s.update_current()

    def update_current(s):
        """ update button to read current frame """
        frame = cmds.currentTime(q=True)
        cmds.button(s.current_button, e=True, l="%s (%s)" % (s.language["current"], frame))

    def add_current(s, frame):
        """ Add current frame """
        print "adding ", frame


    def refresh(s):
        """ add entries to gui """


MainWindow()
