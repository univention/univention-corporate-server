The Online Update Module supports the following hooks which are called
once at module startup:
- updater_show_message
- updater_prohibit_update

These hooks may reside within a single python file that has to be placed in the
directory /usr/share/univention-updater/hooks/
The content of an example hookfile is placed below.

Hook "updater_show_message"
===========================
This hook is called to allow 3rd party software to display messages within the
Online Update Module. The returned message will be displayed in a separate
TitlePane for each hook.

This hook has to return a python dictionary:
Key       | Type    | Description
==========|=========|===============================================================
'valid'   | Boolean | Indicates if this hooks wants to display a message (REQUIRED)
          |         | All other keys have to be set, if this value is set to True.
----------|---------|---------------------------------------------------------------
'title'   | String  | title of displayed TitlePane
----------|---------|---------------------------------------------------------------
'message' | String  | content of TitlePane
----------|---------|---------------------------------------------------------------


Hook "updater_prohibit_update"
==============================
This hook is called to allow 3rd party software to block further updates. Please use
this feature only if the update would fail or break the system otherwise.
Each hook has to return a Boolean. If at least one hook returns the value True, the
update related TitlePanes will not be displayed to the user.



Example myhook.py
=================

	def my_func1(*args, **kwargs):
		return { 'valid': True,
				 'title': 'The Title Of The TitlePane',
				 'message': '<p>The content of the <b>TitlePane</b></p>'
				 }

	def my_func2(*args, **kwargs):
		return True

	def register_hooks():
		return [ ('updater_show_message', my_func1),
				 ('updater_prohibit_update', my_func2)]
