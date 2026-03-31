import params

# Decomposes 𝑟 into (𝑟1, 𝑟0) such that 𝑟 ≡ 𝑟12𝑑 + 𝑟0 mod 𝑞.
# Input: 𝑟 ∈ ℤ𝑞.
# Output: Integers (𝑟1, 𝑟0)
def Power2Round(r):
    r_plus=r%params.MLDSA_Q
    r0=r_plus&((1<<params.MLDSA_D)-1)
    if r0>(1<<params.MLDSA_D-1):
        r0-=1<<params.MLDSA_D
    return (r_plus-r0)>>params.MLDSA_D, r0


# Decomposes 𝑟 into (𝑟1, 𝑟0) such that 𝑟 ≡ 𝑟1(2𝛾2) + 𝑟0 mod 𝑞.
# Input: 𝑟 ∈ ℤ𝑞.
# Output: Integers (𝑟1, 𝑟0).
def Decompose(gamma2,r):
    r1=0
    r_plus=r%params.MLDSA_Q
    r0=r_plus%(gamma2*2)
    if r0>gamma2:
        r0-=gamma2*2
    if r_plus-r0==params.MLDSA_Q-1:
        r0-=1
    else:
        r1=(r_plus-r0)//(2*gamma2)
    return r1,r0


# Returns 𝑟1 from the output of Decompose (𝑟).
# Input: 𝑟 ∈ ℤ𝑞.
# Output: Integer 𝑟1.
def HighBits(gamma2,r):
    r1,r0=Decompose(gamma2,r)
    return r1


# Returns 𝑟0 from the output of Decompose (𝑟).
# Input: 𝑟 ∈ ℤ𝑞.
# Output: Integer 𝑟0.
def LowBits(gamma2,r):
    r1,r0=Decompose(gamma2,r)
    return r0


# Computes hint bit indicating whether adding 𝑧 to 𝑟 alters the high bits of 𝑟.
# Input: 𝑧, 𝑟 ∈ ℤ𝑞.
# Output: Boolean.
def MakeHints(gamma2,z,r):
    r1=HighBits(gamma2,r)
    v1=HighBits(gamma2,r+z)
    return v1!=r1

def MakeHints_vec(k,gamma2,z,r):
    h=[[0 for i in range(params.MLDSA_N)] for j in range(k)]
    for i in range(k):
        for j in range(params.MLDSA_N):
            h[i][j]=MakeHints(gamma2,z[i][j],r[i][j])
    return h


# Returns the high bits of 𝑟 adjusted according to hint ℎ.
# Input: Boolean ℎ, 𝑟 ∈ ℤ𝑞.
# Output: 𝑟1 ∈ ℤ with 0 ≤ 𝑟1 ≤ 𝑞−1/2 gamma2.
def UseHint(gamma2,h,r):
    m=(params.MLDSA_Q-1)//(2*gamma2)
    r1,r0=Decompose(gamma2,r)
    # print(hex(r),hex(r1),hex(r0))
    if h==1 and r0>0:
        if r1==m-1:
            # print( hex(0) )
            return 0  
        else:
            # print( hex(r1+1) )
            return r1+1
    elif h==1 and r0<0:
        if r1==0:
            # print( hex(m-1) )
            return m-1
        else:
            # print( hex(r1-1) )
            return r1-1
    # print( hex(r1) )
    return r1

def UseHints_vec(k,gamma2,h,r):
    r1=[[0 for i in range(params.MLDSA_N)] for j in range(k)]
    for i in range(k):
        for j in range(params.MLDSA_N):
            r1[i][j]=UseHint(gamma2,h[i][j],r[i][j])
    return r1


if __name__ == '__main__':
    print("Testing Power2Round() function...")
    r=9898988
    r1,r0=Power2Round(r)
    if r1*8192+r0==r%8380417:
        print("Test passed.")
    else:
        print("Test failed.")  

    print("Testing Decompose() function...")
    gamma2=(params.MLDSA_Q-1)//32
    flag=True
    for r in range(0,params.MLDSA_Q+200,100):
        r1,r0=Decompose(gamma2,r)
        if (r1*2*gamma2+r0)%params.MLDSA_Q!=r%params.MLDSA_Q:
            flag=False
            print(r,r1,r0)
            break
    if flag:
        print("Test passed.")
    else:
        print("Test failed.")
