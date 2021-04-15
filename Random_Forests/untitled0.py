# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 18:19:39 2018

@author: Matthew
"""


import numpy as np

from sklearn import datasets as ds
from sklearn.decomposition import PCA
from sklearn import preprocessing

import matplotlib.pyplot as plt

data_all = ds.load_breast_cancer()

x = data_all.data
y = data_all.target

y_names = data_all.target_names 

feature_names = data_all.feature_names




split = int(x.shape[0] * 0.6)

x_train = x[:split,:]
y_train = y[:split]

x_test = x[split:,:]
y_test = y[split:]

print('Training set size:', x_train.shape[0])
print('Test set size:', x_test.shape[0])



pca = PCA(n_components=2)
x_scaled = preprocessing.scale(x[:,:-1]) # We remove the indexing and make sure all the features are in N(0,1)
x_reduced = pca.fit_transform(x_scaled)
#x_reduced = pca.fit_transform(x[:,0:-1]) # Uncomment this to see the result without scaling
fig = plt.figure(figsize=(9, 5), dpi=220)
plt.scatter(x_reduced[:, 0][y==0], x_reduced[:, 1][y==0], marker='+', label='Negative')
plt.scatter(x_reduced[:, 0][y==1], x_reduced[:, 1][y==1], marker='*', label='Positive')
plt.legend()
plt.show()



def calculate_entropy(y):
    # entropy formula is - SUM( p_i * log(p_i) )     i = 0,1
    # Probability for i = 0 is just number of 0's / total number
    values, numOfEl  = np.unique(y, return_counts=True)
    total = numOfEl.sum()
    entropy = - np.array([(numOfEl[i].astype(float) / total) * np.log2((numOfEl[i].astype(float) / total)) for i in range(len(numOfEl))]).sum()
    
    return entropy
    
    
    # **************************************************************** 4 marks  
    
print(calculate_entropy(y))



def find_split(x, y):
    """Given a dataset and its target values, this finds the optimal combination
    of feature and split point that gives the maximum information gain."""
    
    # Need the starting entropy so we can measure improvement...
    start_entropy = calculate_entropy(y)
    
    # Best thus far, initialised to a dud that will be replaced immediately...
    best = {'infogain' : -np.inf}
    
    # Loop every possible split of every dimension...
    for i in range(x.shape[1]):                                         # for the number of columns in our data x (so 2)
        for split in np.unique(x[:,i]):                                 # for the unique values in each column of x
            
            # Need to define left_indices, right_indices and infogain
            # Say everything to the left of some point is something and the other another?
            
            # 'left_indices': Indices of the exemplars that satisfy x[feature_index]<=split.
            
            left_indices = np.where(x[:,i] <= split)[0]
            right_indices = np.where(x[:,i] > split)[0]
#             left_indices = np.where(x[:,i] <= split)
#             right_indices = np.where(x[:,i] > split)
            
            # now the info gain
            #  I(split) = H(p(parent)) − (nl/n) * H(p(left)) − (nr/n) * H(p(right))
            infogain = start_entropy \
            - (len(left_indices))/(len(x[:,i])) * calculate_entropy(y[left_indices]) \
            - (len(right_indices))/(len(x[:,i])) * calculate_entropy(y[right_indices])
           
            

            if infogain > best['infogain']:
                best = {'feature' : i,
                        'split' : split,
                        'infogain' : infogain, 
                        'left_indices' : left_indices,
                        'right_indices' : right_indices}
    return best


print(find_split(x_train, y_train))



def build_tree(x, y, max_depth = np.inf):
    # Check if either of the stopping conditions have been reached. If so generate a leaf node...
    if max_depth==1 or (y==y[0]).all():
        # Generate a leaf node...
        classes, counts = np.unique(y, return_counts=True)
        return {'leaf' : True, 'class' : classes[np.argmax(counts)]}
    
    else:
        move = find_split(x, y)
        
        left = build_tree(x[move['left_indices'],:], y[move['left_indices']], max_depth - 1)
        right = build_tree(x[move['right_indices'],:], y[move['right_indices']], max_depth - 1)
        
        return {'leaf' : False,
                'feature' : move['feature'],
                'split' : move['split'],
                'infogain' : move['infogain'],
                'left' : left,
                'right' : right}



def predict_one(tree, sample):
    """Does the prediction for a single data point"""
    if tree['leaf']:
        return tree['class']
    
    else:
        if sample[tree['feature']] <= tree['split']:
            return predict_one(tree['left'], sample)
        else:
            return predict_one(tree['right'], sample)



def predict(tree, samples):
    """Predicts class for every entry of a data matrix."""
    ret = np.empty(samples.shape[0], dtype=int)
    ret.fill(-1)
    indices = np.arange(samples.shape[0])
    
    def tranverse(node, indices):
        nonlocal samples
        nonlocal ret
        
        if node['leaf']:
            ret[indices] = node['class']
        
        else:
            going_left = samples[indices, node['feature']] <= node['split']
            left_indices = indices[going_left]
            right_indices = indices[np.logical_not(going_left)]
            
            if left_indices.shape[0] > 0:                           # If there is at least 1 point in the left split.... 
                tranverse(node['left'], left_indices)               # Call transverse again
                
            if right_indices.shape[0] > 0:                          # If there is at least 1 point in the right split...
                tranverse(node['right'], right_indices)             # Call transverse again
    
    tranverse(tree, indices)
    return ret



tree = build_tree(x_train, y_train)                                  # Using the max depth
prediction_train = predict(tree, x_train)
prediction_test = predict(tree, x_test)

correct_train = prediction_train[y_train==prediction_train]
correct_test = prediction_test[y_test==prediction_test]

print('Train Data Accuracy : ', len(correct_train)*100/len(prediction_train), '%')
print('Test Data Accuracy : ', len(correct_test)*100/len(prediction_test), '%')



best_max_depth = 1
train_acc = 0.0
test_acc = 0.0


for i in range(2,6):
    tree = build_tree(x_train, y_train, max_depth=i)                                  # Using the max depth
    prediction_test = predict(tree, x_test)
    correct_test = prediction_test[y_test==prediction_test]    
    test_accuracy = len(correct_test)*100/len(prediction_test)
    
    
    if test_accuracy > test_acc:
        test_acc, best_max_depth = test_accuracy, i

tree = build_tree(x_train, y_train, max_depth=best_max_depth)
prediction_train = predict(tree, x_train)
correct_train = prediction_train[y_train==prediction_train]

print(tree)

print('Best max depth is ', best_max_depth)
print('Train Data Accuracy : ', len(correct_train)*100/len(prediction_train), '%')
print('Test Data Accuracy : ', test_acc, '%')









