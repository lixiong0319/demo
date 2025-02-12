import cv2
import numpy as np
import ffmpeg
import subprocess

def calculate_psnr(original_video_path, distorted_video_path):
    #打开原始视频和失真视频
    original_cap = cv2.VideoCapture(original_video_path)
    distorted_cap = cv2.VideoCapture(distorted_video_path)

    psnr_values = []

    while True:
        ret_original, frame_original = original_cap.read()
        ret_distorted, frame_distorted = distorted_cap.read()

        if not ret_original or not ret_distorted:
            break

        #计算PSNR
        psnr = cv2.PSNR(frame_original, frame_distorted)
        psnr_values.append(psnr)

    original_cap.release()
    distorted_cap.release()

    if psnr_values:
        average_psnr = np.mean(psnr_values)
        return average_psnr
    else:
        return None
    
def calculate_ssim(original_video_path, distorted_video_path):
    #打开原始视频和失真视频
    original_cap = cv2.VideoCapture(original_video_path)
    distorted_cap = cv2.VideoCapture(distorted_video_path)

    ssim_values = []

    while True:
        ret_original, frame_original = original_cap.read()
        ret_distorted, frame_distorted = distorted_cap.read()

        if not ret_original or not ret_distorted:
            break

        #将帧转换为灰度图
        gray_original = cv2.cvtColor(frame_original, cv2.COLOR_BGR2GRAY)
        gray_distorted = cv2.cvtColor(frame_distorted, cv2.COLOR_BGR2GRAY)

        #计算SSIM
        from skimage.metrics import structural_similarity as ssim
        s = ssim(gray_original, gray_distorted)
        ssim_values.append(s)

    original_cap.release()
    distorted_cap.release()

    if ssim_values:
        average_ssim = np.mean(ssim_values)
        return average_ssim
    else:
        return None
    
def calculate_vmaf(origin_video_path, distorted_video_path):
    try:
        #构建FFmpeg命令
        command = [
            'ffmpeg',
            '-i', origin_video_path,
            '-i', distorted_video_path,
            '-lavfi', 'libvmaf=model_path=vmaf_v0.6.1.json:log_path=vmaf_log.json:log_fmt=json',
            '-f', 'null', '-'
        ]

        #执行ffmpeg命令
        result = subprocess.run(command, capture_output=True, text=True)

        #读取VMAF日志文件
        import json
        with open('vmaf_log.json', 'r') as f:
            vmaf_log = json.load(f)

        vmaf_scores = [float(frame['metrics']['vmaf']) for frame in vmaf_log['frames']]
        average_vmaf = np.mean(vmaf_scores)
        return average_vmaf
    except Exception as e:
        print(f"Error calculating VMAF: {e}")
        return None

if __name__ == "__main__":
    original_video = r'C:\Users\86188\Desktop\wz_project\study_ffmpeg\ffmpeg_test\origin/test_video_1.mp4'
    distorted_video = r'C:\Users\86188\Desktop\wz_project\study_ffmpeg\ffmpeg_test\origin/test_video_1_crf-36.mp4'

    psnr = calculate_psnr(original_video, distorted_video)
    print(f"PSNR: {psnr}")
    ssim = calculate_ssim(original_video, distorted_video)
    print(f"SSIM: {ssim}")
    vmaf = calculate_vmaf(original_video, distorted_video)
    print(f"VMAF: {vmaf}")

    
    
    

