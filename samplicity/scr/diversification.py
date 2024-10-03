import pandas as pd
import copy
from itertools import combinations


def shapely_calc(scr):

    # Remove the toal row
    scr = scr.iloc[:-1]
    scr_list=scr.index.to_list()

    #scr_list=scr['combinations']
    scr_list=[set(x) for x in scr_list]

    # Flattening the list of sets to get all elements
    element = [y for x in scr_list for y in x]

    # Replicating the list of sets for each element in the sets
    index_upper = [set(x) for x in scr_list for _ in x]

    # Creating a deep copy of index_upper
    index_lower = copy.deepcopy(index_upper)

    # Removing each element from the corresponding set in index_lower
    for x, y in zip(index_lower, element):
        x.discard(y)  # Using discard instead of remove to avoid KeyError if y is not found in x

    # Create a DataFrame
    div_index = pd.DataFrame({
        'index_upper': [frozenset(x) for x in index_upper],
        'element': element,
        'index_lower': [frozenset(x) for x in index_lower]
    },
        index= [frozenset(x) for x in index_upper])

    div_index['count']=div_index['index_upper'].apply(len)

    lower=pd.merge(div_index[['element','index_lower']],scr, how='left', left_on='index_lower', right_index=True)
    lower=lower.fillna(0).drop(['index_lower'], axis=1)
    upper=pd.merge(div_index[['element','count', 'index_upper']],scr, how='left', left_on='index_upper', right_index=True).fillna(0).drop(['index_upper'], axis=1)
    
    # Don't want the element or count element
    selected_columns = upper.columns.drop(['count','element'])  
    upper[selected_columns]=upper[selected_columns]-lower[selected_columns]

    # First group
    div_calc=upper.groupby(['element','count']).mean()
    #Last group
    div_calc=div_calc.groupby(['element']).mean()

    return(div_calc)