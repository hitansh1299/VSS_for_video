import matplotlib.pyplot as plt
import skimage.io as io
import numpy as np
from numba import jit, vectorize
import numba as nb
import share_combiner
BITPLANE_COUNT = 16

'''
Using arithmetic instead of bitwise operations because python has a "fast track" for arithmetic operations
'''
@jit(nopython=True)
def color_to_gray(img: np.ndarray):
    img = img.astype(np.uint16)
    gray_img = np.zeros(img.shape, dtype=np.uint16)
    get_first_5_bits = lambda x: x // 0b1000
    gray_img = get_first_5_bits(img[:, :, 0]) * 2048 + get_first_5_bits(img[:, :, 1]) * 64 + get_first_5_bits(img[:, :, 2]) * 2
    # plt.imshow(gray_img, cmap='gray')
    return gray_img

@vectorize(nopython=True)
def get_bitplane(img: np.ndarray, n: int):
    return (img // 2**n) & 1

@jit(nopython=True)
def create_bitplane_shares(img: np.ndarray):
    shares = {
        0: (np.array([[0,1],[0,1]]), np.array([[1,0],[1,0]])),
        1: (np.array([[1,0],[1,0]]), np.array([[0,1],[0,1]])),
        2: (np.array([[1,0],[1,0]]), np.array([[1,0],[1,0]])),
        3: (np.array([[0,1],[0,1]]), np.array([[0,1],[0,1]]))
    }   
    img = img*2 + np.random.randint(0, 2, size=img.shape)
    share1 = np.zeros((img.shape[0] * 2, img.shape[1] * 2), dtype=np.uint16)
    share2 = np.zeros((img.shape[0] * 2, img.shape[1] * 2), dtype=np.uint16)
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            share1[i*2:i*2+2, j*2:j*2+2] = shares[img[i][j]][0]
            share2[i*2:i*2+2, j*2:j*2+2] = shares[img[i][j]][1]
    return share1.astype(np.uint16), share2.astype(np.uint16)

#Broken the function into two parts to make to keep the pure numba functions separate from Matplotlib utils
@jit(nopython=True)
def __generate_shares__(img: np.ndarray):
    img = color_to_gray(img)
    share_image1 = np.zeros(shape=(img.shape[0]*2, img.shape[1]*2), dtype=np.uint16)
    share_image2 = np.zeros(shape=(img.shape[0]*2, img.shape[1]*2), dtype=np.uint16)

    for i in range(BITPLANE_COUNT):
        bitplane = get_bitplane(img, i)
        s1, s2 = create_bitplane_shares(bitplane)
        share_image1 = share_image1 + (s1 * 2**i).astype(np.uint16)
        share_image2 = share_image2 + (s2 * 2**i).astype(np.uint16)
    return share_image1, share_image2

def generate_shares(img: np.ndarray, verbose = False):
    share1, share2 = __generate_shares__(img)
    if verbose:
        img = color_to_gray(img)
        print("orig gray", img[100:120,100:120])
        plt.figure(figsize=(30,160))
        for i in range(BITPLANE_COUNT):
            plt.subplot(3, BITPLANE_COUNT, i+1)
            plt.axis('off')
            plt.xlabel(f'Bitplane {i}')
            plt.imshow(get_bitplane(img, i), cmap='gray')
            plt.subplot(3, BITPLANE_COUNT, i+BITPLANE_COUNT+1)
            plt.axis('off')
            plt.xlabel(f'Bitplane {i}')
            plt.imshow(get_bitplane(share1,i), cmap='gray')
            plt.subplot(3, BITPLANE_COUNT, i+BITPLANE_COUNT*2+1)
            plt.axis('off')
            plt.xlabel(f'Bitplane {i}')
            plt.imshow(get_bitplane(share2,i), cmap='gray')
        plt.show()
        plt.subplot(1,4,1)
        plt.imshow(img, cmap='gray')
        plt.subplot(1,4,2)
        plt.imshow(share1, cmap='gray')
        plt.subplot(1,4,3)
        plt.imshow(share2, cmap='gray')
        plt.subplot(1,4,4)
        combined_share = share_combiner.denoise_image(share1 & share2)
        plt.imshow(combined_share, cmap='gray')
        print("combined share",combined_share[100:120,100:120])
        plt.show()
    return share1, share2


if __name__ == '__main__':
    IMAGE = io.imread('images.jpeg')
    generate_shares(IMAGE, verbose=True)