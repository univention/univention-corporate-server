# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  event loop
#
# Copyright 2010-2012 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.
"""Event loop. From libvirt/examples/domain-events/events-python/event-test-py"""
#################################################################################
# Start off by implementing a general purpose event loop for anyones use
#################################################################################

import os
import libvirt
import select
import errno
import time
import threading

class virEventLoopPure:
    """
    This general purpose event loop will support waiting for file handle
    I/O and errors events, as well as scheduling repeatable timers with
    a fixed interval.

    It is a pure python implementation based around the poll() API."""
    class virEventLoopPureHandle:
        """This class contains the data we need to track for a single file handle."""
        def __init__(self, handle, fd, events, cb, opaque):
            self.handle = handle
            self.fd = fd
            self.events = events
            self.cb = cb
            self.opaque = opaque

        def get_id(self):
            return self.handle

        def get_fd(self):
            return self.fd

        def get_events(self):
            return self.events

        def set_events(self, events):
            self.events = events

        def dispatch(self, events):
            self.cb(self.handle,
                    self.fd,
                    events,
                    self.opaque[0],
                    self.opaque[1])

    class virEventLoopPureTimer:
        """This class contains the data we need to track for a single periodic timer."""
        def __init__(self, timer, interval, cb, opaque):
            self.timer = timer
            self.interval = interval
            self.cb = cb
            self.opaque = opaque
            self.lastfired = 0

        def get_id(self):
            return self.timer

        def get_interval(self):
            return self.interval

        def set_interval(self, interval):
            self.interval = interval

        def get_last_fired(self):
            return self.lastfired

        def set_last_fired(self, now):
            self.lastfired = now

        def dispatch(self):
            self.cb(self.timer,
                    self.opaque[0],
                    self.opaque[1])


    def __init__(self, debug=False):
        self.debugOn = debug
        self.poll = select.poll()
        self.pipetrick = os.pipe()
        self.pendingWakeup = False
        self.runningPoll = False
        self.nextHandleID = 1
        self.nextTimerID = 1
        self.handles = []
        self.timers = []
        self.quit = False

        # The event loop can be used from multiple threads at once.
        # Specifically while the main thread is sleeping in poll()
        # waiting for events to occur, another thread may come along
        # and add/update/remove a file handle, or timer. When this
        # happens we need to interrupt the poll() sleep in the other
        # thread, so that it'll see the file handle / timer changes.
        #
        # Using OS level signals for this is very unreliable and
        # hard to implement correctly. Thus we use the real classic
        # "self pipe" trick. A anonymous pipe, with one end registered
        # with the event loop for input events. When we need to force
        # the main thread out of a poll() sleep, we simple write a
        # single byte of data to the other end of the pipe.
        self.debug("Self pipe watch %d write %d" %(self.pipetrick[0], self.pipetrick[1]))
        self.poll.register(self.pipetrick[0], select.POLLIN)

    def debug(self, msg):
        if self.debugOn:
            print msg


    def next_timeout(self):
        """Calculate when the next timeout is due to occurr, returning
        the absolute timestamp for the next timeout, or 0 if there is
        no timeout due."""
        next = 0
        for t in self.timers:
            last = t.get_last_fired()
            interval = t.get_interval()
            if interval < 0:
                continue
            if next == 0 or (last + interval) < next:
                next = last + interval

        return next

    def get_handle_by_fd(self, fd):
        """Lookup a virEventLoopPureHandle object based on file descriptor."""
        for h in self.handles:
            if h.get_fd() == fd:
                return h
        return None

    def get_handle_by_id(self, handleID):
        """Lookup a virEventLoopPureHandle object based on its event loop ID."""
        for h in self.handles:
            if h.get_id() == handleID:
                return h
        return None


    def run_once(self):
        """
        This is the heart of the event loop, performing one single
        iteration. It asks when the next timeout is due, and then
        calcuates the maximum amount of time it is able to sleep
        for in poll() pending file handle events.

        It then goes into the poll() sleep.

        When poll() returns, there will zero or more file handle
        events which need to be dispatched to registered callbacks
        It may also be time to fire some periodic timers.

        Due to the coarse granularity of schedular timeslices, if
        we ask for a sleep of 500ms in order to satisfy a timer, we
        may return upto 1 schedular timeslice early. So even though
        our sleep timeout was reached, the registered timer may not
        technically be at its expiry point. This leads to us going
        back around the loop with a crazy 5ms sleep. So when checking
        if timeouts are due, we allow a margin of 20ms, to avoid
        these pointless repeated tiny sleeps."""
        sleep = -1
        self.runningPoll = True
        next = self.next_timeout()
        self.debug("Next timeout due at %d" % next)
        if next > 0:
            now = int(time.time() * 1000)
            if now >= next:
                sleep = 0
            else:
                sleep = (next - now) / 1000.0

        self.debug("Poll with a sleep of %d" % sleep)
        while True:
            try:
                events = self.poll.poll(sleep)
                break
            except select.error, (err, msg):
                if err != errno.EINTR:
                    raise

        # Dispatch any file handle events that occurred
        for (fd, revents) in events:
            # See if the events was from the self-pipe
            # telling us to wakup. if so, then discard
            # the data just continue
            if fd == self.pipetrick[0]:
                self.pendingWakeup = False
                data = os.read(fd, 1)
                continue

            h = self.get_handle_by_fd(fd)
            if h:
                self.debug("Dispatch fd %d handle %d events %d" % (fd, h.get_id(), revents))
                h.dispatch(self.events_from_poll(revents))

        now = int(time.time() * 1000)
        for t in self.timers:
            interval = t.get_interval()
            if interval < 0:
                continue

            want = t.get_last_fired() + interval
            # Deduct 20ms, since schedular timeslice
            # means we could be ever so slightly early
            if now >= (want-20):
                self.debug("Dispatch timer %d now %s want %s" % (t.get_id(), str(now), str(want)))
                t.set_last_fired(now)
                t.dispatch()

        self.runningPoll = False

    def run_loop(self):
        """Actually the event loop forever."""
        self.quit = False
        while not self.quit:
            self.run_once()

    def interrupt(self):
        if self.runningPoll and not self.pendingWakeup:
            self.pendingWakeup = True
            os.write(self.pipetrick[1], 'c')


    def add_handle(self, fd, events, cb, opaque):
        """
        Registers a new file handle 'fd', monitoring  for 'events' (libvirt
        event constants), firing the callback  cb() when an event occurs.
        Returns a unique integer identier for this handle, that should be
        used to later update/remove it."""
        handleID = self.nextHandleID + 1
        self.nextHandleID = self.nextHandleID + 1

        h = self.virEventLoopPureHandle(handleID, fd, events, cb, opaque)
        self.handles.append(h)

        self.poll.register(fd, self.events_to_poll(events))
        self.interrupt()

        self.debug("Add handle %d fd %d events %d" % (handleID, fd, events))

        return handleID

    def add_timer(self, interval, cb, opaque):
        """
        Registers a new timer with periodic expiry at 'interval' ms,
        firing cb() each time the timer expires. If 'interval' is -1,
        then the timer is registered, but not enabled
        Returns a unique integer identier for this handle, that should be
        used to later update/remove it."""
        timerID = self.nextTimerID + 1
        self.nextTimerID = self.nextTimerID + 1

        h = self.virEventLoopPureTimer(timerID, interval, cb, opaque)
        self.timers.append(h)
        self.interrupt()

        self.debug("Add timer %d interval %d" % (timerID, interval))

        return timerID

    def update_handle(self, handleID, events):
        """Change the set of events to be monitored on the file handle."""
        h = self.get_handle_by_id(handleID)
        if h:
            h.set_events(events)
            self.poll.unregister(h.get_fd())
            self.poll.register(h.get_fd(), self.events_to_poll(events))
            self.interrupt()

            self.debug("Update handle %d fd %d events %d" % (handleID, h.get_fd(), events))

    def update_timer(self, timerID, interval):
        """Change the periodic frequency of the timer."""
        for h in self.timers:
            if h.get_id() == timerID:
                h.set_interval(interval);
                self.interrupt()

                self.debug("Update timer %d interval %d"  % (timerID, interval))
                break

    def remove_handle(self, handleID):
        """Stop monitoring for events on the file handle."""
        handles = []
        for h in self.handles:
            if h.get_id() == handleID:
                self.poll.unregister(h.get_fd())
                self.debug("Remove handle %d fd %d" % (handleID, h.get_fd()))
            else:
                handles.append(h)
        self.handles = handles
        self.interrupt()

    def remove_timer(self, timerID):
        """Stop firing the periodic timer."""
        timers = []
        for h in self.timers:
            if h.get_id() != timerID:
                timers.append(h)
                self.debug("Remove timer %d" % timerID)
        self.timers = timers
        self.interrupt()

    def events_to_poll(self, events):
        """Convert from libvirt event constants, to poll() events constants."""
        ret = 0
        if events & libvirt.VIR_EVENT_HANDLE_READABLE:
            ret |= select.POLLIN
        if events & libvirt.VIR_EVENT_HANDLE_WRITABLE:
            ret |= select.POLLOUT
        if events & libvirt.VIR_EVENT_HANDLE_ERROR:
            ret |= select.POLLERR;
        if events & libvirt.VIR_EVENT_HANDLE_HANGUP:
            ret |= select.POLLHUP;
        return ret

    def events_from_poll(self, events):
        """Convert from poll() event constants, to libvirt events constants."""
        ret = 0;
        if events & select.POLLIN:
            ret |= libvirt.VIR_EVENT_HANDLE_READABLE;
        if events & select.POLLOUT:
            ret |= libvirt.VIR_EVENT_HANDLE_WRITABLE;
        if events & select.POLLNVAL:
            ret |= libvirt.VIR_EVENT_HANDLE_ERROR;
        if events & select.POLLERR:
            ret |= libvirt.VIR_EVENT_HANDLE_ERROR;
        if events & select.POLLHUP:
            ret |= libvirt.VIR_EVENT_HANDLE_HANGUP;
        return ret;


