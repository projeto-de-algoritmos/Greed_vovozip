from __future__ import annotations
import heapq

class Node:
    def __init__(self, value:int|None, probability:int, left:Node|None=None, right:Node|None=None) -> None:
        self.value = value
        self.probability = probability
        self.left = left
        self.right = right

    def from_codes(codes:dict[int, str]) -> Node:
        root = Node(value=None, probability=0)
        for value, code in codes.items():
            node = root
            for c in code:
                if c == '0':
                    if node.left is None:
                        node.left = Node(value=None, probability=0)
                    node = node.left
                elif c == '1':
                    if node.right is None:
                        node.right = Node(value=None, probability=0)
                    node = node.right
            node.value = value

        return root
    
    def __lt__(self, other:Node) -> bool:
        return self.probability < other.probability

def get_probability(data:bytes) -> dict[int, int]:
    probabilities:dict[int, int] = {}
    for value in data:
        if value in probabilities:
            probabilities[value] += 1
        else:
            probabilities[value] = 1

    return probabilities

# Retorna a raíz da árvore de códigos
def get_huffman_codes_tree(probabilities:dict[int, int]) -> Node:
    heap:list[Node] = []

    for value, probability in probabilities.items():
        heapq.heappush(heap, Node(value, probability))

    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
    
        heapq.heappush(heap, Node(None, node1.probability + node2.probability, left=node1, right=node2))
    
    return heap[0]

def get_codes(root:Node) -> dict[int, str]:
    codes:dict[int, str] = {}
    __get_codes_r(root, codes)
    return codes

def __get_codes_r(node:Node, codes:dict[int, str], current_code:str='') -> None:
    if node.value is not None:
        codes[node.value] = current_code
    else:
        __get_codes_r(node.left, codes, current_code + '0')
        __get_codes_r(node.right, codes, current_code + '1')

def compress(data:bytes) -> tuple[str, dict[int, str], dict[int, int]]:
    probabilities = get_probability(data)
    codes_tree = get_huffman_codes_tree(probabilities)
    codes = get_codes(codes_tree)
    compressed_bits = ''

    for value in data:
        compressed_bits += codes[value]

    return compressed_bits, codes, probabilities

def write_compressed_file(compressed_bits:str, codes:dict[int, str], output_file:str):
    header = bytearray()
    for value, code in codes.items():
        header.append(value)
        header.append(len(code))
        for c in code:
            header.append(ord(c))
    header_size = len(header)

    remaining_zeroes = 0
    if len(compressed_bits) % 8 != 0:
        remaining_zeroes = 8 - len(compressed_bits) % 8
        compressed_bits += '0' * remaining_zeroes

    compressed_bytes = bytearray()
    for i in range(0, len(compressed_bits), 8):
        byte = compressed_bits[i : i+8]
        compressed_bytes.append(int(byte, 2))

    with open(output_file, 'wb') as f:
        f.write(header_size.to_bytes(4, 'big'))
        f.write(remaining_zeroes.to_bytes(1, 'big'))
        f.write(header)
        f.write(compressed_bytes)

def write_codes(codes:dict[int, str], probabilities:dict[int, int]):
    codes_list = [(value, code, probabilities[value]) for value, code in codes.items()]
    codes_list.sort(key=lambda x: x[2], reverse=True)

    with open('codes.txt', 'w') as fcodes:
        acl = sum(len(code) * prob for value, code, prob in codes_list) / sum(probabilities.values())
        fcodes.write(f'Average Codeword Length = {acl:.3f} bits/symbol\n')

        for value, code, prob in codes_list:
            fcodes.write(f"\'{chr(value)}\'" if 32 <= value <= 126 else f'{value}')
            fcodes.write(f' ({prob}) : {code}\n')

def decompress(compressed_file) -> bytearray:
    with open(compressed_file, 'rb') as bfile:
        header_size = int.from_bytes(bfile.read(4), 'big')
        remaining_zeroes = int.from_bytes(bfile.read(1), 'big')
        codes:dict[int, str] = {}

        while bfile.tell() < header_size + 5:
            value = int.from_bytes(bfile.read(1), 'big')
            size = int.from_bytes(bfile.read(1), 'big')
            code = bfile.read(size).decode('ascii')
            codes[value] = code

        compressed_data = bfile.read()
        root = Node.from_codes(codes)
        node = root
        uncompressed_data = bytearray()

        for i, byte in enumerate(compressed_data):
            bits = bin(byte)[2:]
            bits = '0' * (8 - len(bits)) + bits

            for ib, b in enumerate(bits):
                if i == len(compressed_data) - 1 and ib == 8 - remaining_zeroes:
                    break
                if b == '0':
                    node = node.left
                if b == '1':
                    node = node.right
                if node.value is not None:
                    uncompressed_data.append(node.value)
                    node = root

    return uncompressed_data

def write_decompressed_data(data, output_file):
    with open(output_file, 'wb') as f:
        f.write(data)
