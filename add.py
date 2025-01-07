# s1="xxy"
# s2="aab"
# l1=[]
# l2=[]
# st1=dict.fromkeys(s1)
# st2=dict.fromkeys(s2)
# for i in range(len(st1)):
#     l1.append(s1.count(st1[i]))
#     l2.append(s2.count(st2[i]))
    
# if(l1==l2):
#     print("Y")
# else:
#     print("N")


l1=[1,2,3,4,2]
l2=[1,2,3,5,7]

print(set(l1)&set(l2))


