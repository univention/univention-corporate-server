# -*- coding: utf-8 -*-
#
# Univention Management Console
#  class representing a link object within a UMCP dialog
#
# Copyright (C) 2006-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import base
import urllib
import random

class RefreshFrame( base.HTML ):
	def __init__( self, sessionid, command, opts = {}, attributes = {}, maxlen=300000, refresh_interval=3000 ):
		"""
		Returns a frame with specified geometry and refreshes its content every 'refresh_interval' miliseconds by calling
		Arguments:
			command 'command' with specified opts
			sessionid: the session id (required)
			command: umcp command to be called for getting new content
			opts: options passed to umcp command
			attributes: dictionary with widget attributes (colspan, width (in pixel), height (in pixel))
			maxlen: maximum length of data shown in frame (don't use too large values - it will slow down your browser)
			refresh_interval: interval in miliseconds

		Example for revamp:
		result.add_row( [ umcd.RefreshFrame( self._sessionid, 'some/command', { 'foo1': 3, 'ding': 'dong' }, attributes = { 'colspan': '3', 'width': '750', 'height': '400' }, refresh_interval=1000) ] )

		from json import JsonWriter
		def _web_some_command(self, object, res):
		 	data = [ '%s ==> %s\n' % (time.ctime(), repr(object.options)) ]
		 	json = JsonWriter()
		 	content = json.write(data)
		 	content_type = 'application/json'
		 	res.dialog = { 'Content-Type': content_type, 'Content': content }
		 	self.revamped( object.id(), res, rawresult = True )

		"""
		# create custom text identifier
		alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
		identifier = ''.join( [ random.choice(alpha) for i in xrange(0, 8) ] )

		# default width and height
		widget_width = 900
		widget_height = 300

		if attributes.get('width'):
			try:
				widget_width = int(attributes.get('width'))
			except:
				pass
		if attributes.get('height'):
			try:
				widget_height = int(attributes.get('height'))
			except:
				pass

		url_options = urllib.urlencode(opts)

		txt_div = '<div id="wnd%(identifier)s" style="width:%(width)spx; height:%(height)spx; overflow: scroll; border:1px solid #000000; margin: 1px; background: #F8F8F8 none repeat scroll 0 0"><pre id="data%(identifier)s" style="background: #F8F8F8 none repeat scroll 0 0"></pre></div>' % { 'width': widget_width, 'height': widget_height, 'identifier': identifier }

		txt_javascript = """
<script type='text/javascript'>
var umc = {};
umc.ajax = {};
umc.ajax.refreshframe = {};
umc.ajax.refreshframe.updateData = function(refreshurl, wndid, dataid, maxlen) {
    var xhrArgs = {
            url: refreshurl,
            handleAs: 'json',
            preventCache: true,
            load: function(data) {
				var newdata = dojo.byId( dataid ).innerHTML + data[0];
				if (newdata.length > maxlen) {
					newdata = newdata.substr(newdata.length - maxlen, maxlen);
				}
				dojo.byId( dataid ).innerHTML = newdata;
				dojo.byId( wndid ).scrollTop = dojo.byId( wndid ).scrollHeight;
            },
        }
    var deferred = dojo.xhrGet(xhrArgs);
};
dojo.addOnLoad (function() {
    url = 'ajax.py?session_id=%(sessionid)s&umcpcmd=%(command)s&%(options)s';
	wndid = 'wnd%(identifier)s';
	dataid = 'data%(identifier)s';
	umc.ajax.refreshframe.updateData(url, wndid, dataid, %(maxlen)d);
    window.setInterval( function() { umc.ajax.refreshframe.updateData(url, wndid, dataid, %(maxlen)d);}, %(interval)s);
});
</script>
""" % { 'sessionid': sessionid,
		'maxlen': maxlen,
		'command': command,
		'options': url_options,
		'interval': refresh_interval,
		'identifier': identifier,
		}

		html = '%s%s' % (txt_div, txt_javascript)
		base.HTML.__init__( self, html, attributes = attributes )


AjaxTypes = ( type( RefreshFrame('','') ), )
