import sys
import cv2
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QSlider
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.cap = None
        self.playing = False
        self.total_frames = 0
        self.current_frame = 0

        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def initUI(self):
        layout = QVBoxLayout()

        #选择文件按钮
        self.select_button = QPushButton('选择文件', self)
        self.select_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_button)

        #视频显示按钮
        self.video_label = QLabel(self)
        layout.addWidget(self.video_label)

        #暂停/播放按钮
        self.play_pause_button = QPushButton('播放', self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setEnabled(False)
        layout.addWidget(self.play_pause_button)

        #快进按钮
        self.forward_button = QPushButton('快进', self)
        self.forward_button.clicked.connect(self.forward)
        self.forward_button.setEnabled(False)
        layout.addWidget(self.forward_button)

        #快退按钮
        self.backward_button = QPushButton('快退', self)
        self.backward_button.clicked.connect(self.backward)
        self.backward_button.setEnabled(False)
        layout.addWidget(self.backward_button)

        #进度条
        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setValue(0)
        self.progress_slider.sliderMoved.connect(self.set_frame)
        self.progress_slider.setEnabled(False)
        layout.addWidget(self.progress_slider)

        self.setLayout(layout)
        self.setWindowTitle('Video_Player')
        self.show()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择视频文件', '', '视频文件 (*.mp4 *avi)')
        if file_path:
            if self.cap is not None:
                self.cap.release()
            self.cap = cv2.VideoCapture(file_path)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_frame = 0
            self.progress_slider.setRange(0, self.total_frames - 1)
            self.play_pause_button.setEnabled(True)
            self.forward_button.setEnabled(True)
            self.backward_button.setEnabled(True)
            self.progress_slider.setEnabled(True)

            #获取视频的原始宽度和高度
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) 
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            #设置显示视频的标签大小为视频的原始大小
            self.video_label.setFixedSize(width - 300 , height - 500)
    
    def toggle_play_pause(self):
        if self.playing:
            self.playing = False
            self.timer.stop()
            self.play_pause_button.setText('播放')
        else:
            self.playing = True
            self.timer.start(30)
            self.play_pause_button.setText('暂停')

    def update_frame(self):
        if self.cap.isOpened() and self.playing:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.progress_slider.setValue(self.current_frame)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                #self.video_label.setPixmap(pixmap.scaled(self.video_label.width(),self.video_label.height()))
                self.video_label.setPixmap(pixmap)
            else:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame = 0
                self.progress_slider.setValue(0)
                self.playing = False
                self.timer.stop()
                self.play_pause_button.setText('播放')
    
    def forward(self):
        if self.cap.isOpened():
            new_frame = min(self.current_frame + 10, self.total_frames - 1)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
            self.current_frame = new_frame
            self.progress_slider.setValue(new_frame)
            self.update_frame()

    def backward(self):
        if self.cap.isOpened():
            new_frame = max(self.current_frame - 10, 0)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
            self.current_frame = new_frame
            self.progress_slider.setValue(new_frame)
            self.update_frame()

    def set_frame(self, value):
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)
            self.current_frame = value
            self.update_frame()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    sys.exit(app.exec())

