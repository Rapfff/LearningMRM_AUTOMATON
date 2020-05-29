from Model import Model
import stormpy
import stormpy.core
from pylstar.ObservationTable import ObservationTable
from pylstar.Letter import Letter
from pylstar.OutputQuery import OutputQuery
from pylstar.Word import Word
from pylstar.KnowledgeBase import KnowledgeBase
from getExperience import GetExperience
from getExperience import MODE_MIN
from getExperience import MODE_MAX
from getExperience import TMP_MODEL_PATH
from GUI import GUI
import time
import random
from os import remove
import sys, getopt
import re

MODE = MODE_MAX
STEPS_PER_EPISODE = 1000
ACTIONTOEXECUTE = 5*STEPS_PER_EPISODE

class MRMActiveKnowledgeBase(KnowledgeBase):
	"""
	The class that implements the main mecanism of an active Mealy EnvironReward Machine knowledge base.
	"""
	def __init__(self,world):
		self.world = world
		super(MRMActiveKnowledgeBase, self).__init__()
		self.nuof_MQs = 0
		self.actionsForLearning = 0

	# LEARNING BY PLANNING
	def _execute_word(self, word):
		# Executes the specified word.
		if word is None:
			raise Exception("Word cannot be None")
		self._logger.debug("Execute word '{}'".format(word))
		#print("Execute word '{}'".format(word))

		reward_trace = []
		self.nuof_MQs += 1

		self.world.mrm.reset()
		self.world.map.reset()

		ge = GetExperience(self.world,word,MODE) #Create the scheduler

		i = 0
		while i < len(word):
			letter = word.letters[i]
			a = ge.getActionScheduler(self.world.map.current,i) #ask for the next action to execute
			(obs,rew) = self.world.moveAPF(a) #get observation and reward
			reset = False
			while Letter(obs) != letter:
				if obs == "null": #if we observe nothing execute a new action
					self.actionsForLearning += 1
					a = ge.getActionScheduler(self.world.map.current,i)
					(obs,rew) = self.world.moveAPF(a)
				else:             #if we observe something we don't want, reset
					reset = True
					break
			
			if reset:
				self.world.reset()
				i = 0
				reward_trace = []
			else:                 #if we observe what we want
				i += 1
				reward_trace.append(rew)
		w = Word([Letter(r) for r in reward_trace])
		return w



