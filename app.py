from PyQt5 import QtWidgets
from openni import openni2
import numpy as np
import cv2
import mydesign
import sys

ESCAPE = 27


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

    def reset_vars(self):
        self.frame_index = 0
        self.new_frame_index = 0
        self.frame_max_count = 0
        self.new_position = False
        self.pause_flag = False

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
        self.pause_flag = not self.pause_flag

    def new_index_playback(self, value):
        value = abs(value)
        self.new_frame_index = value
        self.new_position = True

    def browse_folder(self):
        path = '.'
        self.listWidget.clear()
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Выберите файл', path, 'ONI (*.oni)')[0]
        if filename:
            cv2.destroyAllWindows()
            self.reset_vars()
            self.listWidget.addItem(filename)
            dev = openni_init(filename)
            depth_frames, color_frames = self.read_frames(dev)
            self.openni_playback(depth_frames, color_frames)

    def openni_playback(self, depth_frames, color_frames):
        frame_generator = frame_gen(depth_frames, color_frames)
        while True:
            def new_generator(start_index=0, paused=False):
                nonlocal frame_generator
                self.frame_index = start_index
                frame_generator = frame_gen(depth_frames, color_frames, start_index)
                self.pause_flag = paused
                return

            key = cv2.waitKey(20) & 0xFF
            if key == ord(' '):
                self.play_pause()
            if key == ESCAPE or self.exit_app:
                break

            if self.frame_index > self.frame_max_count:
                print('Повтор воспроизведения...')
                new_generator(0, True)
                continue

            if self.new_position:
                new_generator(self.new_frame_index, False)

            if not self.pause_flag:
                try:
                    depth_frame, color_frame = next(frame_generator)
                except StopIteration:
                    print('Повтор воспроизведения...')
                    new_generator(0, True)
                    continue

                self.frame_count_label.setText(str(self.frame_index))
                self.movie_slider.setValue(self.frame_index)
                depth_array, color_array = prepare_arrays(depth_frame, color_frame)
                cv2.imshow('Depth', depth_array)
                cv2.imshow("Color", color_array)
                self.frame_index += 1

                if self.new_position:
                    self.new_position = False
                    self.pause_flag = True
            else:
                continue

        cv2.destroyAllWindows()
        return

    def read_frames(self, dev):
        depth_frames = []
        color_frames = []
        depth_stream = dev.create_depth_stream()
        color_stream = dev.create_color_stream()
        depth_stream.start()
        color_stream.start()

        playback = openni2.PlaybackSupport(dev)
        playback.set_speed(100)

        self.frame_max_count = depth_stream.get_number_of_frames()
        print('Общее кол-во фреймов: ', self.frame_max_count)
        self.movie_slider.setRange(0, self.frame_max_count)
        for _ in range(self.frame_max_count):
            depth_frames.append(depth_stream.read_frame())
            color_frames.append(color_stream.read_frame())
        depth_stream.stop()
        color_stream.stop()
        return depth_frames, color_frames

    def closeEvent(self, event):
        self.exit_app = True


def openni_init(filename):
    openni2.initialize()
    dev = openni2.Device.open_file(filename.encode('utf-8'))
    print('Инфо: {}'.format(dev.get_device_info()))
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


def frame_gen(depth_frames, color_frames, index=0):
    max_frames = len(depth_frames)
    for start_pos in range(index, max_frames):
        try:
            depth_frame = depth_frames[start_pos]
            color_frame = color_frames[start_pos]
        except IndexError as err:
            print('Index error: ', err)
            exit()
        yield depth_frame, color_frame


def main():
    app = QtWidgets.QApplication([])
    application = MyWindow()
    application.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
