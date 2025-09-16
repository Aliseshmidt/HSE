import time

def custom_time(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f'Function {func.__name__} completed at {end-start} sec')
        return result
    return wrapper()

# def linear_search(arr: list, target: int):
#     for i in range(len(arr)):
#         if arr[i] == target:
#             return i
#         else:
#             return None

# def test_linear_search():
#     assert linear_search([1,2,3,4], 3) == 2
#     assert linear_search([], 3) == None
#     assert linear_search([1, 2, 3, 4], 3) == 2
#     assert linear_search([1, 2, 3, 4], 3) == 2
#     assert linear_search([1, 2, 3, 4], 3) == 2

@custom_time
def binary_search(arr: list, target: int):
    left, right = 0, len(arr)-1
    while left<=right:
        mid = (left+right) //2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return None

custom_time(binary_search([1,2,3,4,5,6], 4))

