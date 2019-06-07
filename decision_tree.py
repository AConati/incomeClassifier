from load_data import load_data
from collections import defaultdict
import math


def represents_integer(s):
    """Return true if the string s is an integer, false otherwise.
    
    This is used for determining if an attribute is categorical or continuous.
    """
    try:
        int(s)
        return True
    except ValueError:
        return False


def find_baseline_attribute(data):
    """Finds the singular attribute of the data that has the most predictive power.
    (ie. The attribute which allows us to predict the highest proportion of the training data.)
    
    Arguments:
    data --- A list of dictionaries as returned by the function load_data in load_data.py.
    """
    best_ratio = 0
    best_attribute = None
    data_length = len(data)

    for attribute in data[0]:
        if attribute == 'fnlwgt':
            continue
        correct = 0
        if represents_integer(data[0][attribute]):  # check if attribute is continuous
            counts = get_counts(data, attribute, find_threshold(data, attribute))
        else:
            counts = get_counts(data, attribute)

        for category in counts:
            correct += counts[category][0] if counts[category][0] > counts[category][1] else counts[category][1]
        
        if correct / data_length > best_ratio:
            best_attribute = attribute
            best_ratio = correct / data_length

    if represents_integer(data[0][best_attribute]):
        counts = get_counts(data, best_attribute, find_threshold(data, attribute))
    else:
        counts = get_counts(data, best_attribute)

    labels = {}
    for category in counts:
        labels[category] = 0 if counts[category][0] > counts[category][1] else 1

    return best_attribute, labels


def baseline_classify(item, attribute, labels, threshold=None):
    item_category = item[attribute]
    if threshold is not None:
        if int(item[attribute]) < threshold:
            return labels['below']
        return labels['above']

    return labels[item_category]


class Node:
    """The class which represents the decision tree.

    Instance Variables:
    attribute -- The attribute on which this nodes splits.
    children -- The children of this node.
    label -- The label we should give any data point at this node, assuming the data point
             is not passed on to a child of the current node.
    category -- The subcategory that this node belongs to based on the attribute of its parent.
    threshold -- If the node's attribute is continuous, the value it splits on.


    """
    def __init__(self, category=None, label=-1):
        self.attribute = None
        self.children = []
        self.label = label
        self.category = category
        self.threshold = None

    def display(self, max_level=3, level=0):
        """Simple method which prints the contents of the decision tree up to max_level
        """
        print('\t' * level + repr((self.attribute, self.category, self.label)))
        if level > max_level:
            return
        for child in self.children:
            child.display(level + 1)


def decision_tree_classify(item, node):
    """Classifies data according to a decision tree.
        
    Arguments:
    item --- A dictionary corresponding to a data point.
    node --- A decision tree.
    """

    
    if len(node.children) == 0:
        return node.label
    category = item[node.attribute]
    if not represents_integer(category):
        for child in node.children:
            if child.category == category:
                return decision_tree_classify(item, child)
    else:
        if int(category) < node.threshold:
            return decision_tree_classify(item, node.children[0])
        return decision_tree_classify(item, node.children[1])

    return decision_tree_classify(item, node.children[0])


def build_decision_tree(data, max_depth=None):
    """Creates a decision tree recursively based on training data. Continuous attributes
    are only split on one time at most.

    Arguments:
    data --- A list of dictionaries as outputted by load_data in load_data.py.
    max_depth --- The maximum depth of the decision tree.
    """
    root = Node()
    attributes = [attribute for attribute in data[0]]
    attributes.remove('fnlwgt')
    attributes.remove('class')
    _build_decision_tree(data, root, attributes, max_depth)
    return root


