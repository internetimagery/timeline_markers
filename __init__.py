# Create markers on the timeline.

# TEXT FOR TRANSLATION BELOW::
LANGUAGE = {
    "english" : {
        "current" : "Add current time. (%s)",
        "current_desc" : "Click to add the current time as a marker.",
        "selected" : "Add selected keys.",
        "selected_desc" : "Click to add all keys highlighted in the timeline as markers.",
        "goto" : "Go to frame: %s",
        "save" : "Save markers.",
        "save_desc" : "Save the marker information to a file.",
        "load" : "Load markers.",
        "load_desc" : "Load some markers from a file.",
        "load_err" : "There was a problem loading your file."
    },
    # "english" : {
    #     "current" : "Add current time.",
    #     "current_desc" : "Click to add the current time as a marker.",
    #     "selected" : "Add selected keys.",
    #     "selected_desc" : "Click to add all keys highlighted in the timeline as markers.",
    #     "goto" : "Go to frame: "
    # },
}
DEFAULT_LANGUAGE = "english"

# DON'T TOUCH ANYTHING BELOW THIS LINE

import json
import os.path
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

class Main(object):
    """ Display markers """
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
        s.save_button = cmds.button(p=s.outer, c=s.save_markers)
        s.load_button = cmds.button(p=s.outer, c=s.load_markers)

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
        s.refresh()

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
        cmds.button(s.current_button, e=True, ann=s.language["current_desc"], l=s.language["current"] % frame)
        cmds.button(s.selected_button, e=True, ann=s.language["selected_desc"], l=s.language["selected"])
        cmds.button(s.save_button, e=True, ann=s.language["save_desc"], l=s.language["save"])
        cmds.button(s.load_button, e=True, ann=s.language["load_desc"], l=s.language["load"])

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
        slider = mel.eval("$tmp = $gPlayBackSlider")
        frame_range = (cmds.timeControl(slider, q=True, ra=True) or []) if cmds.timeControl(slider, q=True, rv=True) else (cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True))
        keys = set(cmds.keyframe(q=True, t=frame_range, tc=True) or [])
        for key in keys:
            s.add_marker(key)
        s.refresh()

    def add_marker(s, frame, label="Marker"):
        """ Add a marker """
        if frame not in s.markers:
            s.markers[frame] = label
            s.store.data["markers"] = s.markers
            s.store.save()
            print "Added marker at : %s" % frame

    def remove_marker(s, frame):
        """ Remove marker """
        if frame in s.markers:
            del s.markers[frame]
            s.store.data["markers"] = s.markers
            s.store.save()
            s.refresh()
            print "removing", frame

    def go_to_marker(s, frame):
        """ Switch time to the provided frame """
        cmds.currentTime(frame)
        print "Moving to : %s" % frame

    def load_markers(s, _):
        """ Load markers from a file """
        for path in cmds.fileDialog2(
            dir=cmds.workspace(q=True, rd=True),
            fileMode=1,
            fileFilter="Marker (*.txt)"
        ) or []:
            try:
                with open(path, "r") as f:
                    data = json.load(f)
            except ValueError:
                cmds.warning(s.language["load_err"])

            # Validate our data!
            try:
                for frame in data:
                    check_num = float(frame)
            except ValueError:
                cmds.warning(s.language["load_err"])

            s.markers = data
            s.refresh()


    def save_markers(s, _):
        """ Save markers to a file """
        if s.markers:
            for path in cmds.fileDialog2(
                dir=cmds.workspace(q=True, rd=True),
                fileMode=0,
                fileFilter="Marker (*.txt)"
            ) or []:
                with open(path, "w") as f:
                    json.dump(s.markers, f)

    def refresh(s):
        """ add entries to gui """
        for item in cmds.layout(s.inner, ca=True, q=True) or []:
            cmds.deleteUI(item)

        frames = sorted(s.markers.keys())
        icon_side = 30
        if frames:
            length = max(len(str(f)) for f in frames)
            colours = [
                (0.2, 0.2, 0.2),
                (0.25, 0.25, 0.25)
                ]

            def loop(colour, frame):
                frame_name = str(frame)
                label = s.markers[frame]
                cmds.rowLayout(nc=3, ad3=2, p=s.inner, bgc=colours[colour])
                # cmds.button(l="0" * (length - len(frame_name)) + frame_name, c=lambda _: s.go_to_marker(frame))
                cmds.iconTextButton(
                    ann=s.language["goto"] % frame_name,
                    st="iconAndTextHorizontal",
                    l="0" * (length - len(frame_name)) + frame_name,
                    i="traxFrameRange.png",
                    h=icon_side,
                    c=lambda: s.go_to_marker(frame)
                )
                cmds.textField(tx=label, cc=lambda tx: s.update_name(frame, tx))
                cmds.iconTextButton(
                    st="iconOnly",
                    i="removeRenderable.png",
                    h=icon_side,
                    w=icon_side,
                    c=lambda: s.remove_marker(frame)
                    )
            for i, frame in enumerate(frames):
                loop(i % 2, frame)
