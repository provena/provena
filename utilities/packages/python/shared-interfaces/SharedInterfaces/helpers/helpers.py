import collections
from typing import List

def duplicates(my_list: List[str]) -> List[str]:
    # Use collections counter object to get unique list of the inputted items 
    # and the fre of each to check for duplicates and return any :).
    return [h for h, count in collections.Counter(my_list).items() if count > 1]

def has_duplicates(my_list: List[str]) -> bool:
    return len(duplicates(my_list))>0