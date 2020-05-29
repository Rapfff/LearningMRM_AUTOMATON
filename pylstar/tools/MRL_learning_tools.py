# from treasure_map_world import labelingFunc
from treasure_map_world import labelingFunc
# from seventeen_node_domain import labelingFunc
# from cookie_domain import labelingFunc



def extractStateTrace(i_a_trace):
    # assuming interaction_trace = [action_1, state_1, reward_1, ..., action_k, state_k, reward_k]
    sttTrace = []
    for i in range(len(i_a_trace)):
        if i % 3 == 1:
            sttTrace.append(i_a_trace[i])
    return sttTrace


def extractRewTrace(interaction_trace):
    # assuming interaction_trace = [action_1, state_1, reward_1, ..., action_k, state_k, reward_k]
    rewTrace = []
    for i in range(len(interaction_trace)):
        if i % 3 == 2:
            rewTrace.append(interaction_trace[i])
    return rewTrace


def sttTrace2obsSeq(state_trace):
    obsSeq = []
    for s in state_trace:
        obsSeq.append(labelingFunc(s))
    return obsSeq


def i_a_Trace2obsSeq4CookieDomain(interaction_trace):
    obsSeq = []
    for i in range(len(interaction_trace)):
        a = None
        s = None
        if i % 3 == 1:
            a = interaction_trace[i-1]
            s = interaction_trace[i]
        obsSeq.append(labelingFunc(a, s))
    return obsSeq

