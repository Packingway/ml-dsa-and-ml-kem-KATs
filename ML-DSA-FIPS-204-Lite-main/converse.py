import params


# Computes a base-2 representation of 𝑥 mod 2^𝛼 using little-endian order.
# Input: A nonnegative integer 𝑥 and a positive integer 𝛼.
# Output: A bit string 𝑦 of length 𝛼
def IntegerToBits(x, a):
    x1=x
    y=[0]*a
    for i in range(a):
        y[i]=x1&1
        x1=x1>>1
    return y


# Computes the integer value expressed by a bit string using little-endian order.
# Input: A positive integer 𝛼 and a bit string 𝑦 of length 𝛼.
# Output: A nonnegative integer 𝑥.
def BitsToInteger(y, a):
    x=0
    for i in range(a):
        x=(x<<1)+y[a-i-1]
    return x


# Computes a base-256 representation of 𝑥 mod 256𝛼 using little-endian order.
# Input: A nonnegative integer 𝑥 and a positive integer 𝛼.
# Output: A byte string 𝑦 of length 𝛼.
def IntegerToBytes(x, a):
    x1=x
    y=bytearray(a)
    for i in range(a):
        y[i]=x1&0xff
        x1=x1>>8
    return y


# Converts a bit string into a byte string using little-endian order.
# Input: A bit string 𝑦 of length 𝛼.
# Output: A byte string 𝑧 of length ⌈𝛼/8⌉.
def BitsToBytes(y):
    a=len(y)
    z=bytearray((a+7)//8)
    for i in range(a):
        z[i>>3]+=y[i]<<(i&7)
    return z


# Converts a byte string into a bit string using little-endian order.
# Input: A byte string 𝑧 of length 𝛼.
# Output: A bit string 𝑦 of length 8𝛼.
def BytesToBits(z):
    a=len(z)*8
    y=[0]*a
    z1=z[:]
    for i in range(len(z)):
        for j in range(8):
            y[i*8+j]=z1[i]&1
            z1[i]=z1[i]>>1
    return y


# Generates an element of {0, 1, 2, … , 𝑞 − 1} ∪ {⊥}.
# Input: Bytes 𝑏0, 𝑏1, 𝑏2.
# Output: An integer modulo 𝑞 or ⊥.
# 24 bits to generate a 23 bit number less than 8380417
# Used in uniform sampling 
def CoeffFromThreeBytes(b0,b1,b2):
    b2_prime=b2&0x7f
    z=(b2_prime<<16)+(b1<<8)+b0
    if z<params.MLDSA_Q:
        return z
    else:
        return None

# Let 𝜂 ∈ {2, 4}. Generates an element of {−𝜂, −𝜂 + 1, … , 𝜂} ∪ {⊥}.
# Input: Integer 𝑏 ∈ {0, 1, … , 15}.
# Output: An integer between −𝜂 and 𝜂, or ⊥.
# Used in uniform sampling 
def CoeffFromHalfByte(eta,b):
    if eta==2 and b<15:
        return 2-b%5
    elif eta==4 and b<9:
        return 4-b
    else:
        return None


# Encodes a polynomial 𝑤 into a byte string.
# Input: 𝑏 ∈ ℕ and 𝑤 ∈ 𝑅 such that the coefficients of 𝑤 are all in [0, 𝑏].
# Output: A byte string of length 32 ⋅ bitlen b
def SimpleBitPack(w,b):
    z=[]
    blen=b.bit_length()
    for i in range(params.MLDSA_N):
        z+=IntegerToBits(w[i],blen)
    return BitsToBytes(z)

# Encodes a polynomial 𝑤 into a byte string.
# Input: 𝑎, 𝑏 ∈ ℕ and 𝑤 ∈ 𝑅 such that the coefficients of 𝑤 are all in [−𝑎, 𝑏].
# Output: A byte string of length 32 ⋅ bitlen (𝑎 + 𝑏)
def BitPack(w,a,b):
    z=[]
    lenab=(a+b).bit_length()
    for i in range(params.MLDSA_N):
        z+=IntegerToBits(b-w[i],lenab)
    return BitsToBytes(z)

# Reverses the procedure SimpleBitPack.
# Input: 𝑏 ∈ ℕ and a byte string 𝑣 of length 32 ⋅ bitlen 𝑏.
# Output: A polynomial 𝑤 ∈ 𝑅 with coefficients in [0, 2𝑐 − 1], where 𝑐 = bitlen 𝑏.
# When 𝑏 + 1 is a power of 2, the coefficients are in [0, 𝑏].
def SimpleBitUnpack(v,b):
    c=b.bit_length()
    z=BytesToBits(v)
    w=[0]*params.MLDSA_N
    for i in range(params.MLDSA_N):
        w[i]=BitsToInteger(z[i*c:(i+1)*c],c)
    return w


# Reverses the procedure BitPack.
# Input: 𝑎, 𝑏 ∈ ℕ and a byte string 𝑣 of length 32 ⋅ bitlen (𝑎 + 𝑏).
# Output: A polynomial 𝑤 ∈ 𝑅 with coefficients in [𝑏 − 2𝑐 + 1, 𝑏], where 𝑐 = bitlen (𝑎 + 𝑏).
# When 𝑎 + 𝑏 + 1 is a power of 2, the coefficients are in [−𝑎, 𝑏].
def BitUnpack(v,a,b):
    c=(a+b).bit_length()
    z=BytesToBits(v)
    w=[0]*params.MLDSA_N
    for i in range(params.MLDSA_N):
        w[i]=b-BitsToInteger(z[i*c:(i+1)*c],c)
    return w


# Encodes a polynomial vector 𝐡 with binary coefficients into a byte string.
# Input: A polynomial vector 𝐡 ∈ 𝑅2
# 𝑘 such that the polynomials 𝐡[0], 𝐡[1],...,𝐡[𝑘 − 1] have
# collectively at most 𝜔 nonzero coefficients.
# Output: A byte string 𝑦 of length 𝜔 + 𝑘 that encodes 𝐡 as described above.
def HintBitPack(omega,k,h):
    y=bytearray(omega+k)
    index=0
    for i in range(k):
        for j in range(params.MLDSA_N):
            if h[i][j]!=0:
                y[index]=j
                index+=1
        y[omega+i]=index
    return y

# Reverses the procedure HintBitPack.
# Input: A byte string 𝑦 of length 𝜔 + 𝑘 that encodes 𝐡 as described above.
# Output: A polynomial vector 𝐡 ∈ 𝑅2𝑘 or ⊥.
def HintBitUnpack(omega,k,y):
    h=[[0 for i in range(params.MLDSA_N)] for j in range(k)]
    index=0
    for i in range(k):
        if y[omega+i]<index or y[omega+i]>omega:       # 1 coefficients less than 0 error or more than omega
            return None
        first=index                     # first index of the ith polynomial
        while index<y[omega+i]:
            if index>first:
                if y[index-1]>=y[index]:          # former index is greater than or equal to current index
                    return None
            h[i][y[index]]=1
            index+=1
    #remained coefficients are all 0
    for i in range(index,omega):
        if y[i]!=0:
            return None
    return h


if __name__ == '__main__':
    print("Testing IntegerToBits and BitsToInteger functions...")
    x=475
    y=IntegerToBits(x,10)
    x1=BitsToInteger(y,10)
    if y==[1,1,0,1,1,0,1,1,1,0] and x1==x:
        print("Test passed")
    else:
        print("Test failed")
    print("Testing IntegerToBytes function...")
    x=259
    y=IntegerToBytes(x,3)
    if y.hex()=="030100":
        print("Test passed")
    else:
        print("Test failed")
    print("Testing BitsToBytes and BytesToBits function...")
    y=[1,1,0,1,1,0,0,1,1,0]
    z=BitsToBytes(y)
    y1=BytesToBits(z)
    if y1[:len(y)]==y and z.hex()=="9b01":
        print("Test passed")
    else:
        print("Test failed")
    print("Testing CoeffFromThreeBytes function...")
    z=CoeffFromThreeBytes(0x23,0x56,0xF8)
    if z==0x785623 and CoeffFromThreeBytes(0xFF,0xFF,0xFF)==None:
        print("Test passed")
    else:
        print("Test failed")
    print("Testing CoeffFromHalfByte function...")
    z=CoeffFromHalfByte(2,13)
    if z==-1 and CoeffFromHalfByte(4,12)==None:
        print("Test passed")
    else:
        print("Test failed")
    print("Testing SimpleBitPack and SimpleBitUnpack function...")
    w=[13]*256
    z=SimpleBitPack(w,15)
    w1=SimpleBitUnpack(z,15)
    if w1==w:
        print("Test passed")
    else:
        print("Test failed")
    
    print("Testing BitPack and BitUnpack function...")
    test=[-1,0,1,2]*64
    z=BitPack(test,1,2)
    test1=BitUnpack(z,1,2)
    if test1==test:
        print("Test passed")
    else:
        print("Test failed")

    print("Testing HintBitPack and HintBitUnpack function...")
    omega=4
    k=3
    h=[[0 for i in range(params.MLDSA_N)] for j in range(k)]
    h[0][1]=1
    h[0][100]=1
    h[1][2]=1
    h[2][234]=1
    y=HintBitPack(omega,k,h)
    if y.hex()=="016402ea020304" and HintBitUnpack(omega,k,y)==h:
        print("Test passed")
    else:
        print("Test failed")