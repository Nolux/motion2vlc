import subprocess
import time
from pathlib import Path

import serial

from vlcclient import VLCClient


def distance_to_pulsewidth(distance):
    return int(round(distance * 58.))


def send_max_pulsewidth(distance, arduino):
    pulsewidth = distance_to_pulsewidth(distance)
    arduino.write(pulsewidth >> 8)  # Send first byte
    arduino.write(pulsewidth & 0xff)  # Send secound byte


def get_current_distance(arduino):
    arduino.write(b'n')  # Send a request
    current_distance = float(arduino.readline())
    return current_distance


def update_logfile(filename, content):
    with open(filename, 'a') as file:
        file.write(content)


class VLC:

    def __init__(self, active_video_file, idle_video_file):
        self.active_video_file = active_video_file
        self.idle_video_file = idle_video_file
        self.vlc = VLCClient("::1")
        subprocess.Popen("vlc --intf telnet --telnet-pass admin", shell=True, stdout=subprocess.PIPE)
        time.sleep(2)
        self.vlc.connect()

    def play_active(self):
        self._play_videofile(self.active_video_file)

    def play_idle_video(self):
        self.vlc.add(self.idle_video_file)
        # self.vlc.loop()
        self.vlc.set_fullscreen(True)

    def enqueue_idle_video(self):
        self.vlc.enqueue(self.idle_video_file)

    def rewind_video(self):
        self.vlc.rewind()

    def _play_videofile(self, videofile, loop=False):
        print('Now playing videofile', videofile)
        self.vlc.add(videofile)
        self.vlc.set_fullscreen(True)


def _main():
    # Trigger settings
    max_distance = 400
    trigger_distance = 50  # distance in centimeters
    wait_time = .5  # general wait time between samples in sec
    wait_after_trigger = 60  # wait time between video activations

    # COM settings
    COM = '/dev/ttyACM0'
    arduino = serial.Serial(COM)
    send_max_pulsewidth(max_distance, arduino)

    # VLC settings
    videofolder = Path('motion2vlc')
    active_video_file = videofolder / 'Netflix_Innocents_test_03.mp4'
    idle_video_file = videofolder / 'bv.mp4'
    vlc_player = VLC(active_video_file, idle_video_file)

    # Log settings
    logfolder = Path('motion2vlc/log')
    logfolder.mkdir(parents=True, exist_ok=True)
    logfile = logfolder / f'log - {time.strftime(format("%d %b %Y"))}.txt'
    triggercount = 0

    # Ready VLC
    vlc_player.play_idle_video()

    while True:
        try:
            distance = get_current_distance(arduino)
            print('distance read', distance)
            if distance != -1.:
                if distance < trigger_distance:
                    triggercount += 1
                    update_logfile(logfile, f'{time.strftime(format("%d %b %Y %H:%M:%S"))} - {triggercount}\n')
                    vlc_player.play_active()
                    vlc_player.enqueue_idle_video()
                    if arduino.in_waiting > 0:
                        arduino.read(arduino.in_waiting)  # dump remaining bytes from stream
                    print(f"Waiting til next trigger, {wait_after_trigger} sec")
                    time.sleep(wait_after_trigger)
            #vlc_player.rewind_video()
            time.sleep(wait_time)
        except KeyboardInterrupt:
            arduino.close()
            subprocess.call(['killall vlc'])
            print('killing program')


if __name__ == '__main__':
    _main()
