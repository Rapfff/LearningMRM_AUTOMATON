from tkinter import *
import Map
import time

class GUI:

	def __init__(self,map,positions,rewards,observations):
		self.fenetre = Tk()

		self.grid_width = 600
		self.grid_height = 600

		self.cell_width = self.grid_width / map.width
		self.cell_height = self.grid_height / map.height

		self.positions = positions
		self.rewards = rewards
		self.rewardsTxt = 0
		self.observations = observations
		self.observationsTxt = "Start"
		self.current = 1

		self.labelVariables = LabelFrame(self.fenetre, text="Variables", padx=20, pady=20)
		self.labelVariables.pack(fill="both",expand="yes")
		self.labelRewards = Label(self.labelVariables)
		self.labelRewards.configure(text="Cumulated reward = "+str(self.rewardsTxt))
		self.labelRewards.pack(anchor='nw')
		self.labelObservations = Label(self.labelVariables)
		self.labelObservations.pack(anchor='sw')
		
		self.canvas = Canvas(self.fenetre, width=self.grid_width, height = self.grid_height)
		
		for i in range(map.height+1):
			self.canvas.create_line(0,i*self.cell_height,self.grid_width,i*self.cell_height)
			self.canvas.create_line(i*self.cell_width,0,i*self.cell_width,self.grid_height)

		for r in range(map.height):
			for c in range(map.width):
				if map.cells[r][c].isObstacle():
					self.putObstacle(r,c)
				elif map.cells[r][c].observation != "null":
					self.putObs(r,c,map.cells[r][c].observation)

		self.initializeAgent()

		self.canvas.pack()
		self.canvas.update()
		time.sleep(0.5)
		while self.current < len(self.positions):
			self.fenetre.after(500,self.moveNext())

	def initializeAgent(self):
		r = self.positions[0][0]
		c = self.positions[0][1]
		self.agent = self.canvas.create_oval(int((r+0.25)*self.cell_height), int((c+0.25)*self.cell_width),int((r+0.75)*self.cell_height), int((c+0.75)*self.cell_width),fill='blue')
		self.ar = r
		self.ac = c

	def putObstacle(self,r,c):
		self.canvas.create_rectangle(r*self.cell_height, c*self.cell_width, (r+1)*self.cell_height, (c+1)*self.cell_width,fill='black')

	def putObs(self,r,c,o):
		self.canvas.create_text(int((r+0.5)*self.cell_height), int((c+0.5)*self.cell_width),text=o)

	def moveNext(self):
		self.rewardsTxt += self.rewards[self.current-1]
		self.labelRewards.configure(text="Cumulated reward = "+str(self.rewardsTxt))

		if self.observations[self.current-1] != "null":
			self.observationsTxt += "-> "+self.observations[self.current-1]
		elif self.observations[self.current-2] == "reset":
			self.observationsTxt = "reset"
		self.labelObservations.configure(text=self.observationsTxt)
		
		self.move(self.positions[self.current][0],self.positions[self.current][1])
		self.current += 1

	def move(self,r,c):
		dr = (r - self.ar)*self.cell_height
		dc = (c - self.ac)*self.cell_width
		self.canvas.move(self.agent,dr,dc)
		self.ar = r
		self.ac = c
		self.canvas.update()



if __name__ == "__main__":
	m = Map.Map("small_map.mp")
	g = GUI(m,[(0,0),(1,0),(1,1),(1,2),(2,2),(2,3),(0,0)],[-1,-1,10,-1,-1,-5])
