# AlexaLover
### Connect Alexa with other devices using WeMo protocol

## Summary

Alexa (Amazon Echo) can control 16 supported devices using your voice. These
supported devices can perform multiple actions, using their own protocol.

AlexaLover uses the interaction between Alexa and Belkin devices (WeMo protocol)
to emulate a Belking plug (or light). I used some code from 
[fauxmo](https://github.com/makermusings/fauxmo) (related to connection management).

WeMo devices has only two different states: On and Off. We can use these different states
to turn on lights and turn off. But we can use two send different commands to any device,
for example using the `On` status to select the VGA input for our TV and `Off` for the
HDMI input.

You can tell to Alexa:

`Alexa, turn on The light`

and `The light` device will turn on. Also, you can tell:

`Alexa, turn off The light`

and `The light` device will turn off.

Any WeMo device is a UPnP device. They respond a UPnP discoveries pointing to
their own TCP port to interact with Alexa.

AlexaLove emulates a multiple UPnP devices. For each device, AlexaLove
implements the UDP server to reply the UPnP discoveries, and one TCP port
per device to interact with Alexa.

To do it, AlexaLove uses a configuration file with 4 fields:

* Device name
* Script to execute with the Turn-on action
* Script to execute with the Turn-off action
* TCP Port. Different between devices (value between 1024 and 65535).
  Port 0 can be used, AlexaLove will select the port, but is not recommended.

## Requirements

To run AlexaLove you need Python 2.7 and standard libraries. 

## Files:

- home.py: Is the launcher script. You can execute this script using `./home.py.`
  If you use the argument `-d` (`./home.py -d`) you will get an extra debug.
- alexalover.conf: This is the configuration file, you must modify this file to
  include your devices.
- scripts folder: This folder includes examples to interact with Xiaomi Yeelight
  bulbs. Add your own scripts for your devices here. Sharing you scripts is appreciated.
  For Yeelight, I am using [yeelight-shell-scripts](https://github.com/hphde/yeelight-shell-scripts).

#### Other files:
- alexalover.py: Is the library code. You do not need modify this file.
- alexa_conf_reader.py: Library to read and parse the configuration file.


## Configuration

Edit the `alexalover.conf` configuration file. You will see something like this:

```
# Only 16 devices can be used
# Enter your devices with this format:
# Name;script to turn on; script to turn off; Port (0 if not set)
Test1;/home/kix/src/alexalover/scripts/test-on.sh;/home/kix/src/alexalover/scripts/test-off.sh;0
Test2;/home/kix/src/alexalover/scripts/test-on.sh;/home/kix/src/alexalover/scripts/test-off.sh;0
```

Modify your configuration file to something like this:

```
# Only 16 devices can be used
# Enter your devices with this format:
# Name;script to turn on; script to turn off; Port (0 if not set)
Room;/home/kix/src/alexalover/scripts/yeelight-blue-on.sh;/home/kix/src/alexalover/scripts/yeelight-off.sh;50000
Dorm;/home/kix/src/alexalover/scripts/dorm-blue-on.sh;/home/kix/src/alexalover/scripts/dorm-off.sh;50001
```

This configuration file has two devices (Room and Dorm). The first device (Room) has
two scripts, first (yeelight-blue-on.sh) is used for the "On" action. The second one
(yeelight-off.sh) is used for the "Off" action. The last value for the first device is
the TCP port, 50000 is used.
The second device (Dorm) includes the files to turn on and off the dorm light. It uses the
port 50001.

## Running AlexaLover

First, modify your configuration file and launch AlexaLover using the `home.py` script:

```
./home.py
```

Then tell to your Amazon Echo "Find connected devices".

If you want, can add the `home.py` script to your `/etc/rc.local` file to launch AlexaLover
when your system boots. Remember to include the full path:

```
# AlexaLover
printf "Running AlexaLover\n"
/home/kix/src/alexalover/home.py &

```

## More Info and contact

- [GitHub](https://www.github.com/thekix/alexalover)
- [Web: http://www.kix.es/](http://www.kix.es/)
- [Contact, email](kix@kix.es)
