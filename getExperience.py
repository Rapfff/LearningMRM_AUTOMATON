import stormpy
import stormpy.core
import re
from pylstar.Letter import Letter
from pylstar.Word import Word

MODE_MAX = 1
MODE_MIN = 0
TMP_MODEL_PATH = "tmp.nm"

class GetExperience:
	"""Class for the getExperience function"""
	def __init__(self,model,observations,mode):
		self.model = model
		self.observations = observations
		self.mode = mode
		
		self.nr_actions = len(self.model.map.actions)
		self.initial_state = self.model.map.current

		if mode == MODE_MAX:
			self.states = [(-1,-1),(self.mappingState(self.initial_state),0)]
		if mode == MODE_MIN:
			self.states = [(self.mappingState(self.initial_state),0)]

		self.transitions = []
		self.target = []
		self.reset_transitions = [[]]
		if mode == MODE_MAX:
			self.reset_transitions.append([])

		self.initializeTransitions()

		self.execute()

	def mappingState(self,s):
		return self.model.map.getIdState(s)
	def inverseMappingState(self,s): # not used
		return self.model.map.getStateFromId(s)

	def mappingAction(self,a):
		return self.model.map.getIdAction(a)

	def inverseMappingAction(self,a):
		try:
			return self.model.map.actions[a]
		except IndexError:
			return a

	def initializeTransitions(self):
		for k in range(len(self.states)):
			self.transitions.append([])
			for i in range(self.nr_actions):
				self.transitions[-1].append([])
				for j in range(len(self.states)):
					self.transitions[-1][-1].append(0)

	def execute(self):
		to_add = [self.states[-1]]
		while len(to_add)>0:
			next_add = to_add.pop(0)
			to_add += self.createNewMdp(next_add[0],next_add[1])
		self.createPrismModel()

		program = stormpy.parse_prism_program(TMP_MODEL_PATH)
		if self.mode == MODE_MAX:
			prop = 'Pmax=? [F "target"]'
		if self.mode == MODE_MIN:
			prop = 'Rmin=? [F "target"]'
		properties = stormpy.parse_properties_for_prism_program(prop, program)
		options = stormpy.BuilderOptions(True,True) #To keep rewards and labels
		built_model = stormpy.build_sparse_model_with_options(program,options)
		
		#compute prop---------------------------------------------------------------
		result = stormpy.model_checking(built_model, properties[0], extract_scheduler=True)
		
		#extract scheduler----------------------------------------------------------
		scheduler = result.scheduler
		#print(scheduler)
		self.scheduler_nrmdp = []
		for i in range(len(self.model.map.states)):
			self.scheduler_nrmdp.append([])
			for j in range(len(self.observations)+1):
				self.scheduler_nrmdp[-1].append(-1)
		for state in built_model.states:
			if not "sink" in state.labels:
				state_lbl = self.getStateInNRMDP(state.labels)
				self.scheduler_nrmdp[state_lbl[0]][state_lbl[1]] = scheduler.get_choice(state).get_deterministic_choice()
		#printScheduler(self.scheduler_nrmdp)


	def createNewMdp(self,state_id,current_obs):
		"""Function which build the temporary MDP"""
		to_add = []
		state = self.inverseMappingState(state_id)
		
		for action in self.model.map.availableActions(state):
			action_id = self.mappingAction(action)
			seen_obs = self.model.map.labelling[state_id][action_id]
			
			for (next_state,proba) in self.model.map.transitions[state_id][action_id]:
			
				if seen_obs == "null": #we observe nothing
					new_state = (next_state,current_obs)
					if self.addNewTransition(new_state,(state_id,current_obs),action_id,proba):
						to_add.append(new_state)
					
				elif Letter(seen_obs) == self.observations.letters[current_obs]: #we observe what we want
					current_obs += 1
					new_state = (next_state,current_obs)
					if self.addNewTransition(new_state,(state_id,current_obs-1),action_id,proba):
						if len(self.observations) == current_obs: #we have done
							self.target.append(self.states.index(new_state))
						else: #continue in every direction
							to_add.append(new_state)
					
					current_obs -= 1

				else: #we observe something we don't want
					self.transitions[self.states.index((state_id,current_obs))][action_id][0] = 1.0
					self.reset_transitions[self.states.index((state_id,current_obs))].append(action_id)

		return to_add


	def addNewTransition(self,new_state,tr_from,tr_action,tr_prob):
		"""add a new transition in the temporary model (G in the notes)"""
		if not new_state in self.states:
			self.createNewState(new_state)
					
		i = self.states.index(new_state)
		tr_from = self.states.index(tr_from)
		if self.transitions[tr_from][tr_action][i] == tr_prob: #We are looping
			return False
		self.transitions[tr_from][tr_action][i] = tr_prob
		return True
	
	def createNewState(self,new_state):
		"""Create a new state in the temporary model (G in the notes)"""
		self.states.append(new_state)
		self.transitions.append([])
		#create new row in self.transitions for the new state
		for i in range(self.nr_actions):
			self.transitions[-1].append([])
			for j in range(len(self.states)):
				self.transitions[-1][-1].append(0)
		#add new cell in self.transitions old rows (for old self.states)
		for i in range(len(self.states)-1):
			for j in range(self.nr_actions):
				self.transitions[i][j].append(0)
		
		self.reset_transitions.append([])

	def createPrismModel(self):
		"""Create a prism file describing the temporary model (G in the notes)"""
		out_file = open(TMP_MODEL_PATH,'w')
		#module
		out_file.write("mdp\n\nmodule tmp\n\n")
		
		#number of state and initial state
		out_file.write("\ts : [0.."+str(len(self.states))+"] init "+str(abs(self.mode))+";\n\n")

		
		#transitions
		for state in range(len(self.transitions)):
			for action in range(len(self.transitions[state])):
				if sum(self.transitions[state][action]) != 0:
					out_file.write("\t["+chr(97+action)+"] s="+str(state)+"-> ")
					destinations = []
					for dest in range(len(self.transitions[state][action])):
						if self.transitions[state][action][dest] != 0:
							destinations.append(str(self.transitions[state][action][dest])+":(s'="+str(dest)+")")
					out_file.write(" + ".join(destinations))
					out_file.write(";\n")
		out_file.write("\nendmodule\n\n")
		
		#label target
		out_file.write('label "target" = ')
		self.target = list(set(self.target))
		self.target = [ "(s="+str(x)+")" for x in self.target]
		if len(self.target) == 0:
			out_file.write("(s="+str(len(self.states)+1)+");\n")
		else:
			out_file.write(" | ".join(self.target))
			out_file.write(";\n")
		
		#label self.states
		if self.mode == MODE_MAX:
			out_file.write('label "sink" = (s=0);\n')
		
		for i in range(self.mode,len(self.states)):
			out_file.write('label "s'+str(self.states[i][0])+'_obs'+str(self.states[i][1])+'" = (s='+str(i)+');\n')

		if self.mode == MODE_MIN:
			out_file.write("\nrewards\n")
			if self.model.mrm.reset_cost == 1:
				out_file.write("\ttrue:1;\n")
			else:
				for i in range(len(self.states)):
					for j in range(self.nr_actions):
						if j in self.reset_transitions[i]:
							out_file.write("\t["+chr(97+j)+"] (s="+str(i)+") : "+str(-1*self.model.mrm.reset_cost)+";\n")
						else:
							out_file.write("\t["+chr(97+j)+"] (s="+str(i)+") : 1;\n")
		
			out_file.write("endrewards\n")
		
		out_file.close()

	def getActionScheduler(self,state,index_wanted_obs):
		#print("In",state,end=" ")
		state = self.mappingState(state)
		#print("Execute",inverseMappingAction(sch[state][index_wanted_obs]))
		return self.inverseMappingAction(self.scheduler_nrmdp[state][index_wanted_obs])

	def getStateInNRMDP(self,lbls):
		"""Given the labels of a state in G, return the corresponding state and observation in M"""
		pattern = re.compile("s[0-9]+_obs[0-9]+")
		for i in lbls:
			if pattern.match(i):
				return [int(i[1:i.index('_')]),int(i[i.index('obs')+3:])]