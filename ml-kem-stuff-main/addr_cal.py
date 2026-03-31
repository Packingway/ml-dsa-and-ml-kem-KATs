# 实现旋转因子的地址计算，以及旋转因子。
mod = 3329
base = 17
mode = 1 # mode=0 表示计算NTT的旋转因子索引 ，mode = 1 表示计算INTT的旋转因子索引。

def reverse_group_order(lst):
    # 计算组数
    group_count = len(lst) // 3 + (1 if len(lst) % 3 != 0 else 0)
    # 初始化一个空列表用于存放结果
    result = []
    # 遍历每个组
    for i in range(group_count):
        # 计算当前组的起始索引和结束索引
        start_index = i * 3
        end_index = start_index + 3
        # 如果当前组的结束索引超出了列表的长度，则取到列表的末尾
        if end_index > len(lst):
            end_index = len(lst)
        # 将当前组的元素添加到结果列表中
        result.append(lst[start_index:end_index])
    # 颠倒每组之间的顺序
    result.reverse()
    # 将结果列表中的子列表展开成一个一维列表
    result = [item for sublist in result for item in sublist]
    return result

# 示例

value  = [64]
index = []
for i in range(85):
    temp  = value[i] >> 1  
    temp1 = (value[i]>> 1) + 64
    if mode == 0:
        index.append(value[i])
        if i <= 20 :
            index.append(value[i]>>1)
            index.append((value[i]>>1) + value[i])
        else:
            index.append(0)
            index.append(value[i])
    else :
        index.append(256-value[i])
        if i <= 20 :
            index.append(256-(value[i]>>1))
            index.append(256-((value[i]>>1) + value[i]))
        else:
            index.append(0)
            index.append(256-value[i])
        
    
    value.append(temp>> 1)  
    value.append((temp >> 1 )+ 64)
    value.append(temp1>> 1)  
    value.append((temp1 >> 1 )+ 64)


 
# a1 = reverse_group_order(index[0:3])
# a2 = reverse_group_order(index[3:15])   
# a3 = reverse_group_order(index[15:63])   
# a4 = reverse_group_order(index[63:255])  
# b=[]
# b=b+a1+a2+a3+a4
# if mode == 1:
#     index = b

 

print(index)


# NTT/INTT旋转因子计算
for i in range(0, len(index), 3):
    line = []
    for j in range(3):
        if i + j < len(index):
            value = pow(base, index[i + j], mod)
            if mode == 1:  # INTT 还需要对旋转因子进行1/4运算，避免NTT执行过程中是进行1/4，降低硬件需求
                if value == 1:
                    value = 1665  # 2的逆元
                else:
                    value = (value >> 1) + (value & 0x01)*1665
                    if i < 63:
                        value = (value >> 1) + (value & 0x01)*1665
            hex_str = f"{value:06x}"  # 24位十六进制
            line.append(hex_str)
    print(''.join(line))


# 计算PWM中所需要用到的旋转因子
def reverse_binary_counter(counter):
    # 将计数器值转换为7位二进制字符串，不足7位前面补0
    binary_str = bin(counter)[2:].zfill(7)
    # 创建一个长度为7的列表，用于存储反序后的二进制位
    reversed_binary_list = ['0'] * 7
    # 遍历原始二进制字符串，将其每一位反序放置到新列表中
    for i in range(7):
        reversed_binary_list[6 - i] = binary_str[i]
    # 将列表转换为字符串
    reversed_binary_str = ''.join(reversed_binary_list)
    # 将反序后的二进制字符串转换为十进制数
    reversed_decimal = int(reversed_binary_str, 2)
    return reversed_binary_str, reversed_decimal

# 示例
counter = 127
index_pwm = []
while counter > 1:  # 你可以根据需要调整范围
    reversed_binary_value, reversed_decimal_value = reverse_binary_counter(counter)
    index_pwm.append(reversed_decimal_value)  
    # print( reversed_decimal_value)
    counter -= 1

print(index_pwm)

for i in range (128):
    index_pwm[i] = index_pwm[i] * 2 + 1
    value = pow(base, index_pwm[i], mod)
    hex_str = f"{value:018x}"  # 24位十六进制
    print(hex_str)
