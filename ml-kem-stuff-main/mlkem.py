# https://words.filippo.io/dispatches/kyber-math/
# https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.203.ipd.pdf

from typing import List, Tuple
import hashlib
import os
from shakestream import ShakeStream
from functools import reduce



ML_KEM_VERSION = 768  # 修改这里切换参数组

if ML_KEM_VERSION == 512:
    K = 2
    ETA1 = 3
    ETA2 = 2
    DU = 10
    DV = 4
elif ML_KEM_VERSION == 768:
    K = 3
    ETA1 = 2
    ETA2 = 2
    DU = 10
    DV = 4
elif ML_KEM_VERSION == 1024:
    K = 4
    ETA1 = 2
    ETA2 = 2
    DU = 11
    DV = 5

N = 256
Q = 3329

def bitrev7(n: int) -> int:
	return int(f"{n:07b}"[::-1], 2)  # gross but it works

# 17 is primitive 256th root of unity mod Q
ZETA = [pow(17, bitrev7(k), Q) for k in range(128)] # used in ntt and ntt_inv
GAMMA = [pow(17, 2*bitrev7(k)+1, Q) for k in range(128)] # used in ntt_mul


# 打印还是，打印一个多项式的系数，采用16进制
def print_ploy(res):
	for i in range(0, 256, 4):
		group = res[i : i+4]  
		hex_str = ' '.join(f'{num:04x}' for num in group)  
		print(hex_str)  
	print('\n')



# can be reused for NTT representatives
def poly256_add(a: List[int], b: List[int]) -> List[int]:
	return [(x + y) % Q for x, y in zip(a, b)]

def poly256_sub(a: List[int], b: List[int]) -> List[int]:
	return [(x - y) % Q for x, y in zip(a, b)]

# naive O(n^2) multiplication algorithm for testing/comparison purposes.
# this is not used for the main impl.
def poly256_slow_mul(a: List[int], b: List[int]) -> List[int]:
	c = [0] * 511

	# textbook multiplication, without carry
	for i in range(256):
		for j in range(256):
			c[i+j] = (c[i+j] + a[j] * b[i]) % Q

	# now for reduction mod X^256 + 1
	for i in range(255):
		c[i] = (c[i] - c[i+256]) % Q
		# we could explicitly zero c[i+256] here, but there's no need...
	
	# ...because we're about to truncate c
	return c[:256]


# by the way, this is O(n logn)
def ntt(f_in: List[int]) -> List[int]:
	f_out = f_in.copy()
	k = 1
	for log2len in range(7, 0, -1):
		length = 2**log2len
		for start in range(0, 256, 2 * length):
			zeta = ZETA[k]
			k += 1
			for j in range(start, start + length):
				t = (zeta * f_out[j + length]) % Q
				f_out[j + length] = (f_out[j] - t) % Q
				f_out[j] = (f_out[j] + t) % Q
	return f_out


# so is this
# def ntt_inv(f_in: List[int]) -> List[int]:
# 	f_out = f_in.copy()
# 	k = 127
# 	for log2len in range(1, 8):
# 		length = 2**log2len
# 		for start in range(0, 256, 2 * length):
# 			zeta = ZETA[k]
			
# 			k -= 1
# 			for j in range(start, start + length):
# 				t = f_out[j]
# 				aa = f_out[j + length] - t
# 				if aa < 0:
# 					aa = aa + 3329
# 				# print(hex(t),hex(f_out[j + length]),hex((t + f_out[j + length]) % 3329 ),hex(aa),hex(zeta))
# 				f_out[j] = (t + f_out[j + length]) % Q
# 				f_out[j + length] = (zeta * (f_out[j + length] - t)) % Q
				
				

# 	for i in range(256):
# 		f_out[i] = (f_out[i] * 3303) % Q  # 3303 == pow(128, -1, Q) 3303

# 	return f_out


def ntt_inv(f_in: List[int]) -> List[int]:
	f_out = f_in.copy()
	k = 127
	for log2len in range(1, 8):
		length = 2**log2len
		for start in range(0, 256, 2 * length):
			zeta = ZETA[k]
			# print(bitrev7(k))
			k -= 1
			
			for j in range(start, start + length):
				t = f_out[j]
				aa = f_out[j + length] - t
				if aa < 0:
					aa = aa + 3329
				# print(hex(t),hex(f_out[j + length]),hex((t + f_out[j + length]) % 3329 ),hex(aa),hex(zeta))
				
				f_out[j] = (t + f_out[j + length]) % Q
				f_out[j + length] = (zeta * (f_out[j + length] - t)) % Q
				f_out[j] = (f_out[j] * 1665) % Q
				f_out[j + length] = (f_out[j + length] * 1665) % Q
			
				

	# for i in range(256):
	# 	f_out[i] = (f_out[i] * 3303) % Q  # 3303 == pow(128, -1, Q) 3303
    

	return f_out



