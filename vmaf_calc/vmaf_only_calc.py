import cv2
import numpy as np
from sklearn.linear_model import LinearRegression  #简单使用线性回归作为模型

#简单的特征提取函数
def extract_features(frame):
    #提高亮度特征
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    return [mean_brightness]

#计算特征差异
def calculate_feature_differences(original_frame, distorted_frame):
    original_features = extract_features(original_frame)
    distorted_features = extract_features(distorted_frame)
    differences = [abs(o -d) for o, d in zip(original_features, distorted_features)]
    return differences

#简化的模型预测
def predict_vmaf(feature_differences):
    #假设已经有训练好的模型
    model = LinearRegression()
    #实际需要真实训练的数据
    X_train = np.array([[0.1], [0.2], [0.3]])
    y_train = np.array([80, 70, 60])
    model.fit(X_train, y_train)
    feature_differences = np.array(feature_differences).reshape(1, -1)
    vmaf_score = model.predict(feature_differences)
    return vmaf_score[0]

#计算视频的平均VMAF
def calculate_video_vmaf(original_video_path, distorted_video_path):
    original_cap = cv2.VideoCapture(original_video_path)
    distorted_cap = cv2.VideoCapture(distorted_video_path)

    vmaf_scores = []

    while True:
        ret_original, frame_original = original_cap.read()
        ret_distorted, frame_distorted = distorted_cap.read()

        if not ret_original or not ret_distorted:
            break

        feature_differences = calculate_feature_differences(frame_original, frame_distorted)
        vmaf_score = predict_vmaf(feature_differences)
        vmaf_scores.append(vmaf_score)

    original_cap.release()
    distorted_cap.release()

    if vmaf_scores:
        average_vmaf = np.mean(vmaf_scores)
        return average_vmaf
    else:
        return None
    
if __name__ == "__main__":
    original_video = r'C:\Users\86188\Desktop\wz_project\study_ffmpeg\ffmpeg_test\origin/test_video_1.mp4'
    distorted_video = r'C:\Users\86188\Desktop\wz_project\study_ffmpeg\ffmpeg_test\origin/test_video_1_crf-36.mp4'
    vmaf = calculate_video_vmaf(original_video, distorted_video)
    print(f"VMAF: {vmaf}")