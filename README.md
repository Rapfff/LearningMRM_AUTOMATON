# LearningMRM

# Prerequisites

* [stormpy](https://moves-rwth.github.io/stormpy/)
* tkinter

# Parameters

* **map** : a file with the map representing the model (as in the examples).
* **expert value** : the value given by the expert for the first check.
* **default cost** : the cost for every move that doesn't bring any observation. (default: 1)
* **reset cost** : the cost paid to reset the system. (default: 5)
* **steps per episode** : number of steps for each episode of exploration during the checks. (default: 5000)
* **number of episodes** : number of episode of checks. (default: 5)
* **getExperience mode** : mode of the experience function (MIN or MAX). (default: MIN)
* **animation** : True to display the animation of the best strategy execution at the end. (default: False)
* **steps for animation** : number of steps shown in the animation. (default: 50)

# Usage
```
Learning_MRMs.py -i <input_file> -v <expert_value>
                [-r <reset_cost>]
                [-d <default_cost>]
                [-a <animation>]
                [--steps_animation <integer>]
                [--steps_episode <integer>]
                [--number_episodes <integer>]
                [--getExperience_mode <True|False>]
```

# Example
```
Learning_MRMs -i small_map.mp -r 5 -d 1 -a True -v 10 --getExperience_mode MAX
```
