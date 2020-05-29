from random import randint
from random import random

class Map:
	"""Represent nrMDP with a labelling function"""
	def __init__(self,path):
		file = open(path,'r')
		self.states = []
		self.initiales = []
		self.actions = []
		self.transitions = []
		self.observations = []
		self.labelling = []

		line = file.readline()
		obs_flag = False
		while line != "MRM DESCRIPTION\n":
			if line == "OBSERVATIONS\n":
				obs_flag = True
				line = file.readline()
			
			line = line.split()

			if line[0] == "initial":
				for i in line[1].split(','):
					if not i in self.initiales:
						self.initiales.append(i)

			else:
				if not line[0] in self.states:
					self.addState(line[0])
				index_from = self.states.index(line[0])
				
				if not line[1] in self.actions:
					self.addAction(line[1])
				index_a = self.actions.index(line[1])
				
				if not obs_flag:
					if not line[3] in self.states:
						self.addState(line[3])
					index_to = self.states.index(line[3])
					if '/' in line[2]:
						line[2] = float(line[2][:line[2].index('/')])/float(line[2][line[2].index('/')+1:])

					self.transitions[index_from][index_a].append((index_to,float(line[2])))
				else:
					if not line[2] in self.observations:
						self.observations.append(line[2])
					self.labelling[index_from][index_a] = line[2]

			line = file.readline()
		
		file.close()
		self.reset()

	def addState(self,name):
		self.states.append(name)
		self.transitions.append([])
		self.labelling.append([])
		for i in range(len(self.actions)):
			self.transitions[-1].append([])
			self.labelling[-1].append('null')

	def addAction(self,name):
		self.actions.append(name)
		for i in range(len(self.states)):
			self.transitions[i].append([])
			self.labelling[i].append('null')

	def reset(self):
		self.current = self.initiales[randint(0,len(self.initiales)-1)]

	def availableActions(self,state):
		"""return a list of actions available in the given state"""
		if type(state) == str:
			state = self.states.index(state)
		return [self.actions[x] for x in range(len(self.actions)) if len(self.transitions[state][x])!=0]

	def moveFrom(self,state,action):
		"""Given a state and an action return [s,o] with s the state reached an o the observation"""
		if type(state) == str:
			state = self.states.index(state)
		if type(action) == str:
			action = self.actions.index(action)
		
		if len(self.transitions[state][action]) == 0:
			print("ERROR: ACTION",self.actions[action],"NOT AVAILABLE IN STATE",self.states[state])
			return None

		i = 0
		s = self.transitions[state][action][0][1]
		r = random()
		while r > s:
			i += 1
			s += self.transitions[state][action][i][1]

		return [self.states[self.transitions[state][action][i][0]],self.labelling[state][action]]

	def move(self,action):
		"""Given a direction move the agent (change the current state) and return the observation"""
		res = self.moveFrom(self.current,action)
		self.current = res[0]
		return res[1]

	def getIdAction(self,action):
		return self.actions.index(action)

	def getIdState(self,state):
		return self.states.index(state)
		#return cell.row * self.width + cell.column

	def getStateFromId(self,i):
		return self.states[i]
		#r = (i//self.width)
		#c = i - (self.width*r)
		#return (r,c)