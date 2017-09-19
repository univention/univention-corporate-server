/*
 * Copyright 2016-2017 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"umc/tools",
	"umc/widgets/NumberSpinner",
	"umc/widgets/Page",
	"umc/widgets/SearchForm",
	"umc/widgets/TextBox",
	"umc/modules/logview/FiletextWidget",
	"umc/i18n!umc/modules/logview"
], function(declare, lang, on, tools, NumberSpinner, Page, SearchForm, TextBox, FiletextWidget, _) {

	var DEFAULT_LOGTEXT = _('... loading log ...');
	var DEFAULT_HELPTEXT = _('Filename');
	var SCROLLING_THRESHOLD = 80;  // distance from the end of the page to trigger lazy loading
	var LINE_BUFFER = 100;  // should fill the screen on any resolution

	return declare("umc.modules.logview.DetailPage", [Page], {

		_readyToLoad: false,
		_filename: '',
		_offset: 0,
		_buffer: LINE_BUFFER,
		_text: '',
		_pattern: '',
		_textWidget: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.headerText = _('View logfile:');
			this.helpText = DEFAULT_HELPTEXT;

			this.headerButtons = [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Back to list of files'),
				callback: lang.hitch(this, 'onClose')
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: TextBox,
				name: 'pattern',
				description: _('Specifies the substring pattern which is searched for in the file\'s content'),
				label: _('Search for content')
			}, {
				type: NumberSpinner,
				name: 'radius',
				description: _('Specifies how many lines of context around an occurrence of the search pattern are displayed'),
				label: _('Search result context radius'),
				constraints: { min: 0, max: 99, places: 0 },
				value: 5
			}];

			var layout = [
				['pattern', 'radius', 'submit']
			];

			this._searchForm = new SearchForm({
				region: 'nav',
				widgets: widgets,
				layout: layout,
				onSearch: lang.hitch(this, '_onSearch')
			});
			this.addChild(this._searchForm);

			this._textWidget = new FiletextWidget({
				region: 'main',
				placeholder: DEFAULT_LOGTEXT
			});
			this.own(this._textWidget);
			this.addChild(this._textWidget);

			on(window, 'scroll', lang.hitch(this, '_onScroll'));
		},

		load: function(filename, pattern, radius) {
			this._filename = filename;
			this.set('helpText', filename);
			this._searchForm.getWidget('pattern').set('value', pattern);
			this._searchForm.getWidget('radius').set('value', radius);
			this._offset = 0;
			this._onSearch(this._searchForm.get('value'));
		},

		getPattern: function() {
			return this._searchForm.getWidget('pattern').get('value');
		},

		onClose: function() {
			this._readyToLoad = false;
			this._filename = '';
			this._text = '';
			this.set('helpText', DEFAULT_HELPTEXT);
			this._textWidget.setText(DEFAULT_LOGTEXT);
		},

		_onScroll: function() {
			if (!this._readyToLoad) {
				return;
			}
			var position = window.pageYOffset;
			var bottom = document.documentElement.scrollHeight - document.documentElement.clientHeight;
			if (position > bottom - SCROLLING_THRESHOLD) {
				this._loadText();
			}
		},

		_loadText: function() {
			this._readyToLoad = false;
			var options = {
				logfile: this._filename,
				offset: this._offset,
				buffer: this._buffer
			};
			this._textWidget.standby(true);
			tools.umcpCommand('logview/load_text', options).then(lang.hitch(this, '_receiveText'));
		},

		_onSearch: function(values) {
			var pattern = this._pattern = values.pattern;
			if (!pattern) {
				this._loadText();
				return;
			}
			this._readyToLoad = false;
			var options = lang.mixin(values, {
				logfile: this._filename,
			});
			this._textWidget.standby(true);
			tools.umcpCommand('logview/search_pattern', options).then(lang.hitch(this, '_receiveText'));
		},

		_receiveText: function(data) {
			var text = data.result;
			var pattern = this._pattern;
			if (pattern) {
				if (text) {
					this._textWidget.setText(text, pattern);
					return;
				}
				this._textWidget.setText(_('No match found for pattern %s.', pattern));
				return;
			}
			if (!text) {
				// EOF
				this._textWidget.setText(this._text);
				return;
			}
			this._text += text;
			this._offset += this._buffer;
			this._textWidget.setText(this._text);
			this._readyToLoad = true;
		}
	});
});
