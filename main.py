import numpy as np
import cv2 as cv
import os

def init_perception_windows(img, r):
    """
    生成感知窗口
    :param r: 卷积核半径
    :param img: 图像
    """
    length, width, cin = img.shape
    # 生成图像引导窗口集合
    windows = [[[list() for i in range(cin)] for j in range(width)] for k in range(length)]
    # 图像扩充
    image_target = cv.copyMakeBorder(img, r, r, r, r, cv.BORDER_DEFAULT)
    for c in range(cin):
        for i in range(r, length + r):
            for j in range(r, width + r):
                windows[i - r][j - r][c] = init_perception_window(image_target, (i, j, c), r)
    return windows


def init_perception_window(img, location, r):
    """
    生成某个像素位置的单个感知窗口
    :param img: 输入图像
    :param location: 目标像素点位置（RGB格式）
    :param r:卷积核半径
    :return: perception_window 该像素点对应的高斯感知窗口
    """
    # 参数
    k = 0.1

    x = location[0]
    y = location[1]
    c = location[2]
    center_val = img[x][y][c]
    gamma = np.abs(img[x - r:x + r + 1, y - r:y + r + 1, c] - center_val)
    perception_window = np.where(gamma <= 255 * k, 1, 0)
    return perception_window


def init_gauss_filter(r, sigma):
    """
    初始化一个高斯滤波器，其中高斯半径为r，标准差为σ
    :param r: 卷积核半径
    :param sigma: 高斯空间滤波参数
    :return: 高斯空间滤波器卷积核
    """
    d = 2 * r + 1
    core = np.zeros((d, d))
    center = np.array([r, r])
    for i in range(d):
        for j in range(d):
            location = np.array([i, j])
            core[i, j] = np.exp(-((np.linalg.norm(location - center) ** 2) / (2 * (sigma ** 2))))
    return core


def guide_gauss_blur(image, windows, r, sigma):
    """
    引导高斯滤波/模糊 GGF
    :param sigma: 高斯空间滤波核标准差
    :param image: 输入图像
    :param windows: 引导窗口
    :param r: 卷积核半径
    """
    # 图像大小参数
    length, width, cin = image.shape
    # 扩充图像画布
    image_target = cv.copyMakeBorder(image, r, r, r, r, cv.BORDER_DEFAULT)
    # 初始化高斯卷积核
    gauss_filter = init_gauss_filter(r, sigma)
    # 滤波结果图片
    image_ret = np.zeros((length, width, cin))
    for c in range(cin):
        for i in range(r, length + r):
            for j in range(r, width + r):
                guide_filter = gauss_filter * np.array(windows[i - r][j - r][c])
                guide_filter = guide_filter / np.sum(guide_filter)
                image_ret[i - r, j - r, c] = np.sum(guide_filter * image_target[i - r:i + r + 1, j - r: j + r + 1, c])
    return np.around(image_ret).astype(np.uint8)


if __name__ == '__main__':
    # 参数
    kernel_GS_r = 2
    kernel_GS_d = 2 * kernel_GS_r + 1
    kernel_GGF_r = 7
    kernel_GGF_d = 2 * kernel_GGF_r + 1
    sigma_GS = 3.0
    sigma_GGF = 3.0

    # 读取测试图像
    file_name = input("input image name:")
    file_format = input("input image format:")
    img_test = cv.imread("img/" + file_name + "." + file_format)
    # 高斯滤波
    img_GS = cv.GaussianBlur(img_test, (kernel_GS_d, kernel_GS_d), sigma_GS)
    # 生成强度感知窗口
    img_GGF_input = np.array(img_test, dtype=int)
    perception_windows = init_perception_windows(img_GGF_input, r=kernel_GGF_r)

    # 引导高斯滤波
    img_GGF = guide_gauss_blur(img_GGF_input, perception_windows, r=kernel_GGF_r, sigma=sigma_GGF)

    # 结果图片输出
    dir_name = "output/" + file_name
    os.mkdir(dir_name)
    cv.imwrite(dir_name + "/before_GS." + file_format, img_test)
    cv.imwrite(dir_name + "/after_GS." + file_format, img_GS)
    cv.imwrite(dir_name + "/after_GGF." + file_format, img_GGF)
