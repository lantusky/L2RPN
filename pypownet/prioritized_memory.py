"""
https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow/blob/master/contents/5.2_Prioritized_Replay_DQN/RL_brain.py
"""

import numpy as np

class SumTree(object):
  """
  This SumTree code is a modified version and the original code is from:
  https://github.com/jaara/AI-blog/blob/master/SumTree.py
  Story data with its priority in the tree.
  """
  data_pointer = 0

  def __init__(self, capacity):
    self.capacity = capacity  # for all priority values
    self.tree = np.zeros(2 * capacity - 1)
    # [--------------Parent nodes-------------][-------leaves to recode priority-------]
    #             size: capacity - 1                       size: capacity
    self.data = np.zeros(capacity, dtype=object)  # for all transitions
    # [--------------data frame-------------]
    #             size: capacity

  def add(self, p, data):
    tree_idx = self.data_pointer + self.capacity - 1
    self.data[self.data_pointer] = data  # update data_frame
    self.update(tree_idx, p)  # update tree_frame

    self.data_pointer += 1
    if self.data_pointer >= self.capacity:  # replace when exceed the capacity
      self.data_pointer = 0

  def update(self, tree_idx, p):
    change = p - self.tree[tree_idx]
    self.tree[tree_idx] = p
    # then propagate the change through tree
    while tree_idx != 0:    # this method is faster than the recursive loop in the reference code
      tree_idx = (tree_idx - 1) // 2
      self.tree[tree_idx] += change

  def get_leaf(self, v):
    """
    Tree structure and array storage:
    Array type for storing:
    [0,1,2,3,4,5,6]
    """
    parent_idx = 0
    while True:     # the while loop is faster than the method in the reference code
      cl_idx = 2 * parent_idx + 1         # this leaf's left and right kids
      cr_idx = cl_idx + 1
      if cl_idx >= len(self.tree):        # reach bottom, end search
        leaf_idx = parent_idx
        break
      else:       # downward search, always search for a higher priority node
        if v <= self.tree[cl_idx]:
          parent_idx = cl_idx
        else:
          v -= self.tree[cl_idx]
          parent_idx = cr_idx

    data_idx = leaf_idx - self.capacity + 1
    return leaf_idx, self.tree[leaf_idx], self.data[data_idx]

  @property
  def total_p(self):
    return self.tree[0]  # the root


class Memory(object):  # stored as ( s, a, r, s_ ) in SumTree
  """
  This Memory class is modified based on the original code from:
  https://github.com/jaara/AI-blog/blob/master/Seaquest-DDQN-PER.py
  """
  epsilon = 0.01  # small amount to avoid zero priority
  beta_increment_per_sampling = 0.001
  abs_err_upper = 1.  # clipped abs error

  def __init__(self, capacity, alpha=0.6, beta=0.4):
    self.capacity = capacity
    self.tree = SumTree(capacity)
    self.alpha = alpha
    self.beta = beta

  def store(self, transition):
    max_p = np.max(self.tree.tree[-self.tree.capacity:])
    if max_p == 0:
      max_p = self.abs_err_upper
    self.tree.add(max_p, transition)   # set the max p for new p

  def sample(self, n):
    b_idx, b_memory, ISWeights = np.empty((n,), dtype=np.int32), [], []
    pri_seg = self.tree.total_p / n       # priority segment
    self.beta = np.min(
        [1., self.beta + self.beta_increment_per_sampling])  # max = 1

    # for later calculate ISweight
    # min_prob = np.min(self.tree.tree[-self.tree.capacity:]) / self.tree.total_p
    for i in range(n):
      a, b = pri_seg * i, pri_seg * (i + 1)
      v = np.random.uniform(a, b)
      idx, p, data = self.tree.get_leaf(v)
      prob = p / self.tree.total_p
      ISWeights.append(np.power(self.capacity * prob, -self.beta))
      b_idx[i] = idx
      b_memory.append(data)
    max_weight = max(ISWeights)
    ISWeights = [x / max_weight for x in ISWeights]
    return b_idx, b_memory, ISWeights

  def batch_update(self, tree_idx, abs_errors):
    abs_errors += self.epsilon  # convert to abs and avoid 0
    clipped_errors = np.minimum(abs_errors, self.abs_err_upper)
    ps = np.power(clipped_errors, self.alpha)
    for ti, p in zip(tree_idx, ps):
      self.tree.update(ti, p)


if __name__ == "__main__":
  exp = Memory(32)
  for i in range(10):
    exp.store(np.array([[1, 2], 2, 3, [2, 3], 5]))

  b_idx, b_memory, ISWeights = exp.sample(2)
  print(b_idx, b_memory, ISWeights)