def _build_decision_tree(data, node, attributes, max_depth=None, depth=0):
    """Recursive helper method for the build_decision_tree function
    """
    depth += 1
    data_classes = [data_point['class'] for data_point in data]
    node.label = majority_label(data)
    if len(attributes) == 0 or len(data_classes) == len(set(data_classes)):
        return
    #  if examples have exactly the same attributes, stop recursing
    if max_depth is not None and depth > max_depth:
        return

    max_information_gain = -1
    best_attribute = None
    best_threshold = None
    for attribute in attributes:
        threshold = None
        if(represents_integer(data[0][attribute])):
            threshold = find_threshold(data, attribute)
            information_gain = get_information_gain(data, attribute, threshold)
        else:
            information_gain = get_information_gain(data, attribute)
        if information_gain > max_information_gain:
            max_information_gain = information_gain
            best_attribute = attribute
            best_threshold = threshold

    if represents_integer(data[0][best_attribute]):
        subsets = split_on_attribute(data, best_attribute, best_threshold)
    else:
        subsets = split_on_attribute(data, best_attribute)
    node.attribute = best_attribute
    node.threshold = best_threshold

    for subset in subsets:
        new_node = Node(category=subset[1])
        node.children.append(new_node)
        if len(subset[0]) == 0:
            new_node.label = majority_label(data)
        else:
            new_attributes = list(attributes)
            new_attributes.remove(best_attribute)
            _build_decision_tree(subset[0], new_node, new_attributes, max_depth, depth)


def split_on_attribute(data, attribute, threshold=None):
    """Helper function for build_decision_tree which splits data based on a given attribute.

    Arguments:
    data --- A list of dictionaries as output by load_data in load_data.py.
    attribute --- The attribute to split the data on.
    threshold --- The threshold to split the data on if the attribute is continuous.

    Returns --- A tuple (subset, category) where category is a subcategory of the given attribute
                and subset is the subset of the data which correspond to that subcategory.
    """
    if threshold is not None:
        return split_on_attribute_threshold(data, attribute, threshold)

    data_categories = defaultdict(lambda: [])
    for data_point in data:
        data_categories[data_point[attribute]].append(data_point)

    return [(data_categories[key], key) for key in data_categories]


def split_on_attribute_threshold(data, attribute, threshold):
    """Helper function for split_on_attribute which handles continuous attributes.
    """

    data_categories = {'below': [], 'above': []}

    for data_point in data:
        if int(data_point[attribute]) < threshold:
            data_categories['below'].append(data_point)
        else:
            data_categories['above'].append(data_point)

    return [(data_categories[key], key) for key in data_categories]


def majority_label(data):
    """Returns the majority label (income class) associated with the given data.
    """
    counts_positive = 0
    counts_negative = 0
    for data_point in data:
        if data_point['class'] == 0:
            counts_negative += 1
        else:
            counts_positive += 1

    return 0 if counts_negative > counts_positive else 1


def get_counts(data, attribute, threshold=None):
    """Gets the counts of each class for each subcategory of an attribute.

    Arguments:
    data --- A list of dictionaries as output by load_data in load_data.py.
    attribute --- The attribute to separate the counts on.
    threshold --- If the attribute is continuous, the threshold to separate the data on.

    Returns: A dictionary with entries {category: (y_1, y_2)} where category is a category
    based on the attribute and y_1, y_2 are the number of data points in the data which have
    income classes <=50K and >50K, respectively. If the attribute is continuous, the categories
    are 'below' and 'above', corresponding to below and above the threshold value.
    """
    if threshold is not None:
        return get_counts_threshold(data, attribute, threshold)
    counts = defaultdict(lambda: [0, 0])
    for item in data:
        if item['class'] == 0:
            counts[item[attribute]][0] += 1
        else:
            counts[item[attribute]][1] += 1

    counts = {item: tuple(counts[item]) for item in counts}

    return counts


def get_counts_threshold(data, attribute, threshold):
    """Helper function for get_counts which handles continuous attributes.
    """
    counts = {'below': [0, 0], 'above': [0, 0]}
    for item in data:
        if item['class'] == 0 and int(item[attribute]) < threshold:
            counts['below'][0] += 1
        elif item['class'] == 0 and int(item[attribute]) >= threshold:
            counts['above'][0] += 1
        elif item['class'] == 1 and int(item[attribute]) < threshold:
            counts['below'][1] += 1
        else:
            counts['above'][1] += 1
    return counts


