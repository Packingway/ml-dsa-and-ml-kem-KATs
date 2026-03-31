import random
import math

# precompute the twiddle factors
# 先基4再基2版本，优点 点乘时可以复用旋转因子，节省rom资源

kesai = 17
q = 3329

w_4_1 = (kesai ** 64) % q
inv_kesai = pow(w_4_1,63) % q

# 289, 296, 2319, 1197, 1339, 1534, 3253, 2447, 452, 2277, 1476, 1891,
# 2319, 1426, 1197, 1438, 535, 331, 807, 2094, 2055, 1534, 2882, 76,
# 650, 3046, 2474, 2865, 2240, 2617, 2513, 56, 910, 1320, 1333, 1848,
# 2647, 2393, 2513, 2474, 1974, 33, 1481, 2879, 2679, 1227, 821, 2009,

w_rom = [2580, 1729, 3289,
         1062, 2642, 2786, 193, 630, 1746, 2786, 1897, 1919, 569, 848, 3136,

         289, 296, 2319, 3253, 2447, 452, 1197, 1339, 1534, 2277, 1476, 1891,
         650, 3046, 2474, 2513, 56, 910, 2865, 2240, 2617, 1320, 1333, 1848,
         2319, 1426, 1197, 807, 2094, 2055, 1438, 535, 331, 1534, 2882, 76,
         2647, 2393, 2513, 1481, 2879, 2679, 2474, 1974, 33, 1227, 821, 2009,

         17, 2761, 583, 2649, 1637, 723, 2288, 1100, 1409, 2662, 3281, 233, 756, 2156, 3015, 3050, 1703, 1651, 2789,
         1789, 1847, 952, 1461, 2687, 939, 2308, 2437, 2388, 733, 2337, 268, 641, 1584, 2298, 2037, 3220, 375, 2549,
         2090, 1645, 1063, 319, 2773, 757, 2099, 561, 2466, 2594, 2804, 1092, 403, 1026, 1143, 2150, 2775, 886, 1722,
         1212, 1874, 1029, 2110, 2935, 885, 2154,
         3312, 568, 2746, 680, 1692, 2606, 1041, 2229, 1920, 667, 48, 3096, 2573, 1173, 314, 279, 1626, 1678, 540, 1540,
         1482, 2377, 1868, 642, 2390, 1021, 892, 941, 2596, 992, 3061, 2688, 1745, 1031, 1292, 109, 2954, 780, 1239,
         1684, 2266, 3010, 556, 2572, 1230, 2768, 863, 735, 525, 2237, 2926, 2303, 2186, 1179, 554, 2443, 1607, 2117,
         1455, 2300, 1219, 394, 2444, 1175]

# w_rom = [2580, 1729, 3289,
#          1062, 2642, 2786, 2786, 1897, 1919, 193, 630, 1746, 569, 848, 3136,
#
#          289, 296, 2319, 1197, 1339, 1534, 3253, 2447, 452, 2277, 1476, 1891,
#          2319, 1426, 1197, 1438, 535, 331, 807, 2094, 2055, 1534, 2882, 76,
#          650, 3046, 2474, 2865, 2240, 2617, 2513, 56, 910, 1320, 1333, 1848,
#          2647, 2393, 2513, 2474, 1974, 33, 1481, 2879, 2679, 1227, 821, 2009,
#
#          17, 2761, 583, 2649, 1637, 723, 2288, 1100, 1409, 2662, 3281, 233, 756, 2156, 3015, 3050, 1703, 1651, 2789,
#          1789, 1847, 952, 1461, 2687, 939, 2308, 2437, 2388, 733, 2337, 268, 641, 1584, 2298, 2037, 3220, 375, 2549,
#          2090, 1645, 1063, 319, 2773, 757, 2099, 561, 2466, 2594, 2804, 1092, 403, 1026, 1143, 2150, 2775, 886, 1722,
#          1212, 1874, 1029, 2110, 2935, 885, 2154,
#          3312, 568, 2746, 680, 1692, 2606, 1041, 2229, 1920, 667, 48, 3096, 2573, 1173, 314, 279, 1626, 1678, 540, 1540,
#          1482, 2377, 1868, 642, 2390, 1021, 892, 941, 2596, 992, 3061, 2688, 1745, 1031, 1292, 109, 2954, 780, 1239,
#          1684, 2266, 3010, 556, 2572, 1230, 2768, 863, 735, 525, 2237, 2926, 2303, 2186, 1179, 554, 2443, 1607, 2117,
#          1455, 2300, 1219, 394, 2444, 1175]


