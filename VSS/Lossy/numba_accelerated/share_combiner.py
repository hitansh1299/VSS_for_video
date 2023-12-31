import numpy as np
import matplotlib.pyplot as plt
import skimage.io as io
# from skimage.measure import block_reduce
from numba import jit, prange
from numpy.typing import NDArray

@jit(nopython=True, cache=True, parallel=True)
def __block_reduce_add__(img: np.ndarray, block_size: tuple):
    x = np.zeros((img.shape[0]//block_size[0], img.shape[1]//block_size[1]), dtype=np.uint16)
    for i in prange(x.shape[0]):
        for j in prange(x.shape[1]):
            x[i][j] = np.sum(img[i:i+block_size[0], j:j+block_size[1]])
            j += block_size[1]
        i += block_size[0]
        
    return x.astype(np.uint8)


@jit(nopython=True, cache=True, parallel=True)
def __block_reduce_or__(img: np.ndarray, block_size: tuple):
    x = np.zeros((img.shape[0]//block_size[0], img.shape[1]//block_size[1]))
    for i in prange(x.shape[0]):
        for j in prange(x.shape[1]):
            x[i][j] =   img[i * block_size[0]][j * block_size[1]] | \
                        img[i * block_size[0] + 1][j * block_size[1]] | \
                        img[i * block_size[0]][j * block_size[1] + 1] | \
                        img[i * block_size[0] + 1][j * block_size[1] + 1]
            
    return x.astype(np.uint16)

@jit(nopython=True, cache=True)
def block_reduce_add(img: np.ndarray, block_size: tuple) -> NDArray[np.uint16]:
    result = __block_reduce_add__(img, block_size)
    return result

@jit(nopython=True, cache=True)
def block_reduce_or(img: np.ndarray, block_size: tuple) -> NDArray[np.uint16]:
    result = __block_reduce_or__(img, block_size)
    return result

@jit(nopython=True, cache=True)
def denoise_image(img: np.ndarray):
    denoised = block_reduce_or(img, (2,2))
    return denoised

'''
    Exapnds the compressed image into a 3 channel image (RGB)
    RGB -> Gray Scale, in the ratio 2:3:3, as per this paper: https://www.researchgate.net/publication/269300186_Legibility_of_Web_Page_on_Full_High_Definition_Display
'''
@jit(parallel=True, nopython=True, cache=True)
def expand(compressed_img: np.ndarray):
    img = np.zeros((compressed_img.shape[0], compressed_img.shape[1], 3))
    img[:,:,0] = (compressed_img & 0b11000000)
    img[:,:,1] = (compressed_img & 0b00111000) << 2 
    img[:,:,2] = (compressed_img & 0b00000111) << 5
 
    return img.astype(np.uint8)

@jit(parallel=True, nopython=True, cache=True)
def expand_16bit(compressed_img: np.ndarray):
    # compressed_img = compressed_img.astype(np.uint8)
    img = np.zeros((compressed_img.shape[0], compressed_img.shape[1], 3), dtype=np.uint16)
    img[:,:,0] = (compressed_img & 0b1111100000000000)
    img[:,:,1] = (compressed_img & 0b0000011111100000) << 5 
    img[:,:,2] = (compressed_img & 0b0000000000011111) << 11
    img =  img >> 8
    return img.astype(np.uint8)

@jit(nopython=True, cache=True, parallel=True)
def __combine_shares__(share1: np.ndarray, share2: np.ndarray):
    combined_share = np.bitwise_and(share1, share2) 
    combined_share = denoise_image(combined_share).astype(np.uint8)
    combined_share = expand(combined_share)
    return combined_share

@jit(nopython=True, cache=True, parallel=True)
def __combine_shares_16_bit__(share1: np.ndarray, share2: np.ndarray):
    combined_share = np.bitwise_and(share1, share2) 
    combined_share = denoise_image(combined_share).astype(np.uint16)
    combined_share = expand_16bit(combined_share)
    return combined_share


def combine_shares(share1: np.ndarray, share2: np.ndarray, verbose=True, high_res = False):
    # print('combining shares')
    if high_res:
        combined_share = __combine_shares_16_bit__(share1, share2)
    else:
        combined_share = __combine_shares__(share1, share2)
    if verbose:
        plt.imshow(combined_share)
        plt.show()
    return combined_share