import subprocess
import RPi.GPIO as gp
gp.setmode(gp.BOARD)
gp.setup(35, gp.IN)
import time
while 1:
    val = gp.input(35)
    print(val)
    if val == 1:
        print("shutting down")
        subprocess.call("sudo bash -c 'shutdown -h now'", shell=True)
        print("shut down called")
    time.sleep(1)
