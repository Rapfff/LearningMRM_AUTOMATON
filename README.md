# LearningMRM

## Description
Given a nrMDP and a MRM this framework will learn the MRM from the nrMDP and several experiments using the Angluin algorithm apply on mealy machine.

## nrMDP and MRM file format
The nrMDP and the MRM are described in a file structured as follow:
```
<description of the nrMDP>
OBSERVATIONS
<description of the observation function>
MRM DESCIPTION
<description of the MRM>
```
### Description of the nrMDP
The first line list the initial states as follow:
```
initial <list of the names of the initial states separated by ",">
```
Example:
```
initial s0,s1
```
Then each line describe a transition as follow:
```
<strating state> <action> <probability> <destination>
```
Example:
```
s0 a 0.2 s1
```
The probability can also be written down by a fraction:
```
s0 a 1/5 s1
```

### Description of the observation function
An observation function returns an observation for a pair state-action. Each line corresponds to an observation:
```
<state> <action> <observation>
```
If a pair isn't represented by any line the observation corresponding to this pair is 'null'. Example:
```
s0 a A
```
In this case the pair $(s0,a)$ corresponds to the observation $A$. Suppose the action $b$ is available in $s0$, then the pair $(s0,b)$ corresponds to the observation 'null'.

### Description of the MRM
The MRM is a mealy machine where the input alphabet are the obseravtions and the output alphabet some rewards. Each line corresponds to a transition in this mealy machine as follow:
```
<starting state> <observation> <reward> <destination state>
```
Example:
```
0 A 10 1
```
In this case if the current state of the MRM is 0, if the agent observes A by moving in the nrMDP then he gets a reward of 10 and the MRM changes its current state to 1.
  
  
## Prerequisites

* [stormpy](https://moves-rwth.github.io/stormpy/)

## Parameters

* **map** : a file with the map representing the model.
* **expert value** : the value given by the expert for the first check.
* **default cost** : the cost for every move that doesn't bring any observation. (default: 1)
* **reset cost** : the cost paid to reset the system. (default: 5)
* **steps per episode** : number of steps for each episode of exploration during the second checks. (default: 5000)
* **number of episodes** : number of episode of exploration during the second checks. (default: 5)
* **getExperience mode** : mode of the experience function (MIN or MAX). (default: MIN)

## Usage
```
Learning_MRMs.py -i <input_file> -v <expert_value>
                [-r <reset_cost>]
                [-d <default_cost>]
                [--steps_episode <integer>]
                [--number_episodes <integer>]
                [--getExperience_mode <MIN|MAX>]
```

## Example
```
Learning_MRMs -i examples/example.mp -r 5 -d 1 -a True -v 1.5 --getExperience_mode MAX
```
## Remark
The code in pylstar is not from me.