def find_threshold(data, attribute):
    """Finds the threshold which maximizes the information gain for the given attribute.
    This is done by testing all possible thresholds which do not lie between two points which
    share the same class. 

    Arguments:

    data --- A list of dictionaries as output by load_data.
    attribute --- The continuous attribute for which the optimal threshold is found.
    """
    sorted_data = sorted(data, key=lambda i: i[attribute])
    previous_class = -1
    max_info_gain = 0
    best_threshold = 0

    tested = []

    for x in range(len(data)):
        if sorted_data[x][attribute] not in tested and sorted_data[x]['class'] != previous_class:
            threshold = sorted_data[x][attribute]
            tested.append(threshold)
            threshold_info_gain = get_information_gain_threshold(sorted_data, attribute, threshold)
            if threshold_info_gain > max_info_gain:
                max_info_gain = threshold_info_gain
                best_threshold = threshold

        previous_class = sorted_data[x]['class']

    return int(best_threshold)


def get_information_gain(data, attribute, threshold=None):
    """Finds the information gain of a particular attribute.

    Arguments:

    data --- A list of dictionaries as output by load_data.
    attribute --- The attribute for which the information gain is calculated.
    threshold --- If the attribute is continuous, the threshold on which to split.
    """
    counts = get_counts(data, attribute, threshold)
    total_0 = 0
    total_1 = 0

    for category in counts:
        total_0 += counts[category][0]
        total_1 += counts[category][1]

    entropy = 0
    if total_0 != 0 and total_1 != 0:
        entropy = -((total_0 / len(data) * math.log(total_0 / len(data), 2)) + (total_1 / len(data) * math.log(total_1 / len(data), 2)))

    conditional_entropy = 0
    for category in counts:
        if counts[category][0] == 0 or counts[category][1] == 0:
            continue
        total = counts[category][0] + counts[category][1]
        proportion = total / len(data)
        label_0 = (counts[category][0] / total) * (math.log(counts[category][0] / total, 2))
        label_1 = (counts[category][1] / total) * (math.log(counts[category][1] / total, 2))
        conditional_entropy += proportion * (label_0 + label_1)
    conditional_entropy *= -1

    return entropy - conditional_entropy


def get_information_gain_threshold(sorted_data, attribute, threshold):
    """Helper method for find_threshold which calculates the information gain of a given
    threshold for the purpose of finding the optimal threshold.
    """
    counts_bt = [0, 0]  # bt = below threshold, at = above threshold
    counts_at = [0, 0]
    current_index = 0
    while sorted_data[current_index][attribute] < threshold:
        if sorted_data[current_index]['class'] == 0:
            counts_bt[0] += 1
        else:
            counts_bt[1] += 1
        current_index += 1
    
    for x in range(current_index, len(sorted_data)):
        if sorted_data[x]['class'] == 0:
            counts_at[0] += 1
        else:
            counts_at[1] += 1

    total_bt = (counts_bt[0] + counts_bt[1])
    total_at = (counts_at[0] + counts_at[1])

    if 0 in counts_bt or 0 in counts_at:
        return 0

    probability_bt = total_bt / len(sorted_data)
    probability_at = total_at / len(sorted_data)
    conditional_bt = (counts_bt[0] / total_bt) * math.log((counts_bt[0] / total_bt), 2) + (counts_bt[1] / total_bt) * math.log((counts_bt[1] / total_bt), 2)
    conditional_at = (counts_at[0] / total_at) * math.log((counts_at[0] / total_at), 2) + (counts_at[1] / total_at) * math.log((counts_at[1] / total_at), 2)

    return probability_bt * -conditional_bt + probability_at * -conditional_at