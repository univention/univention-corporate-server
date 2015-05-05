Introduction
============

To be notified or to be threaded that is the question!

As the package name may suggest, pyNotifier is a notifier/event
scheduler abstraction written in python. It implements notification
mechanisms for socket events (read or write) and timers. Additionally
external event dispatchers may be called during an idle period.

Applications using such an notifier mechanism implemented by
pyNotifier have a specific software architecture. These applications
are interactive, meaning that almost all action is only done because
an event occurred that was watched by the application. For example a
server application has to react if there is data waiting on a socket
or the socket is again ready to write data to the network. Some
applications may need to act in a recurrently interval of
time. Another type of interaction can be found in applications having
a graphical user interface.

Most applications of the described type do not need threads. Threading
is a mechanism that may help to solve some problems, but in most cases
it causes more problems than it solves. Threads are very often used to
process two or more tasks in parallel. The belief that threads are the
solution to this problem is a fallacy. The only solution to this
problem is the existence of several CPUs. A quasi parallel order of
events may be solved by using threads, but can also be solved by using
a notifier. When using threads the critical sections of the programs
must be locked by using adequate algorithm as the thread scheduler may
interrupt a function at any point. By using a notifier this problems
are irrelevant as a notifier just schedules the next event, when the
handler of the previous event is finished, i.e. there are no critical
sections that have to be protected. Being able to forego on any kind
of protection for critical sections reduces the length and increases
the clarity of the source code.

Application programmers who want to use a notifier/event scheduler
based architecture for their software may run into one problem when
trying to implement a graphical user interface for the X11 Window
System. As the X11 window system itself uses a event based
architecture all known widget set implementations are also based on
such mechanisms. Examples for such widget sets are GTK+, Qt or
wxWindows. The problem is that these software packages implement their
own notifier/event schedulers. To solve this problem pyNotifier
provides the possibility to wrap the notifier of a selected widget
set, so that applications using the pyNotifier API may still be able
to use a widget set without the need to convert their code to the
notifier API of the widget set. Currently wrappers for the previously
listed widget sets are available.

API
===

An application using pyNotifier has to initialise the notifier,
i.e. it has to choose which notifier implementation should be
used. This is done by calling the 'init' function:

	def init( type = GENERIC ):

If no argument is given to the 'init' function the internal
implementation of pyNotifier is used. Other possible choices for the
'type' argument are GTK, QT and WX (current support for wxWindows is
not up-to-date).

Some notifier implementations provide a set of options that control the
behaviour of the notifier. The options are passed to the implementation
as a keyword list through the 'init' function as shown in the following
example:

	def init( type = GTK, x11 = False )

This example uses the 'x11' option for the GTK notifier. If set
to False the notifier does not require gtk anymore and uses gobject
instead.

Sockets
-------

To get notified when a specific event occurs the application has to
register its interest for this event. For sockets and files this is
done with the 'socket\_add' function':

	def socket_add( id, method, condition = IO_IN )