###########################################################################
# Now glue an instance of the general event loop into libvirt's event loop
###########################################################################

# This single global instance of the event loop wil be used for
# monitoring libvirt events
eventLoop = virEventLoopPure(debug=False)

# This keeps track of what thread is running the event loop,
# (if it is run in a background thread)
eventLoopThread = None


# These next set of 6 methods are the glue between the official
# libvirt events API, and our particular impl of the event loop
#
# There is no reason why the 'virEventLoopPure' has to be used.
# An application could easily may these 6 glue methods hook into
# another event loop such as GLib's, or something like the python
# Twisted event framework.

def virEventAddHandleImpl(fd, events, cb, opaque):
    global eventLoop
    return eventLoop.add_handle(fd, events, cb, opaque)

def virEventUpdateHandleImpl(handleID, events):
    global eventLoop
    return eventLoop.update_handle(handleID, events)

def virEventRemoveHandleImpl(handleID):
    global eventLoop
    return eventLoop.remove_handle(handleID)

def virEventAddTimerImpl(interval, cb, opaque):
    global eventLoop
    return eventLoop.add_timer(interval, cb, opaque)

def virEventUpdateTimerImpl(timerID, interval):
    global eventLoop
    return eventLoop.update_timer(timerID, interval)

def virEventRemoveTimerImpl(timerID):
    global eventLoop
    return eventLoop.remove_timer(timerID)

def virEventLoopPureRegister():
    """This tells libvirt what event loop implementation it should use."""
    libvirt.virEventRegisterImpl(virEventAddHandleImpl,
                                 virEventUpdateHandleImpl,
                                 virEventRemoveHandleImpl,
                                 virEventAddTimerImpl,
                                 virEventUpdateTimerImpl,
                                 virEventRemoveTimerImpl)

def virEventLoopPureRun():
    """Directly run the event loop in the current thread."""
    global eventLoop
    eventLoop.run_loop()

def virEventLoopPureStart():
    """Spawn a background thread to run the event loop."""
    global eventLoopThread
    eventLoopThread = threading.Thread(target=virEventLoopPureRun, name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()