def DIT_NR_NTT(a,w_rom):
    n = 256
    log_n = int(math.log(n,4))
    r = 0
    for p in range(log_n-1,-1,-1):  #-1
        if p != 0:
            J = int(pow(4,p))
            for k in range(int(n/(4*J))):
                w1 = w_rom[r]
                w2 = w_rom[r+1]
                w3 = w_rom[r+2]
                r = r + 3
                # print(w1,w2,w3)
                # print('######################################')
                for j in range(J):
                    address0_old = 4*k*J + j
                    address1_old = 4*k*J + j + J
                    address2_old = 4*k*J + j + 2*J
                    address3_old = 4*k*J + j + 3*J

                    u0 = a[address0_old]
                    v0 = a[address1_old]
                    u1 = a[address2_old]
                    v1 = a[address3_old]

                    t0 = (u0 + (u1 * w2)) % q
                    t1 = (u0 - (u1 * w2)) % q
                    t2 = ((v0 * w1) + (v1 * w3)) % q
                    t3 = ((v0 * w1) - (v1 * w3)) % q

                    a[address0_old] = (t0 + t2) % q
                    a[address2_old] = (t1 + (t3 * w_4_1)) % q
                    a[address1_old] = (t0 - t2) % q
                    a[address3_old] = (t1 - (t3 * w_4_1)) % q
                    # print(address0_old,address1_old,address2_old,address3_old,'#',a[address0_old],a[address1_old],a[address2_old],a[address3_old])
        else:
            J = int(pow(2, p+1))
            for k in range(int(n/(2*J))):
                w = w_rom[r]
                r = r + 1
                for j in range(J):
                    u = a[k*2*J + j] % q
                    t = (a[k*2*J + j + J]*w) % q
                    a[k*2*J + j] = (u + t) % q
                    a[k*2*J + j + J] = (u - t) % q
    return a

def address_map(address):
    temp = bin(address)[2:].zfill(10)
    index = (int(temp[0:2],2) + int(temp[2:4],2) + int(temp[4:6],2) + int(temp[6:8],2) + int(temp[8:10],2)) % 4
    return index

def op21(a):
    if a & 1 == 0:
        r = (a >> 1) % q
    else:
        r = ((a >> 1) + ((q + 1)>>1)) % q
    return r

def DIF_RN_INTT(a,w_rom):
    n = 256
    log_n = int(math.log(n,4))
    # r = 126
    r = 126
    for p in range(0,1): # log_n
        if p == 0:
            J = int(pow(2, p+1))
            for k in range(int(n / (2 * J))):
                w = w_rom[r]
                r = r - 1
                for j in range(J):
                    u = a[k*2*J + j] % q
                    t = a[k*2*J + j + J] % q
                    a[k*2*J + j] = (op21(u + t)) % q
                    a[k*2*J + j + J] = (op21(t - u)*w) % q
            r = r - 2
        else:
            J = int(pow(4,p))
            for k in range(int(n/(4*J))):
                w1 = w_rom[r]
                w2 = w_rom[r+1]
                w3 = w_rom[r+2]
                r = r - 3
                for j in range(J):

                    address0_old = 4*k*J + j
                    address1_old = 4*k*J + j + J
                    address2_old = 4*k*J + j + 2*J
                    address3_old = 4*k*J + j + 3*J

                    u0 = a[address0_old]
                    v0 = a[address2_old]
                    u1 = a[address1_old]
                    v1 = a[address3_old]

                    t0 = op21(u0 + u1) % q
                    t1 = op21(u1 - u0)*w_4_1 % q
                    t2 = op21(v0 + v1) % q
                    t3 = op21(v1 - v0) % q

                    a[address0_old] = op21(t0 + t2) % q
                    a[address1_old] = op21(t1 + t3)*(w1) % q
                    a[address2_old] = op21(t2 - t0)*(w2) % q
                    a[address3_old] = op21(t3 - t1)*(w3) % q

    return a


def wise_pwm(x,y):
    q = 3329
    N = len(x)//4
    z = []
    for i in range(N):
        Linear0 = (x[4*i]*y[4*i] + x[4*i+1]*y[4*i+1]*w_rom[63+i]) % q
        Linear1 = (x[4*i]*y[4*i+1] + x[4*i+1]*y[4*i]) % q
        print(x[4 * i], w_rom[63+i])
        Linear2 = (x[4*i+2]*y[4*i+2] + x[4*i+3]*y[4*i+3]*(w_rom[127+i]%q)) % q
        Linear3 = (x[4*i+2]*y[4*i+3] + x[4*i+3]*y[4*i+2]) % q
        print(x[4 * i + 2], w_rom[127 + i])
        z.append(Linear0)
        z.append(Linear1)
        z.append(Linear2)
        z.append(Linear3)
    return z

def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    gcd, x1, y1 = extended_gcd(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    return gcd, x, y

def mod_inverse(a, m):
    gcd, x, _ = extended_gcd(a, m)
    if gcd != 1:
        raise Exception("逆元不存在，因为 a 和 m 不互质")
    else:
        return x % m


def test():
    a = []
    for i in range(256):
        a.append(i)
    # print(a)
    b = [1] * 256
    # b[0] = 1
    # b[1] = 1
    # b[2] = 2

    ffta = DIT_NR_NTT(a,w_rom)
    # fftb = DIT_NR_NTT(b,w_rom)
    # print("ffta = ",ffta)
    # print("fftb = ",fftb)

    # c = wise_pwm(ffta,fftb)
    # print("c = ",c)

    ifftc = DIF_RN_INTT(b,w_rom)
    print("ifftc = ",ifftc)


if __name__ == "__main__":
    test()
