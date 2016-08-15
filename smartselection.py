import maya.cmds as cmds
import maya.mel as mel

# Created by Jason Dixon 14/03/14
# http://internetimagery.com

# Known "bug" : If you select only keys on a locked attribute, script will move to the next selection.

# smartSelection().get()  -- Grab the selection

# smartSelection().loop( function ) -- run your own function and let the script do the looping for you

# smartSelection( True ) -- Adding true will select all the keys on selected curves.

# smartSelection( False, [ time, time ] ) -- Adding a time frame will look only in this specified time.

class smartSelection(object):
	def __init__(self, full = False, time = []): # Full curves even if a range is specified.
		self.selection = {} #selection format { object : { attribute : [ key, key, etc... ] } }
		self.range = time
		self.full = full

		if not self.range:
			slider = mel.eval('$tempvar = $gPlayBackSlider')
			if cmds.timeControl( slider, rangeVisible = True, query=True ):
				self.range = cmds.timeControl ( slider, query = True, rangeArray = True )

		selection = self._getKeySelection()
		if not selection:
			selection = self._getGraphSelection()
			if not selection:
				selection = self._getChannelSelection()
				if selection is False:
					selection = self._getAllSelection()
					if not selection:
						selection = False
		if selection:
			self.selection = selection
		else:
			print 'No Selection Made.'

	def _getAllSelection(self):
		objects = cmds.ls( selection = True )
		selection = {}
		if objects:
			for obj in objects:
				attribute = cmds.listConnections( obj , source=True, type='animCurve')
				attrlist = {}
				if attribute:
					for attr in attribute:
						attr = attr.rpartition('_')[2]
						keys = cmds.keyframe( obj, at=attr, query=True )
						if self.range and not self.full:
							keys = self._inrange( keys, self.range )
						if keys:
							attrlist[attr] = keys
				if attrlist:
					selection[obj] = attrlist
			if selection:
				return selection
		return False
	def _getChannelSelection(self):
		objects = cmds.channelBox( 'mainChannelBox' , mol = True, query = True )
		channels = cmds.channelBox( 'mainChannelBox' , sma = True, query = True )
		selection = {}
		if channels:
			for obj in objects:
				attrlist = {}
				for attribute in channels:
					try:
						attr = cmds.listConnections(obj+'.'+attribute,type='animCurve').rpartition('_')[2]
						keys = cmds.keyframe( obj, at=attr, query=True )
						if self.range and not self.full:
							keys = self._inrange( keys, self.range )
						if keys:
							attrlist[attr] = keys
					except:
						print 'Selected channels not on all objects / or missing animation.'
				if attrlist:
					selection[obj] = attrlist
			return selection
		return False
	def _getKeySelection(self):
		selection = {}
		objects = cmds.ls( selection = True )
		if objects:
			for obj in objects:
				curves = cmds.keyframe( obj, query = True, name = True, selected = True )
				if curves:
					attribute = {}
					for curve in curves:
						attr = curve.rpartition('_')[2]
						if self.full:
							keys = cmds.keyframe( obj, at=attr, query = True )
						else:
							keys = cmds.keyframe( obj, at=attr, query = True, selected = True )
							if self.range:
								keys = self._inrange( keys, self.range )
						if keys:
							attribute[attr] = keys
					if attribute:
						selection[obj] = attribute
			if selection:
				return selection
		return False
	def _getGraphSelection(self):
		graphselect = cmds.selectionConnection( (cmds.getPanel( scriptType='graphEditor' )[0]+'FromOutliner'), query = True , obj = True)
		selection = {}
		if graphselect:
			if graphselect[0].rpartition('.')[0]:
				for l in graphselect:
					(obj, dot, attr) = l.rpartition('.')
					if self.range and not self.full:
						keys = self._inrange( keys, self.range )
					else:
						keys = cmds.keyframe( obj, at=attr, query = True)
					if keys:
						selection[obj] = selection.get(obj, {})
						selection[obj][attr] = selection[obj].get(attr, keys)
			else:
				for obj in graphselect:
					attribute = cmds.keyframe(obj, q=True, name=True)
					for attr in attribute:
						attr = attr.rpartition('_')[2]
						if self.range and not self.full:
							keys = self._inrange( keys, self.range )
						else:
							keys = cmds.keyframe( obj, at=attr, query = True)
						if keys:
							selection[obj] = selection.get(obj, {})
							selection[attr] = selection.get(attr, [])
			if selection:
				return selection
		return False
	def _inrange(self, keylist, range ):
		new = []
		if keylist:
			for key in keylist:
				if range[0] <= key <= range[1]:
					new.append( key )
		return new
	#call functions for each key set: function(obj, attr, keys)
	def loop(self, methods):
		if self.selection and methods:
			for obj in self.selection:
				for attr in self.selection[obj]:
					for method in methods:
						method(obj, attr, self.selection[obj][attr])
	def get(self):
		return self.selection
	def add(self, selection):
		print 'add to existing selection'