class LearningMRM:
	"""Main class of the framework"""
	def __init__(self,path,reset_cost,default_reward,value_expert):
		self.world = Model(path,reset_cost,default_reward)
		self.value_expert = value_expert
		
		in_letters = [Letter(symbol) for symbol in self.world.mrm.observations]
		self.kbase = MRMActiveKnowledgeBase(self.world)
		self.OT = ObservationTable(input_letters=in_letters, knowledge_base=self.kbase)

		print('Initializing OT')
		self.OT.initialize()
		print('OT initialized')

		#COUNTERS
		self.total_learning_time = 0
		self.total_exploring_time = 0
		self.rewards = 0
		self.iteration4Explor = 0
		self.iteration4OT = 0
		self.nuof_counter_examples = 0

		#EXECUTION
		self.learn()
		while not self.check():
			self.learn()

		#END PRINT
		self.endPrints()
		remove(TMP_MODEL_PATH)


	def learn(self):
		"""Use L*_M algorithm to learn the MRM"""
		StartTime = time.time()
		iteration4OT = 0
		closed = self.OT.is_closed()
		inconsistency = self.OT.find_inconsistency()
		
		while not closed or inconsistency is not None:
			iteration4OT += 1
			print('Building the OT;', 'iteration', iteration4OT)
			
			if not closed:
				self.OT.close_table()

			if inconsistency is not None:
				self.OT.make_consistent(inconsistency)
	 	
			closed = self.OT.is_closed()
			inconsistency = self.OT.find_inconsistency()

		EndTime = time.time()
		self.total_learning_time += EndTime - StartTime

	def check(self):
		"""Check if the hypothesis is correct"""
		StartTime = time.time()
		self.createHypothesis()

		if not self.passedFirstCheck(): # Expert value check
			res = False
		elif not self.passedSecondCheck(): # Exploitation check
			res = False
		else:
			res = True

		EndTime = time.time()
		self.total_exploring_time += EndTime - StartTime
		return res
	
	def endPrints(self):
		print()
		print('Optimization problem:',["MIN","MAX"][MODE])
		print('# learning actions:', self.kbase.actionsForLearning)
		print()
		print('rewards:', self.rewards)
		print('nuof_MQs:', self.kbase.nuof_MQs)
		print('Exploration iterations:', self.iteration4Explor)
		print('nuof_counter_examples:', self.nuof_counter_examples)
		print('total_learning_time:', self.total_learning_time)
		print('total_exploring_time:',self.total_exploring_time)


	def createHypothesis(self):
		print()
		print('Building hypothesis MRM...')
		RM = self.OT.build_hypothesis()
		print('Hypothesis MRM built !')
		self.buildProductAutomaton(RM) # Write the prism file with the hypothesis 
		
		program = stormpy.parse_prism_program(TMP_MODEL_PATH)
		properties = stormpy.parse_properties_for_prism_program("Rmax=? [ LRA ]", program)
		options = stormpy.BuilderOptions(True,True) #To keep rewards and labels
		self.h = stormpy.build_sparse_model_with_options(program,options)
		self.result_h = stormpy.model_checking(self.h, properties[0],extract_scheduler = True).at(0)
		self.scheduler = stormpy.model_checking(self.h, properties[0],extract_scheduler = True).scheduler

	def passedFirstCheck(self):
		# Expert value check
		if self.result_h < self.value_expert:
			print(self.result_h," < Value_expert:",self.value_expert,", looking for counter-example...")
			self.findCounterExample()
			return False
		else:
			print(self.result_h," >= Value_expert:",self.value_expert)
			return True

	def passedSecondCheck(self):
		# Exploitation check. Check if the hypothesis is correct by executing the strategy
		# After STERPS_PER_EPISODE we reset the system
		# We end if we observe a counter example or if we have already performed ACTIONTOTEXECUTE actions
		actionsExecuted = 0
		while actionsExecuted < ACTIONTOEXECUTE :
			self.iteration4Explor += 1
			print()
			print('Exploration iteration', self.iteration4Explor)

			# Initialize agent's state to a rand position and
			current_state_h = self.resetExploration()
			
			for step in range(STEPS_PER_EPISODE):
				a = self.scheduler.get_choice(current_state_h)
				if self.isResetAction(a):
					next_state_h = self.resetExploration()
					obs = "null"
					r_h = self.world.mrm.reset_cost
					r_m = self.world.mrm.reset_cost
					next_state_m = self.world.map.current

				else:
					(r_h,r_m,next_state_h,next_state_m,obs) = self.executeOneStepExploration(current_state_h,a.get_deterministic_choice())
			
				self.updateTraces(obs,r_m)

				actionsExecuted += 1
				if self.isCounterExample(r_h,r_m):
					self.nuof_counter_examples += 1
					return False
				else:
					current_state_h = next_state_h
					self.world.map.current = next_state_m
		return True

	def getStateInHypothesis(self,states_h,state):
		for i in states_h:
			if int(i.name) == int(state):
				return i

	def buildProductAutomaton(self,h):
		"""Given a hypothesis of the angluin algo, build the product between the gird and this hypothesis and write it in a PRISM file.
		The init state is {'c1','r1','null'} with no obs already made"""
		
		rewards = "rewards\n"
		labels = ''
		out_file = open(TMP_MODEL_PATH,'w')
		#module
		out_file.write("mdp\n\nmodule tmp\n\n")
		
		#number of state and initial state
		new_states = []
		for s in self.world.map.states:
			for o in range(len(h.get_states())):
				labels += 'label "'+s+'_'+str(o)+'" = s='+str(len(new_states))+' ;\n'
				new_states.append((s,o))

		out_file.write("\ts : [0.."+str(len(new_states)-1)+"] init "+str(new_states.index((self.world.map.initiales[0],0)))+";\n\n")

		#transitions
		for s in new_states:
			state_id = self.world.map.getIdState(s[0])
			for a  in self.world.map.availableActions(s[0]):
				action_id = self.world.map.getIdAction(a)
				obs = self.world.map.labelling[state_id][action_id]

				#if len(self.world.map.transitions[state_id][action_id]) > 0:
				out_file.write("\t["+a+"] s="+str(new_states.index(s))+"-> ")
				temp_list = []
				
				if obs == 'null':
					rewards += "\t["+a+"] (s="+str(new_states.index(s))+") : "+str(self.world.mrm.default_reward)+";\n"
					for [dest,prob] in self.world.map.transitions[state_id][action_id]:
						index_dest = str(new_states.index((self.world.map.getStateFromId(dest),s[1])))
						temp_list.append(str(prob)+" : (s'="+index_dest+")")
				else:
					tr_val = h.play_word(Word([Letter(obs)]),self.getStateInHypothesis(h.get_states(),s[1]))
					state_in_h = int(tr_val[1][-1].name)
					rewards += "\t["+a+"] (s="+str(new_states.index(s))+") : "+str(tr_val[0].last_letter().name)+";\n"
					for [dest,prob] in self.world.map.transitions[state_id][action_id]:
						index_dest = str(new_states.index((self.world.map.getStateFromId(dest),state_in_h)))
						temp_list.append(str(prob)+" : (s'="+index_dest+")")

				out_file.write(" + ".join(temp_list))
				out_file.write(";\n")

			a = "reset"
			out_file.write("\t["+a+"] s="+str(new_states.index(s))+"-> 1.0 : (s'="+str(new_states.index((self.world.map.initiales[0],0)))+");\n")
			rewards += "\t["+a+"] (s="+str(new_states.index(s))+") : "+str(self.world.mrm.reset_cost)+";\n"

		out_file.write("\nendmodule\n\n")
		out_file.write(labels)

		rewards +="endrewards\n"
		out_file.write(rewards)
		out_file.close()

	def resetH(self):
		for s in range(len(self.h.states)):
			if {str(self.world.map.current)+'_0'}.issubset(self.h.states[s].labels):
				return s

	def getNextSateH(self,state,action):
		action = state.actions[action]
		r = random.random()
		c = 0
		for transition in action.transitions:
			c += transition.value()
			if r < c:
				break
		return transition.column

	def getRewardH(self,state,action):
		c = 0
		for i in range(state): # i: id in h => state in h => state in m
			c += len(self.h.states[i].actions)
		return self.h.reward_models[''].state_action_rewards[c+int(action.__str__())]# +1 because we have the reset action

	def fromIdStateHToIdStateM(self,sh):
		pattern = re.compile("s[0-9]+_[0-9]+")
		for i in self.h.states[sh].labels:
			if pattern.match(i):
				return i[:i.index('_')]

	def executeOneStepExploration(self,current_state_h,action):
		next_state_h = self.getNextSateH(self.h.states[current_state_h],action)
		r_h = self.getRewardH(current_state_h,action)
		obs = self.world.map.labelling[self.world.map.getIdState(self.world.map.current)][int(action.__str__())]
		next_state_m = self.fromIdStateHToIdStateM(next_state_h)
		#[next_state_m,obs] = self.world.map.moveFrom(self.world.map.current,self.world.map.actions[int(action.__str__())])
		r_m = None
		if obs == 'null':
			r_m = self.world.mrm.default_reward
		else:
			r_m = self.world.mrm.move(obs)

		return (r_h,r_m,next_state_h,next_state_m,obs)

	def isCounterExample(self,r_h,r_m):
		"""Return True if the two rewards r_h and r_m are different and add the counter example at the OT."""
		if r_m != r_h:
			print("CE", r_m, r_h, self.observation_seq)
			input_word  = Word([Letter(symbol) for symbol in self.observation_seq])
			output_word = Word([Letter(symbol) for symbol in self.reward_trace])
			self.OT.add_counterexample(input_word, output_word)
			return True
		return False


	def findCounterExample(self):
		"""Execute actions uniformly at random until we get a counter example"""
		while True:
			current_state_h = self.resetExploration()

			for ep in range(STEPS_PER_EPISODE):
				a = int(random.random()//(1/(len(self.world.map.availableActions(self.world.map.current)))))
				(r_h,r_m,next_state_h,next_state_m,obs) = self.executeOneStepExploration(current_state_h,a)

				if obs != 'null':
					self.observation_seq.append(obs)
					self.reward_trace.append(r_m)

				if self.isCounterExample(r_h,r_m):
					self.nuof_counter_examples += 1
					return None
				else:
					current_state_h = next_state_h
					self.world.map.current = next_state_m	

	def isResetAction(self,a):
		return int(a.__str__()) == len(self.world.map.actions)

	def resetExploration(self):
		self.observation_seq = []
		self.reward_trace = []

		self.world.map.reset()
		self.world.mrm.reset()
		return self.resetH()

	def updateTraces(self,obs,r_m):
		if obs != 'null':
			self.observation_seq.append(obs)
			self.reward_trace.append(r_m)
		self.rewards += r_m

if __name__ == "__main__":
	help_txt = "usage: Learning_MRMs.py -i <input_file> -v <expert_value>\n\t\t\t[-r <reset_cost>]\n\t\t\t[-d <default_cost>]\n\t\t\t[--steps_episode <integer>]\n\t\t\t[--number_episodes <integer>]\n\t\t\t[--getExperience_mode <max|min>]\n\nexample : 'Learning_MRMs -i examples/example.mp -r 5 -d 1 -v 10'"
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hi:r:d:v:a:",["help",
																"input_file=",
																"reset_cost=",
																"default_cost=",
																"expert_value=",
																"steps_episode=",
																"number_episodes=",
																"getExperience_mode="])
	except getopt.GetoptError:
		print(help_txt)
		sys.exit(2)

	r = None
	v = None
	d = None
	p = None
	nb = None

	for opt, arg in opts:
		
		if opt in ('-h','--help'):
			print(help_txt)
			sys.exit()
		
		elif opt in ('-i','--input_file'):
			try:
				p = open(arg,'r')
			except FileNotFoundError:
				print("No such file")
				sys.exit(2)
			p.close()
			p = arg

		elif opt in ('-r','--reset_cost'):
			try:
				r = -1*float(arg)
			except ValueError:
				print("reset cost must be a numerical value")
				sys.exit(2)

		elif opt in ('-d','--default_cost'):
			try:
				d = -1*float(arg)
			except ValueError:
				print("default cost must be a numerical value")
				sys.exit(2)

		elif opt in ('-v','--expert_value'):
			try:
				v = 1*float(arg)
			except ValueError:
				print("expert value must be a numerical value")
				sys.exit(2)

		elif opt == "--steps_episode":
			try:
				STEPS_PER_EPISODE = int(arg)
			except ValueError:
				print("the number of steps per episode must be an integer")
				sys.exit(2)

		elif opt == "--number_episodes":
			try:
				nb = int(arg)
			except ValueError:
				print("the number of episodes must be an integer")
				sys.exit(2)

		elif opt == "--getExperience_mode":
			if arg.lower() not in ("min","max"):
				print("getExperience_mode must be max or min")
				sys.exit(2)
			if arg.lower() == "max":
				MODE =  MODE_MAX

	if nb == None:
		ACTIONTOEXECUTE = 5*STEPS_PER_EPISODE
	else:
		ACTIONTOEXECUTE = nb*STEPS_PER_EPISODE
	if r == None:
		r = -5
	if d == None:
		d = -1
	if p == None:
		print("Input file is mandatory")
		print("-----------------------")
		print(help_txt)
		sys.exit(2)

	if v == None:
		print("Expert value is mandatory")
		print("-----------------------")
		print(help_txt)
		sys.exit(2)
	LearningMRM(p,r,d,v)
