import serial
import time
from vlcclient import VLCClient
from pathlib import Path


def distance_to_pulsewidth(distance):
    return int(round(distance * 58.))


def send_max_pulsewidth(distance, arduino):
    pulsewidth = distance_to_pulsewidth(distance)
    arduino.write(pulsewidth >> 8) # Send first byte
    arduino.write(pulsewidth & 0xff) # Send secound byte


def get_current_distance(arduino):
    arduino.write(b'n') # Send a request
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
        self.vlc.connect()

    def play_active(self):
        self._play_videofile(self.active_video_file)


    def enqueue_idle_video(self):
        self.vlc.enqueue(self.idle_video_file)


    def _play_videofile(self, videofile, loop = False):
        print('Now playing videofile', videofile)
        self.vlc.add(videofile)
        self.vlc.set_fullscreen(True)
        #if loop:
        #    self.vlc.loop()


def _main():
    # Trigger settings
    max_distance = 400
    trigger_distance = 50  # distance in centimeters
    wait_time = 1 # general wait time between samples in sec
    wait_after_trigger = 60 # wait time between video activations


    # COM settings
    COM = '/dev/cu.usbmodem14511'
    arduino = serial.Serial(COM)
    send_max_pulsewidth(max_distance, arduino)


    # VLC settings
    
    active_video_file = '/Users/atlsel/Dropbox/python/motionvlc/Netflix_Innocents_test_03.mp4'
    idle_video_file = '/Users/atlsel/Dropbox/python/motionvlc/bv.mp4'
    vlc_player = VLC(active_video_file, idle_video_file)


    # Log settings
    logfolder = Path('log')
    logfolder.mkdir(parents = True, exist_ok = True)
    logfile = logfolder / f'log - {time.strftime(format("%d %b %Y"))}.txt'
    triggercount = 0


    while True:
        distance = get_current_distance(arduino)
        print('distance read', distance)
        if distance != -1.:
            if distance < trigger_distance:
                triggercount += 1
                update_logfile(logfile, f'{time.strftime(format("%d %b %Y %H:%M:%S"))} - {triggercount}\n')
                vlc_player.play_active()
                vlc_player.enqueue_idle_video()
                time.sleep(wait_after_trigger)
                arduino.flush()
        time.sleep(wait_time)


if __name__ == '__main__':
    _main()
