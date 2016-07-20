# Create markers on the timeline.

# TEXT FOR TRANSLATION BELOW::
LANGUAGE = {
    "english" : {
        "current" : "Add current time.",
        "current_desc" : "Click to add the current time as a marker.",
        "selected" : "Add selected keys.",
        "selected_desc" : "Click to add all keys highlighted in the timeline as markers."

    },
    # "english" : {
    #     "current" : "Add current time.",
    #     "current_desc" : "Click to add the current time as a marker.",
    #     "selected" : "Add selected keys.",
    #     "selected_desc" : "Click to add all keys highlighted in the timeline as markers."
    #
    # },
}
DEFAULT_LANGUAGE = "english"

# DON'T TOUCH ANYTHING BELOW THIS LINE

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
        s.inner = cmds.scrollLayout(cr=True, h=600)

        # Buttons!
        s.current_button = cmds.button(p=s.outer, c=s.add_current)
        s.selected_button = cmds.button(p=s.outer, c=s.add_selected)


        # Lets go!
        s.load_data()
        s.refresh()

        cmds.showWindow(s.window)

        cmds.scriptJob(e=["PostSceneRead", s.load_data], p=s.window)
        cmds.scriptJob(e=["NewSceneOpened", s.load_data], p=s.window)
        cmds.scriptJob(e=["timeChanged", s.update_current], p=s.window)

    def load_data(s):
        """ Load up any stored data """
        s.save_data = s.store.data
        language = s.save_data.get("lang", DEFAULT_LANGUAGE)
        s.markers = s.save_data.get("markers", {})
        s.build_gui(language if language in LANGUAGE else DEFAULT_LANGUAGE)

    def build_gui(s, language):
        """ build out buttons etc """
        s.save_data["lang"] = language
        s.language = LANGUAGE[language]
        s.store.save()
        cmds.optionMenu(s.language_box, e=True, v=language)

        s.update_current()

    def update_current(s):
        """ update button to read current frame """
        frame = cmds.currentTime(q=True)
        cmds.button(s.current_button, e=True, ann=s.language["current_desc"], l="%s (%s)" % (s.language["current"], frame))
        cmds.button(s.selected_button, e=True, ann=s.language["selected_desc"], l=s.language["selected"])

    def update_name(s, frame, text):
        """ update the name of text box """
        if frame in s.markers:
            s.markers[frame] = text
            s.store.data["markers"] = s.markers
            s.store.save()
            print "Updated marker %s label : %s" % (frame, text)

    def add_current(s, _):
        """ Add current frame """
        s.add_marker(cmds.currentTime(q=True))
        s.refresh()

    def add_selected(s, _):
        """ Add selected keys """
        print "adding selected"

    def add_marker(s, frame, label="Marker"):
        """ Add a marker """
        if frame not in s.markers:
            s.markers[frame] = label
            s.store.data["markers"] = s.markers
            s.store.save()
            print "Added marker at : %s" % frame

    def remove_marker(s, frame):
        """ Remove marker """
        print "removing", frame

    def refresh(s):
        """ add entries to gui """
        for item in cmds.layout(s.inner, ca=True, q=True) or []:
            cmds.deleteUI(item)

        frames = sorted(s.markers.keys())
        length = max(len(str(f)) for f in frames)

        def loop(frame):
            frame_name = str(frame)
            label = s.markers[frame]
            cmds.rowLayout(nc=3, ad3=2, p=s.inner)
            cmds.button(l="0" * (length - len(frame_name)) + frame_name)
            cmds.textField(tx=label, cc=lambda tx: s.update_name(frame, tx))
            cmds.iconTextButton(
                st="iconOnly",
                i="removeRenderable.png",
                ann="Remove this object from the export selection.",
                h=30,
                w=30,
                c=lambda: s.remove_marker(frame))
        for frame in frames:
            loop(frame)

def Main():
    MainWindow()
