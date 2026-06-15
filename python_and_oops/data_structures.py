# arr = [1,2,3,"2"]
# arr.reverse()
# print(arr)
# arr = ["abc", "def","aaaa","a"]
# arr.sort(key=lambda x: len(x))
# print(arr)
# arr = [i*i for i in range(5)]
# print(arr)
# twod_arr = [[0]*4 for _ in range(4)]
# print(twod_arr)
# strings = ["abc", "def", "aaaa", "a"]
# print("".join(strings))
#queues
# from collections import deque
# q = deque()
# q.append(1)
# q.append(2)
# print(q)
# q.popleft()
# q.appendleft(2)
# print(q)
# print(set([1,2,3,4,5,1,2,3]))
# mymap = {}
# mymap["alice"] = 1
# print(mymap)


# import heapq as hq
# minheap = []
# hq.heappush(minheap, 3)
# hq.heappush(minheap, 1)
# hq.heappush(minheap, 2)
# print(minheap)
# hq.heappop(minheap)
# print(minheap)
# for max heap, we can push negative of the values and pop the negative of the values to get the original values in max heap order.
# arr = [-1, -2, -3, -4]
# hq.heapify(arr)
# while arr:
#     print(-1 * hq.heappop(arr))