ntt_add = poly256_add  # it's just elementwise addition

# and this is just O(n)
def ntt_mul(a: List[int], b: List[int]) -> List[int]:
	c = []
	for i in range(128):
		a0, a1 = a[2 * i: 2 * i + 2]
		b0, b1 = b[2 * i: 2 * i + 2]
		# if i == 1:
		# 	print(a0,a1,b0,b1,GAMMA[i])
		c.append((a0 * b0 + a1 * b1 * GAMMA[i]) % Q)
		c.append((a0 * b1 + a1 * b0) % Q)
	return c


# crypto functions

def mlkem_prf(eta: int, data: bytes, b: int) -> bytes:
	return hashlib.shake_256(data + bytes([b])).digest(64 * eta)

def mlkem_xof(data: bytes, i: int, j: int) -> ShakeStream:
	# print(hashlib.shake_128(data + bytes([i, j])).digest)
	return ShakeStream(hashlib.shake_128(data + bytes([i, j])).digest)

def mlkem_hash_H(data: bytes) -> bytes:
	return hashlib.sha3_256(data).digest()

def mlkem_hash_J(data: bytes) -> bytes:
	return hashlib.shake_256(data).digest(32)

def mlkem_hash_G(data: bytes) -> bytes:
	return hashlib.sha3_512(data).digest()


# encode/decode logic

def bits_to_bytes(bits: List[int]) -> bytes:
	assert(len(bits) % 8 == 0)
	return bytes(
		sum(bits[i + j] << j for j in range(8))
		for i in range(0, len(bits), 8)
	)

def bytes_to_bits(data: bytes) -> List[int]:
	bits = []
	for word in data:
		for i in range(8):
			bits.append((word >> i) & 1)
	return bits

def byte_encode(d: int, f: List[int]) -> bytes:
	assert(len(f) == 256)
	bits = []
	for a in f:
		for i in range(d):
			bits.append((a >> i) & 1)
	return bits_to_bytes(bits)

def byte_decode(d: int, data: bytes) -> List[int]:
	bits = bytes_to_bits(data)
	return [sum(bits[i * d + j] << j for j in range(d)) for i in range(256)]
 
