class MRM:

	def __init__(self,path,reset_cost,default_reward):
		self.default_reward = default_reward
		self.reset_cost = reset_cost

		self.current = 0
		self.transitions = []
		self.observations = []

		file = open(path)
		
		line = file.readline()
		while line != "MRM DESCRIPTION\n":
			line = file.readline()
		line = file.readline()
		
		while line:
			line = line.split()
			while int(line[0]) >= len(self.transitions):
				self.transitions.append([])
			
			self.transitions[int(line[0])].append([line[1],int(line[2]),int(line[3])])
			
			if line[1] not in self.observations:
				self.observations.append(line[1])
			line = file.readline()
		
		file.close()

	def move(self,observation):
		if self.current >= len(self.transitions):
			return self.default_reward
		for t in self.transitions[self.current]:
			if t[0] == observation:
				self.current = t[2]
				return t[1]
		return self.default_reward

	def reset(self):
		self.current = 0
		return self.reset_cost
