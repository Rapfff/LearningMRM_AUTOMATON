#from pylstar.tools.Decorators import PylstarLogger
from pylstar.KnowledgeBase import KnowledgeBase
from pylstar.Letter import Letter
import treasure_map_world_4 as tmw
import pylstar.tools.MRL_learning_tools as mlt
import copy


class MRMActiveKnowledgeBase(KnowledgeBase):
    """
    The class that implements the main mecanism of an active Mealy Reward Machine knowledge base.
    """

    # def __init__(self, cache_file_path=None):
    #     super(MRMActiveKnowledgeBase, self).__init__(cache_file_path=cache_file_path)

    def __init__(self):
        super(MRMActiveKnowledgeBase, self).__init__()


    def _execute_word(self, word):
        """Executes the specified word."""

        if word is None:
            raise Exception("Word cannot be None")

        self._logger.debug("Execute word '{}'".format(word))

        plan = self.findOptimalPlanToAnswer(word, tmw.current_state)
        interaction_trace = self.executePlan(plan, tmw.current_state)
        state_trace = mlt.extractStateTrace(interaction_trace)
        observation_seq = mlt.sttTrace2obsSeq(state_trace)
        while observation_seq != word:
            interaction_trace = self.executePlan(plan, tmw.current_state)
            state_trace = mlt.extractStateTrace(interaction_trace)
            observation_seq = mlt.sttTrace2obsSeq(state_trace)
        reward_trace = mlt.extractRewTrace(interaction_trace)
        return reward_trace

    def findOptimalPlanToAnswer(self, observations, s):
        plan = []
        for obs in observations.letters:
            maxEP = -1000000000
            bestAct = None
            bestState = dict()
            for a in tmw.A:
                maxProb = -1
                expectedProb = 0
                for ss in tmw.S:
                    if Letter(tmw.labelingFunc(ss)) == obs:
                        transProb = tmw.T(s, a, ss)
                        expectedProb += transProb
                        if transProb > maxProb:
                            maxProb = transProb
                            bestState[a] = ss
                if expectedProb > maxEP:
                    maxEP = expectedProb
                    bestAct = a
            plan.append(bestAct)
            s = bestState[bestAct]
        #return [Letter(symbol) for symbol in plan]
        return plan

    def executePlan(self, plan, s):
        intActTrace = []
        for a in plan:
            intActTrace.append(a)
            s_next = tmw.NextState(s, a)
            s_next_copy = copy.deepcopy(s_next)
            # Reward() potentially removes the rewarding feature from the last state in state-trace. (Agent gets reward only once for reaching the feature.)
            r = tmw.Reward(s_next)
            tmw.RemoveUsedResource(s_next, r)
            intActTrace.append(s_next_copy)
            intActTrace.append(r)
            updateInteractionTrace(interaction_trace, a, s_next, r)
        return intActTrace