The 'id' argument may be a socket or file object or a file descriptor
that can be retrieved by calling the 'fileno()' member function of
these objects. The second argument 'method' has to be a callable
python object that is invoked by the notifier if the registered event
has occured. The function is invoked with the 'id' as an
argument. Instead of a normal function the [Callback](#callbacks)
object provided by pyNotifier may be useful at this point.

To remove a registered socket or file from the notifier the
'socket\_remove' function has to be invoked. The 'id' is the socket or
file object or the file descriptor given to 'socket\_add' and the
optional argument 'condition' may be set to IO\_IN or IO\_OUT depending
on the previously registered event:

	def socket_remove( id, condition = IO_IN )

Another way to achieve the removal of a socket or file object from the
notifier is to return False in the callback function. If a callback
function returns False or nothing it is removed at the application is
never again triggered if this specific event occurs.

Timer
-----

pyNotifier supports just one type of timer. If a timer is registered
for a given interval of time the application is recurrently triggered
when the timer expires. To register a timer the 'timer\_add' function
has to be invoked. The first argument 'interval' must be specified in
milliseconds. 'method' is the callback function that is invoked by the
notifier without any argument when the timer expires.

	def timer_add( interval, method ) -> unique timer identifier

To implement a one-shot timer that is just triggered once and never
again the application can use the return value of its callback
function for this timer and return False or None. In this case the
notifier automatically removes the timer. Another way to remove a
timer is to call the method 'timer\_remove'.

	def timer_remove( id )

The 'id' argument is the unique timer identifier returned by 'timer\_add'.

Signals
-------

Currently there are two types of events that could cause a reaction of
the process: sockets and timers. With signals pyNotifier provides a
third technique to trigger a reaction within the process. This type does
not depend on external events or constant intervals of time. It can be
emitted whenever the application reaches a specific state and it can be
caught several times.

A signal is identified by a simple character string which must be unique
within the context. Before a signal can be emitted it has to be
created. Depending on the context (global or within an object) the
method names differ a little. In the following examples, demonstrating
the usage of signals, both variants will be shown.

The first thing to do is to create a new signal. The following example
shows that a signal '''signal1''' can be created in different contexts,
with the same name, because the uniqueness is just required within the
context.

	import notifier.signals as signals

	# global context
	signals.new( 'signal1' )

	class Test( signals.Provider ):
		def __init__( self ):
			signals.Provider.__init__( self )
			self.signal_new( 'signal1' )

To get informed when a signal is emitted a connection must be created as
shown in the following code snippet.

	# global context
	def _cb_signal( signal ):
		pass

	signals.connect( 'signal1', _cb_signal )

	# within the object
	class Test2( object ):
		def __init__( self, test ):
			test.signals_connect( 'signal1', self._cb_signal )

		def _cb_signal( self, signal ):
			pass

	test = Test()
	test2 = Test2( test )

There is no restriction in how many connection to a signal may exist,
but it should be noted, that to many connected instances may result an a
quite long amount of time where the application can not react on other
events.

So far it is possible to create new signals and to connect to them. To
emit a signal its name and possibly optional arguments are passed to a
function as shown in the following snippet.

	# global context
	signals.emit( 'signal1', a, b )

	# within an object
	test.signals_emit( 'signal1', a, b, c )

The signature of the callback function for a signal depends on the
specific signal provider, e.g. each signal may provide as many arguments
of different types as wanted. As there are currently no descriptions of
the callback signatures stored with the signals, the signal providers
hopefully provide some information.

External Dispatcher
-------------------

All already described tasks of an applications are scheduled by events
that have occurred on sockets or files or by predefined recurrently
time intervals. But some applications may also have some tasks that
may not need to be scheduled by any events or an exact timing. These
tasks should be repeated quite often, if there is some time to do it.

pyNotifier provides the feature to add so called external
dispatchers. These dispatchers are functions that will be invoked in
each notifier step after all timers and sockets were checked. To add a
dispatcher function to the notifier main loop the function
'dispatcher\_add' is provided. The only argument to this function is the
callback method that will be called.

	def dispatcher_add( method )

To remove such a dispatcher function from the notifier main loop
'dispatcher\_remove' is used with the call back method as the only argument.

	def dispatcher_remove( method )

Callbacks
---------

pyNotifier provides a class 'Callback' that can be used as a callback
function that is passed to the 'socket\_add' and 'timer\_add'
function. This class provides the possibility to pass more than the
specified arguments to the callback functions. For example the socket
callback function is called with one single argument. To pass some
state information to the callback function the 'Callback' object may
be used. A default callback function for a socket event would look
like 'socket1'.

	import notifier
	...
	notifier.socket_add( fd, socket1 )
	...

	def socket1( fd ):
		print 'data received on socket', fd
		return True

'fd' is the 'id' given to 'socket\_add'. To pass some state information
to the callback function it can be done as shown in the following
example.

	import notifier
	...
	notifier.socket_add( fd, notifier.Callback( socket1, arg1, arg2 ) )
	...

	def socket1( fd, arg1, arg2 ):
		print 'data received on socket', fd
		print 'additional state information', arg1, arg2

The arguments given to the Callback object are appended to the
original list of arguments for the callback function. The argument
list to the Callback object can be of any length.

Example
=======

The following example will demonstrate the most important features of
pyNotifier. More examples can be found in the latest release of
pyNotifier in the examples sub-directory.

	import sys

	import notifier

	def another_minute():
		print "another minute is elapsed"
		# callback should be invoked again
		return True

	def first_10_secs( secs ):
		print "the first %d secs are elapsed" % secs
		# this should be a one-shot timer
		return False

	def standard_in( in ):
		print "someone entered some data on stdin"
		print in.read( 80 )
		# still want to watch it
		return True

	if __name__ == "__main__":
		notifier.init( notifier.GENERIC )

		notifier.timer_add( 60000, another_minute )
		notifier.timer_add( 10000, notifier.Callback( first_10_secs, 10 ) )
		notifier.socket_add( sys.stdin, standard_in )

		notifier.loop()

Download
========

You can find the current development source at

	git clone https://github.com/crunchy-github/python-notifier.git

The latest release can be found at ["Downloads/pynotifier"]


Contact
=======

Any comments or questions can be send to

crunchy@bitkipper.net