def compress(d: int, x: List[int]) -> List[int]:
	return [(((n * 2**d) + Q // 2 ) // Q) % (2**d) for n in x]

def decompress(d: int, x: List[int]) -> List[int]:
	return [(((n * Q) + 2**(d-1) ) // 2**d) % Q for n in x]


# sampling

def sample_ntt(xof: ShakeStream):
	res = []
	# print(xof.read(6).hex())
	# a, b, c = xof.read(3)
	# d1 = ((b & 0xf) << 8) | a
	# d2 = c << 4 | b >> 4
	# print(d1,d2)
	while len(res) < 256:
		a, b, c = xof.read(3)
		
		d1 = ((b & 0xf) << 8) | a
		d2 = c << 4 | b >> 4
		if d1 < Q:
			res.append(d1)
		if d2 < Q and len(res) < 256:
			res.append(d2)
	return res


def sample_poly_cbd(eta: int, data: bytes) -> List[int]:
	assert(len(data) == 64 * eta)
	bits = bytes_to_bits(data)
	f = []
	for i in range(256):
		x = sum(bits[2*i*eta+j] for j in range(eta))
		y = sum(bits[2*i*eta+eta+j] for j in range(eta))
		f.append((x - y) % Q)
	# print(bits)
	# print_ploy(f)
	return f


# K-PKE

def kpke_keygen(seed: bytes=None) -> Tuple[bytes, bytes]:
	d = os.urandom(32) if seed is None else seed
	print("seed: ")
	print(d.hex(),"\n")

	d = bytearray.fromhex("5615a4565071763dbef4b9c704158bf07df8ef194bae8ded6cd3d62bf05e8273" + f"0{K}")   # 固定种子，便于测试
	# d = d + bytes([K])
	# print(d.hex(),"\n")


	ghash = mlkem_hash_G(d)   
	rho, sigma = ghash[:32], ghash[32:]

	# print(rho.hex())

    # 矩阵A采样
	ahat = []
	for i in range(K):
		row = []
		for j in range(K):
			row.append(sample_ntt(mlkem_xof(rho, j, i)))
		ahat.append(row)
	# print_ploy(ahat[0][1])
	
	shat = [
		ntt(sample_poly_cbd(ETA1, mlkem_prf(ETA1, sigma, i)))
		for i in range(K)
	]

	# print_ploy(shat[0])  # NTT(s)

	ehat = [
		ntt(sample_poly_cbd(ETA1, mlkem_prf(ETA1, sigma, i+K)))
		for i in range(K)
	]

	# print_ploy(ehat[0])  # NTT(s)


	that = [ # t = a * s + e
		reduce(ntt_add, [
			ntt_mul(ahat[j][i], shat[j])
			for j in range(K)
		] + [ehat[i]])
		for i in range(K)
	]

	# that = [ # t = a * s + e
	# 	reduce(ntt_add, [
	# 		ntt_mul(ahat[j][i], shat[j])
	# 		for j in range(2)
	# 	] )
	# 	for i in range(K)
	# ]

 
	# print_ploy(ahat[3][3])
	# print_ploy(shat[2])
	# print_ploy(that[3]) 

	ek_pke = b"".join(byte_encode(12, s) for s in that) + rho
	# print(ek_pke.hex())

	dk_pke = b"".join(byte_encode(12, s) for s in shat)
	# print(dk_pke.hex())
	return ek_pke, dk_pke


def kpke_encrypt(ek_pke: bytes, m: bytes, r: bytes) -> bytes:
	# print(ek_pke[0:1].hex())
	that = [byte_decode(12, ek_pke[i*384:(i+1)*384]) for i in range(K)]   # 修改，原先不同等级有错误
	rho = ek_pke[-32:]
	# print_ploy(that[0])
	# print(rho.hex())
	# r = bytearray.fromhex("52414e4452414e4452414e4452414e4452414e4452414e4452414e4452414e44")   # 固定种子，便于测试
	# print(r.hex())
    
	# this is identical to as in kpke_keygen
	ahat = []
	for i in range(K):
		row = []
		for j in range(K):
			row.append(sample_ntt(mlkem_xof(rho, i, j)))
		ahat.append(row)
    
	# print_ploy(ahat[0][0])

	rhat = [
		ntt(sample_poly_cbd(ETA1, mlkem_prf(ETA1, r, i)))
		for i in range(K)
	]
	# print("hello")
	# print(r.hex())

	# print_ploy(rhat[0])


	e1 = [
		sample_poly_cbd(ETA2, mlkem_prf(ETA2, r, i+K))
		for i in range(K)
	]

	# print_ploy(e1[0])

	e2 = sample_poly_cbd(ETA2, mlkem_prf(ETA2, r, 2*K))

	u = [ # u = ntt-1(AT*r)+e1
		poly256_add(ntt_inv(reduce(ntt_add, [
			ntt_mul(ahat[i][j], rhat[j]) # note that i,j are reversed here
			for j in range(K)
		])), e1[i])
		for i in range(K)
	]

	# kdd = [ # u = ntt-1(AT*r)+e1
	# 	reduce(ntt_add, [
	# 		ntt_mul(ahat[i][j], rhat[j]) # note that i,j are reversed here
	# 		for j in range(K)
	# 	])
	# 	for i in range(K)
	# ]

	# print_ploy(ahat[0][1])
	# print_ploy(rhat[1])
	# print_ploy(kdd[0])

	mu = decompress(1, byte_decode(1, m))
	# print_ploy(byte_decode(1, m))
	# print(m.hex())


	v = poly256_add(ntt_inv(reduce(ntt_add, [
		ntt_mul(that[i], rhat[i])
		for i in range(K)
	])), poly256_add(e2, mu))
	
	# DFD =  poly256_add(ntt_inv(reduce(ntt_add, [
	# 	ntt_mul(that[i], rhat[i])
	# 	for i in range(K)
	# ])), poly256_add(e2, mu))

	# print_ploy (v)
	# print_ploy (e2)
	# print_ploy (mu)
 



	c1 = b"".join(byte_encode(DU, compress(DU, u[i])) for i in range(K))
	# print_ploy (compress(DU, u[0]))
	# print (c1.hex())
	c2 = byte_encode(DV, compress(DV, v))
	# print (c2.hex())
	return c1 + c2


def kpke_decrypt(dk_pke: bytes, c: bytes) -> bytes:
	# print(c.hex())
	c1 = c[:32*DU*K]
	c2 = c[32*DU*K:]
	# print("c2:")
	# print(c2.hex())
	u = [
		decompress(DU, byte_decode(DU, c1[i*32*DU:(i+1)*32*DU]))
		for i in range(K)
	]
   

	# print_ploy(u[3])
 
    
	v = decompress(DV, byte_decode(DV, c2))
	# print(c2.hex())

	# v = byte_decode(DV, c2)
	# print_ploy(v)
	# print(dk_pke.hex())

	shat = [byte_decode(12, dk_pke[i*384:(i+1)*384]) for i in range(K)]


	# print_ploy(shat[0])

	# NOTE: the comment in FIPS203 seems wrong here?
	# it says "NTT−1 and NTT invoked k times", but I think NTT−1 is only invoked once.
	w = poly256_sub(v, ntt_inv(reduce(ntt_add, [
		ntt_mul(shat[i], ntt(u[i]))
		for i in range(K)
	])))

	# w = ntt_inv(reduce(ntt_add, [
	# 	ntt_mul(shat[i], ntt(u[i]))
	# 	for i in range(K)
	# ]))

    
	# print_ploy(shat[0])
	# print_ploy(ntt(u[0]))
	# print_ploy(w)


	m = byte_encode(1, compress(1, w))
	# print("m:")
	# print(m.hex())

	return m


# KEM time

def mlkem_keygen(seed1=None, seed2=None):
	z = os.urandom(32) if seed1 is None else seed1
	z = bytearray.fromhex("52414e4452414e4452414e4452414e4452414e4452414e4452414e4452414e44")  # 先固定方便测试
	ek_pke, dk_pke = kpke_keygen(seed2)
	ek = ek_pke
	dk = dk_pke + ek + mlkem_hash_H(ek) + z
	print("mlkem_hash_H:") 
	print(mlkem_hash_H(ek).hex())
	return ek, dk


def mlkem_encaps(ek: bytes, m: bytes,seed=None) -> Tuple[bytes, bytes]:
	# TODO !!!! input validation !!!!!!!
	# m = os.urandom(32) if seed is None else seed
	# m = bytearray.fromhex("5468697320697320612064656d6f6e7374726174696f6e206d6573736167652e")  # 先固定方便测试
	ghash = mlkem_hash_G(m + mlkem_hash_H(ek))
	# print(ghash.hex())
	k = ghash[:32]
	r = ghash[32:]
	c = kpke_encrypt(ek, m, r)
	return k, c


def mlkem_decaps(c: bytes, dk: bytes) -> bytes:
	# TODO !!!! input validation !!!!!!!
	dk_pke = dk[:384*K]
	ek_pke = dk[384*K : 768*K + 32]
	h = dk[768*K + 32 : 768*K + 64]
	z = dk[768*K + 64 : 768*K + 96]
	
	mdash = kpke_decrypt(dk_pke, c)
	print("m':")
	print(mdash.hex(),"\n")

	ghash = mlkem_hash_G(mdash + h)
	print("(K',r')':")
	print(ghash.hex(),"\n")

	kdash = ghash[:32]
	rdash = ghash[32:]
	# NOTE: J() has unnecessary second argument in the spec???
	kbar = mlkem_hash_J(z + c)
	print("K—:")
	print(kbar.hex(),"\n")
	cdash = kpke_encrypt(ek_pke, mdash, rdash)
	print("c':")
	print(cdash.hex(),"\n")
	kprime = mlkem_hash_J(z + cdash)
	print("K— —:")
	print(kprime.hex(),"\n")
	if cdash != c:
		# I suppose this branch ought to be constant-time, but that's already out the window with this impl
		#print("did not match") # XXX: what does implicit reject mean? I suppose it guarantees it fails in a not-attacker-controlled way?
		return kbar
	return kdash

if __name__ == "__main__":
	a = list(range(256))
	b = list(range(1024, 1024+256))

	# ntt_res = ntt_inv(ntt_add(ntt(a), ntt(b)))
	# poly_res = poly256_add(a, b)

	# assert(ntt_res == poly_res)

	# ntt_prod = ntt_inv(ntt_mul(ntt(a), ntt(b)))
	# poly_prod = poly256_slow_mul(a, b)

	# assert(ntt_prod == poly_prod)

	# ek_pke, dk_pke = kpke_keygen(b"SEED"*8)

	# msg = b"This is a demonstration message."
	# ct = kpke_encrypt(ek_pke, msg, b"RAND"*8)
	# print("c:")
	# print(ct.hex())
	# print("dk_pke:")
	# print(dk_pke.hex())

	# pt = kpke_decrypt(dk_pke, ct)
	# print(pt.hex())
	# assert(pt == msg)

    # 密钥生成
	ek, dk = mlkem_keygen()
	print("dk:")
	print(dk.hex(),"\n")
	print("ek:")
	print(ek.hex(),"\n")

	# 密钥封装
	m = os.urandom(32)  
	# print("m:")
	# print(m.hex(),"\n")
	m = bytearray.fromhex("5468697320697320612064656d6f6e7374726174696f6e206d6573736167652e")  # 先固定方便测试
	k1, c = mlkem_encaps(ek,m)
	print("K1:")
	print(k1.hex(),"\n")
	print("c:")
	print(c.hex(),"\n")
    
	# 密钥接封装
	k2 = mlkem_decaps(c, dk)
	print("K_prime:")
	print(k2.hex(),"\n")


	# print("decapsulated:", k2.hex())

	# assert(k1 == k2)