/*
 * Copyright 2011-2013 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define window console*/

// Class that provides a scrollable logfile viewer.

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/modules/updater/Page",
	"umc/widgets/ExpandingTitlePane",
	"umc/i18n!umc/modules/updater"
], function(declare, lang, tools, Text, ContainerWidget, Page, ExpandingTitlePane, _) {
	return declare('umc.modules.updater.LogPage', Page, {

		_all_lines:		[], // hold all past _max_number_of_lines lines

		// FIXME which class should I take here?
		style:		'border:1px solid #d0d0d0;background-color:#f8f8f8;padding:.3em;',

		postMixInProperties: function () {

		this.footerButtons = [{
				
				name:		'closelog',
				align:		'left',
				label:		_("back"),
				callback: lang.hitch(this, function() {
					this.onCloseLog();
					})
				},
				{
				name:		'jumptoend',
				align:		'right',
				label: 		_("jump to end of log"),
				callback: lang.hitch(this, function(){
					this.scrollToBottom();
					})
				
				}];

		},


		buildRendering: function() {

			this.inherited(arguments);

			this._pane = new ExpandingTitlePane({
				title:		_("Log file view")
			});
			
			this._container = new ContainerWidget ({
				scrollable: 		true  });

			this.addChild(this._pane);
			this._pane.addChild(this._container);	

			this._text = new Text({
				style:		'font-family:monospace;',
				content:	_("... loading log file ...")
			});
			this._container.addChild(this._text);
		},
		
		// read /var/log/univention/updater.log
		_fetch_log: function() {

			tools.umcpCommand('updater/installer/logfile', {},false).then(lang.hitch(this, function (data) {
				this.onQuerySuccess('updater/installer/logfile');
				this.setContentAttr(data.result);
			}));
		},
			

		// set content of _text
		setContentAttr: function(lines) {
			this._all_lines = this._all_lines.concat(lines);
			var printable_lines = this._all_lines;
			var content = printable_lines.join('<br />\n');
			this._text.set('content', content);
		},

	
		// scrolls to the bottom of the log. 
		scrollToBottom: function() {

			var todo = true;
			var node = this._text.contentNode.parentNode;
			var skip = 1024;
			while (todo)
			{
				var oldval = node.scrollTop;
				node.scrollTop = oldval+skip;
				var newval = node.scrollTop;

				// manually changed?
				// or new value not accepted?
				if (newval != (oldval+skip))
				{
					if (skip > 1)
					{
						skip = Math.floor(skip / 2);
					}
					else
					{
						todo = false;
					}
				}
			}
		},

		// can be listened to from outside
		onQueryError: function(subject,data) {
		},
		onQuerySuccess: function(subject) {
		},
		onCloseLog: function() {
		}
	});
});
