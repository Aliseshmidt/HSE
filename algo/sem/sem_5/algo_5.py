def subset(nums):
    result = []
    def bt(index, path):
        if index  == len(nums):
            result.append(path)
            return
        bt(index + 1, path)
        print(path, index)
        bt(index + 1, path + [nums[index]])
    bt(0, [])
    return result

print(subset([10,20,30]))