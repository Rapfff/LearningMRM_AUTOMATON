from Map import Map
from MRM import MRM

class Model:

	def __init__(self,path,reset_cost,default_reward):
		self.map = Map(path)
		self.mrm = MRM(path, reset_cost, default_reward)

	def moveAPF(self,direction):
		obs = self.map.move(direction)
		rew = self.mrm.move(obs)
		return [obs,rew]

	def reset(self):
		self.map.reset()
		self.mrm.reset()