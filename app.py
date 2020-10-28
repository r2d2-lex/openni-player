from PyQt5 import QtWidgets
from openni import openni2
import numpy as np
import cv2
import mydesign
import sys

ESCAPE = 27
WAIT_KEY_TIMEOUT = 20
OPENNI_FOLDER_PATH = r'./OpenNI-Linux-x64-2.3/Redist'


class MyWindow(QtWidgets.QMainWindow, mydesign.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btnOpen.clicked.connect(self.browse_folder)
        self.movie_slider.sliderPressed.connect(self.slider_pressed)
        self.movie_slider.sliderMoved.connect(self.slider_moved)
        self.movie_slider.sliderReleased.connect(self.slider_released)
        self.btnFrameForward.clicked.connect(self.frame_forward)
        self.btnFrameBack.clicked.connect(self.frame_back)
        self.btnPlayPause.clicked.connect(self.play_pause)
        self.exit_app = False
        self.frame_index = 0
        self.new_frame_index = 0
        self.frame_max_count = 0
        self.new_position = False
        self.pause_flag = False
        self.player = None

    def reset_vars(self):
        self.frame_index = 0
        self.new_frame_index = 0
        self.frame_max_count = 0
        self.new_position = False
        self.pause_flag = False
        self.player = None

    def slider_pressed(self):
        self.pause_flag = True

    def slider_released(self):
        self.pause_flag = True

    def slider_moved(self):
        self.new_index_playback(self.movie_slider.value())

    def frame_forward(self):
        self.new_index_playback(self.frame_index)

    def frame_back(self):
        self.new_index_playback(self.frame_index - 2)

    def play_pause(self):
        if self.frame_index >= self.frame_max_count:
            self.new_index_playback(0)
        self.pause_flag = not self.pause_flag

    def new_index_playback(self, value):
        if value < 0:
            value = 0
        if value >= self.frame_max_count:
            value = self.frame_max_count
        self.new_frame_index = value
        self.new_position = True

    def browse_folder(self):
        path = '.'
        self.listWidget.clear()
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Выберите файл', path, 'ONI (*.oni)')[0]
        if filename:
            self.reset_vars()
            self.listWidget.addItem(filename)
            dev = openni_init(filename)
            depth_stream, color_stream = self.get_streams(dev)
            self.openni_playback(depth_stream, color_stream)

    def openni_playback(self, depth_stream, color_stream):
        self.seek_playback(depth_stream, color_stream)
        while True:
            def new_playback(start_index=0, paused=False):
                self.frame_index = start_index
                self.seek_playback(depth_stream, color_stream, start_index)
                self.pause_flag = paused
                return

            key = cv2.waitKey(WAIT_KEY_TIMEOUT) & 0xFF
            if key == ord(' '):
                self.play_pause()
            if key == ESCAPE or self.exit_app:
                break

            if self.new_position:
                new_playback(self.new_frame_index, False)

            if self.frame_index > self.frame_max_count+1:
                self.new_index_playback(self.frame_max_count)
                continue

            if not self.pause_flag:
                self.frame_count_label.setText(str(self.frame_index))
                self.movie_slider.setValue(self.frame_index)

                depth_frame = depth_stream.read_frame()
                color_frame = color_stream.read_frame()
                depth_array, color_array = prepare_arrays(depth_frame, color_frame)
                cv2.imshow('Depth', depth_array)
                cv2.imshow("Color", color_array)
                self.frame_index += 1

                if self.new_position:
                    self.new_position = False
                    self.pause_flag = True
            else:
                continue
        return

    def seek_playback(self, depth_stream, color_stream, frame_index=0):
        try:
            self.player.seek(color_stream, frame_index)
            self.player.seek(depth_stream, frame_index)
        except Exception as err:
            print('Ошибка Seek: ', err)
            sys.exit()
        return

    def get_streams(self, dev):
        self.player = openni2.PlaybackSupport(dev)
        depth_stream = dev.create_depth_stream()
        color_stream = dev.create_color_stream()
        depth_stream.start()
        color_stream.start()
        self.frame_max_count = depth_stream.get_number_of_frames()
        # print('Общее кол-во фреймов: ', self.frame_max_count)
        self.movie_slider.setRange(0, self.frame_max_count)
        return depth_stream, color_stream

    def closeEvent(self, event):
        cv2.destroyAllWindows()
        openni2.unload()
        self.exit_app = True


def openni_init(filename):
    openni2.initialize(OPENNI_FOLDER_PATH)
    dev = openni2.Device.open_file(filename.encode('utf-8'))
    # print('Инфо: {}'.format(dev.get_device_info()))
    return dev


def prepare_arrays(frame_depth, frame_color):
    depth_divider = 5000.  # depth_divider = 2300.
    frame_depth_data = frame_depth.get_buffer_as_uint16()
    frame_color_data = frame_color.get_buffer_as_uint8()
    depth_array = np.ndarray((frame_depth.height, frame_depth.width),
                             dtype=np.uint16,
                             buffer=frame_depth_data) / depth_divider
    color_array = np.ndarray((frame_color.height, frame_color.width, 3),
                             dtype=np.uint8,
                             buffer=frame_color_data)
    color_array = cv2.cvtColor(color_array, cv2.COLOR_BGR2RGB)
    return depth_array, color_array


def main():
    app = QtWidgets.QApplication([])
    application = MyWindow()
    application.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
