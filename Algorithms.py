"""A collection of miscellaneous algorithms used throughout the program"""

import typing

def linear_search(data : typing.List[typing.Any], target : typing.Any) -> typing.List[any]:
    """Performs a linear search on the provided data to find any items matching the target."""
    matches : typing.List[any] = []
    for item in data:
        if item == target:
            matches.append(item)
    return matches

def merge_sort(data : typing.List[typing.Any]) -> typing.List[typing.Any]:
    """Sorts data using the recursive merge sort algorithm."""
    
    # base case
    if len(data) <= 1:
        return data
    
    mid : int = len(data) // 2
    left : typing.List[typing.Any] = data[:mid]
    right : typing.List[typing.Any] = data[mid:]

    left_sorted : typing.List[typing.Any] = merge_sort(left)
    right_sorted : typing.List[typing.Any] = merge_sort(right)

    sorted_data : typing.List[typing.Any] = []

    while len(left_sorted) > 0 and len(right_sorted) > 0:
        left_value : any = left_sorted[0]
        right_value : any = right_sorted[0]

        if left_value <= right_value:
            sorted_data.append(left_value)
            left_sorted.pop(0)
        else:
            sorted_data.append(right_value)
            right_sorted.pop(0)

    # add the remaining values from the lists
    sorted_data.extend(left_sorted)
    sorted_data.extend(right_sorted)

    return sorted_data