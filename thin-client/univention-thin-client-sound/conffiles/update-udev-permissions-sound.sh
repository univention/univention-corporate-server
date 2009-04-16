#!/bin/sh
#
# reload udev rules (in case kernel does not support inotify)
udevcontrol reload_rules

# retrigger sound hotplug events
udevtrigger --subsystem-match=sound
