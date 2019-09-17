import os, inspect, importlib, sys, types
from __main__ import Workbench
import FreeCAD, FreeCADGui

class ModuleWorkbenchCommand:
	def __init__(self, commandId):
		self.commandId=commandId
		self.ToolTip=""
		self.Pixmap="freecad"

	def Activated(self):
		self.callback()

	def IsActive(self):
		return True

	def GetResources(self):
		return {
			'Pixmap': self.Pixmap,
			'MenuText': self.MenuText,
			'ToolTip': self.ToolTip
		}

	def addToFreeCAD(self):
		FreeCADGui.addCommand(self.commandId,self)

class ModuleWorkbench:
	def __init__(self, module):
		if not inspect.ismodule(module):
			raise Exception("The workbench is not a module")

		self.module=module
		self.commands={}
		self.createReloadCommand()
		self.createWorkbench()

	def getModuleIcon(self):
		if "__icon__" in self.module.__dict__:
			return (os.path.dirname(self.module.__file__)
				+os.sep+self.module.__icon__)

		return "freecad"

	def createReloadCommand(self):
		self.reloadCommand=ModuleWorkbenchCommand(self.module.__name__+"___reload")
		self.reloadCommand.callback=self.reload
		self.reloadCommand.MenuText="&Reload module"
		self.reloadCommand.Pixmap=self.getModuleIcon()
		self.reloadCommand.addToFreeCAD()

	def assignCommands(self):
		for funcName in self.getModuleFuncNames():
			if funcName not in self.commands:
				cmd=ModuleWorkbenchCommand(self.module.__name__+"_"+funcName)
				cmd.MenuText="&"+funcName
				if self.module.__dict__[funcName].__doc__:
					cmd.ToolTip=self.module.__dict__[funcName].__doc__

				if "icon" in self.module.__dict__[funcName].__dict__:
					cmd.Pixmap=(os.path.dirname(self.module.__file__)
						+os.sep+self.module.__dict__[funcName].icon)

				cmd.addToFreeCAD()
				self.commands[funcName]=cmd

			cmd=self.commands[funcName]
			cmd.callback=self.module.__dict__[funcName]

	def getModuleFuncNames(self):
		res=[]

		for funcName in self.module.__dict__:
			if (type(self.module.__dict__[funcName])==types.FunctionType
					and funcName[0]!="_"
					and self.module.__dict__[funcName].__module__==self.module.__name__):
				res.append(funcName)

		return res

	def Initialize(self):
		self.assignCommands()

		commandIds=[]
		for funcName in self.getModuleFuncNames():
			commandIds.append(self.commands[funcName].commandId)

		self.instance.appendToolbar(self.module.__name__,commandIds)
		self.instance.appendMenu("&"+self.module.__name__,commandIds+["Separator",self.reloadCommand.commandId])

	def createWorkbench(self):
		self.cls=type(self.module.__name__+"Workbench",(Workbench,),{
			"Initialize": self.Initialize
		})
		self.instance=self.cls()
		self.instance.MenuText=self.module.__name__
		self.instance.ToolTip="testing..."
		self.instance.Icon=self.getModuleIcon()

		FreeCADGui.addWorkbench(self.instance)

	def reload(self):
		for funcName in self.getModuleFuncNames():
			del self.module.__dict__[funcName]

		self.module=importlib.reload(self.module)
		self.instance.removeToolbar(self.module.__name__)
		self.instance.removeMenu("&"+self.module.__name__)
		self.Initialize()

		FreeCADGui.activateWorkbench("StartWorkbench")
		FreeCADGui.activateWorkbench(self.module.__name__+"Workbench")

def createModuleWorkbench(module):
	ModuleWorkbench(module)

def icon(icon):
	def wrap(func):
		func.icon=icon
		return func
	return wrap
