/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define, require, console, window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/has",
	"dojo/Deferred",
	"dojo/when",
	"dojo/promise/all",
	"dojo/on",
	"dojo/topic",
	"dojo/aspect",
	"dojo/json",
	"dojo/dom-style",
	"dojo/dom-class",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/_TextBoxMixin",
	"dijit/Dialog",
	"dojox/string/sprintf",
	"dojox/html/entities",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/Form",
	"umc/widgets/SearchForm",
	"umc/widgets/Button",
	"umc/widgets/Tree",
	"umc/widgets/MixedInput",
	"umc/widgets/ProgressBar",
	"umc/widgets/HiddenInput",
	"umc/modules/udm/TileView",
	"umc/modules/udm/TreeModel",
	"umc/modules/udm/CreateReportDialog",
	"umc/modules/udm/NewObjectDialog",
	"umc/modules/udm/DetailPage",
	"umc/modules/udm/cache",
	"umc/modules/udm/startup",
	"umc/i18n!umc/modules/udm",
	"umc/modules/udm/MultiObjectSelect",
	"umc/modules/udm/ComboBox",
	"umc/modules/udm/CertificateUploader",
	"xstyle/css!./udm.css"
], function(declare, lang, array, has, Deferred, when, all, on, topic, aspect, json,
	domStyle, domClass, Menu, MenuItem, _TextBoxMixin, Dialog, sprintf, entities, app, tools, dialog,
	store, ContainerWidget, Text, TextBox, CheckBox, ComboBox, Module, Page, Grid,
	Form, SearchForm, Button, Tree, MixedInput, ProgressBar, HiddenInput, TileView, TreeModel,
	CreateReportDialog, NewObjectDialog, DetailPage, cache, udmStartup, _)
{
	app.registerOnStartup(udmStartup);
	if ('registerOnReset' in tools) {
		tools.registerOnReset(function() {
			cache.reset();
		});
	}

	var _gridViewPreferenceDeferred = null;
	var _loadGridViewPreference = function() {
		// fetch grid view only once
		if (!_gridViewPreferenceDeferred) {
			_gridViewPreferenceDeferred = tools.getUserPreferences().then(function(prefs) {
				return prefs.udmUserGridView || 'default';
			});
		}
		return _gridViewPreferenceDeferred;
	};

	var _saveGridViewPreference = function(view) {
		// save grid view at LDAP user object
		tools.setUserPreference({
			udmUserGridView: view
		});

		// overwrite initially fetched result with the current view
		_gridViewPreferenceDeferred = new Deferred();
		_gridViewPreferenceDeferred.resolve(view);
	};

	// virtual widget which always returns the selected superordinate in the tree
	var SuperordinateWidget = declare("umc.modules.udm.SuperordinateWidget", HiddenInput, {
		udm: null,
		_getValueAttr: function() {
			if (!this.udm._tree) {
				return;
			}
			var path = lang.clone(this.udm._tree.get('path'));
			while (path.length) {
				var item = path.pop();
				if (item.$isSuperordinate$) {
					return item.id;
				}
			}
		}
	});

	var udm = declare("umc.modules.udm", [ Module ], {
		// summary:
		//		Module to interface (Univention Directory Manager) LDAP objects.
		// description:
		//		This class offers a GUI interface to query and manipulate the different types
		//		of LDAP objects. LDAP objects have different properties and functions, however,
		//		the way they are displayed is rudimentary similar across the different types.
		//		This class is meant to be used (a) either to interface a particular UDM type
		//		(users, groups, computers, ...) or (b) to display a navigation interface which
		//		shows the container hierarchy on the left side and existing LDAP objects of
		//		any type on the search list. The behavior of the class is controlled by the
		//		moduleFlavor property (which is set automatically when available modules are
		//		queried during the initialization).

		// openObject: Object?
		//		If given, the module will open upon start the detail page for editing the given
		//		object (specified by its LDAP DN). This property is expected to be a dict with
		//		the properties 'objectType' and 'objectDN' (both as strings).
		openObject: null,

		// newObject: Object?
		//		If given, the module will open upon start the detail page for editing a new
		//		object (specified by its objectType). This property is expected to be a dict with
		//		the properties 'objectType', 'container', 'objectTemplate' (optional), and
		//		'superordinate' (optional).
		newObject: null,

		'class': 'umcModuleUDM',

		// the property field that acts as unique identifier: the LDAP DN
		idProperty: '$dn$',

		// internal reference to the search page
		_searchPage: null,

		// internal reference to the detail page for editing an LDAP object
		_detailPage: null,

		// internal variables for preloading a DetailPage Bug# 38190
		_ldapNameDeferred: null,
		_preloadedObjectType: 'users/user',

		// internal reference if Page is fully rendered
		_pageRenderedDeferred: null,

		// reference to a `umc/widgets/Tree` instance which is used to display the container
		// hierarchy for the UDM navigation module
		_tree: null,

		// internal variable that indicates that the tree is reloading
		_reloadingPath: '',

		// reference to the last item in the navigation on which a context menu has been opened
		_navContextItem: null,

		// a dict of variable -> value entries for relevant UCR variables
		_ucr: null,

		// define grid columns
		_default_columns: null,

		// button to navigate back to the parent container
		_navUpButton: null,

		// button to generate reports
		_reportButton: null,

		// available reports
		_reports: null,

		// internal flag whether the advanced search is shown or not
		_isAdvancedSearch: false,

		_finishedDeferred: null,

		_menuEdit: null,
		_menuDelete: null,
		_menuMove: null,

		_newObjectDialog: null,

		_gridView: null,

		// set the opacity for the standby to 100%
		standbyOpacity: 1,

		postMixInProperties: function() {
			this.inherited(arguments);


			this.selectablePagesToLayoutMapping = {
				'_searchPage': ['navigation', 'dhcp/dhcp', 'dns/dns'].indexOf(this.moduleFlavor) >= 0 ? 'searchpage-grid-and-tree' : 'searchpage-grid',
				'_detailPage': 'udm-detailpage'
			};

			// this deferred is resolved when everything has been loaded
			this._finishedDeferred = new Deferred();
			this._pageRenderedDeferred = new Deferred();

			this._wizardStandby = new Deferred();
		},

		_loadUCRVariables: function() {
			var ucr = lang.getObject('umc.modules.udm.ucr');
			if (ucr) {
				// UCR variables have already been loaded
				this._ucr = ucr;
				var deferred = new Deferred();
				deferred.resolve(ucr);
				return deferred;
			}
			return tools.ucr(['directory/manager/web*', 'ldap/base', 'ad/member']).then(lang.hitch(this, function(ucr) {
				this._ucr = lang.setObject('umc.modules.udm.ucr', ucr);
			}));
		},

		_reloadCache: function(objects) {
			// reset cache if extended attribute or user template or default container changes
			var isExtendedAttribute = array.some(objects, function(iobj) {
				return iobj.objectType == 'settings/extended_attribute';
			});
			var isUserTemplate = array.some(objects, function(iobj) {
				return iobj.objectType == 'settings/usertemplate';
			});
			var isContainer = array.some(objects, function(iobj) {
				return iobj.objectType == 'container/cn' || iobj.objectType == 'container/ou';
			});
			if (isExtendedAttribute || isUserTemplate || isContainer) {
				cache.reset();
			}
		},

		buildRendering: function() {
			// call superclass method
			this.inherited(arguments);

			if (this.props) {
				this.openObject = {
					objectType: this.props.objectType || this.moduleFlavor,
					objectDN: this.props.dn
				};
			}

			if ('users/self' == this.moduleFlavor) {
				this.openObject = {
					objectType: this.moduleFlavor,
					objectDN: 'self'
				};
			}

			// check whether we need to open directly the detail page of a given or a new object
			if (this.openObject) {
				this._loadUCRVariables().then(lang.hitch(this, 'createDetailPage', 'edit',
					this.openObject.objectType, this.openObject.objectDN, undefined, true, this.openObject.note)
				);
				return; // do not render the search page
			}
			if (this.newObject) {
				this._loadUCRVariables().then(lang.hitch(this, 'createDetailPage', 'add',
					this.newObject.objectType, undefined, this.newObject, true, this.newObject.note)
				);
				return; // do not render the search page
			}
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);

			if ('navigation' == this.moduleFlavor) {
				// for the UDM navigation, we only query the UCR variables
				all({
					variables: this._loadUCRVariables(),
					columns: this.getDefaultColumns()
				}).then(lang.hitch(this, function(results) {
					this._default_columns = results.columns;
					this.renderSearchPage(undefined, {has_tree: true});
				}));
			} else {
				// render search page, we first need to query lists of containers/superordinates
				// in order to correctly render the search form...
				// query also necessary UCR variables for the UDM module
				var moduleCache = cache.get(this.moduleFlavor);
				moduleCache.preloadModuleInformation();
				all({
					columns: this.getDefaultColumns(),
					containers: moduleCache.getContainers(),
					reports: moduleCache.getReports(),
					metaInfo: moduleCache.getMetaInfo(),
					ucr: this._loadUCRVariables()
				}).then(lang.hitch(this, function(results) {
					this._reports = results.reports;
					this._default_columns = results.columns;
					this.renderSearchPage(results.containers, results.metaInfo);
					this._pageRenderedDeferred.resolve();
				}), lang.hitch(this, function() {
					this._pageRenderedDeferred.reject();
				}));
			}
		},

		ready: function() {
			//return this._finishedDeferred;
			return this._pageRenderedDeferred;
		},

		postCreate: function() {
			this.inherited(arguments);

			// register onClose events
			this.on('close', lang.hitch(this, 'onCloseTab'));

			// watch the state of the currently focused page
			this._loadUCRVariables().then(lang.hitch(this, function() {
				this.watch('selectedChildWidget', lang.hitch(this, function(name, oldChild, newChild) {
					if (newChild === this._detailPage) {
						window.scrollTo(0, 0);
					}
					this._updateModuleState();
				}));
			}));
		},

		_updateModuleState: function() {
			tools.defer(lang.hitch(this, function() {
				when(this.get('moduleState')).then(lang.hitch(this, function(moduleState) {
					this.set('moduleState', moduleState);
				}));
			}), 0);
		},

		_setModuleStateAttr: function(_state) {
			when(this.get('moduleState')).then(lang.hitch(this, function(currentState) {
				if (this._created && _state == this.moduleState || currentState == _state) {
					this._set('moduleState', _state);
					return;
				}
				var state = _state.split(':');
				if (!state.length || (state.length == 1 && state[0] === '')) {
					if (this._searchPage) {
						this.closeDetailPage();
					}
				}
				else {
					var objType = state.shift();
					var ldapName = state.length > 1 ? state : state[0];
					this._loadUCRVariables().then(lang.hitch(this, function() {
						this.createDetailPage('edit', objType, ldapName);
					}));
				}
				this._set('moduleState', _state);
			}));
		},

		_getModuleStateAttr: function() {
			if (this.selectedChildWidget != this._detailPage) {
				// no detail page shown
				return '';
			}
			return when(this._detailPage && this._detailPage.ldapName).then(lang.hitch(this, function(ldapName) {
				if ('string' == typeof ldapName) {
					// only handle single edits and ignore multi edits
					return lang.replace('{0}:{1}', [this._detailPage.objectType, ldapName]);
				}
				return '';
			}));
		},

		_ldapDN2TreePath: function(ldapDN) {
			var path = [];
			while (ldapDN != this._ucr[ 'ldap/base' ]) {
				path.unshift(ldapDN);
				ldapDN = ldapDN.slice(ldapDN.indexOf(',') + 1);
			}
			path.unshift(ldapDN);

			return path;
		},

		_checkMissingApp: function() {
			var _warningText = lang.hitch(this, function(app, link) {
				var params = {
					name: app.name,
					link: link
				};
				var warningText = {
					'users/user'        : _('Users managed here are used by the application "%(name)s" which is currently not installed.', params),
					'groups/group'      : _('Groups managed here are used by the application "%(name)s" which is currently not installed.', params),
					'computers/computer': _('Computers managed here are used by the application "%(name)s" which is currently not installed.', params),
					'networks/network'  : _('Network objects managed here are used by the application "%(name)s" which is currently not installed.', params),
					'dns/dns'           : _('DNS objects managed here are used by the application "%(name)s" which is currently not installed.', params),
					'dhcp/dhcp'         : _('DHCP objects managed here are used by the application "%(name)s" which is currently not installed.', params),
					'shares/share'      : _('Shares managed here are used by the application "%(name)s" which is currently not installed.', params),
					'shares/print'      : _('Printers managed here are used by the application "%(name)s" which is currently not installed.', params),
					'mail/mail'         : _('Mail objects managed here are used by the application "%(name)s" which is currently not installed.', params),
					'nagios/nagios'     : _('Nagios objects managed here are used by the application "%(name)s" which is currently not installed.', params),
					'policies/policy'   : _('Policies managed here are used by the application "%(name)s" which is currently not installed.', params)
				}[this.moduleFlavor];
				if (!warningText) {
					warningText = _('LDAP objects managed here are used by the application "%(name)s" which is currently not installed.', params);
				}
				warningText += _(' You can install the application using the %(link)s', params);

				return warningText;
			});
			// shows a warning if the UDM module is there, but a app that
			// would utilize the data in LDAP is missing
			// currently configured hard coded because otherwise one would
			// have to mix apps and udm in the backend which feels less right
			var allRequired = {
				'shares/print': 'cups'
			};
			var required = allRequired[this.moduleFlavor];
			if (required) {
				tools.umcpCommand('appcenter/get', {application: required}, false).then(lang.hitch(this, function(data) {
					var app = data.result;
					if (!app.is_installed_anywhere) {
						var link = sprintf('<a href="javascript:void(0)" onclick=\'require("umc/app").openModule(%s, %s).then(function(mod) { mod.showApp(%s) })\'>%s</a>',
							json.stringify('appcenter'),
							json.stringify('appcenter'),
							json.stringify(app),
							'Univention App Center'
						);
						this.addWarning(_warningText(app, link));

					}
				}));
			}
		},

		renderSearchPage: function(containers, metaInfo) {
			// summary:
			//		Render all GUI elements for the search formular, the grid, and the side-bar
			//		for the LDAP-directory and objects with superordinates.

			// show help icon if help_link is given for the module
			metaInfo = metaInfo || {};
			var hasTree = metaInfo.has_tree;
			var hasSuperordinates = hasTree && 'navigation' !== this.moduleFlavor;

			var buttons = [];
			if (metaInfo.help_link) {
				buttons = [{name: 'help',
					iconClass: 'umcHelpIconWhite',
					label: _('Help'),
					callback: lang.hitch(this, function() {
						window.open(metaInfo.help_link);
					})
				}];
			}

			// setup search page
			this._searchPage = new Page({
				headerText: this.description,
				helpText: metaInfo.help_text || '',
				headerButtons: buttons,
				fullWidth: !hasTree
			});

			// get the license information
			if (!tools.status('udm/licenseNote')) {
				tools.status('udm/licenseNote', true);
				this.umcpCommand('udm/license', {}, false).then(lang.hitch(this, function(data) {
					if (data.result.message) {
						var msg = _('<p><b>Add and modify are disabled in this session.</b></p><p>You have too many user accounts for your license. Carry out the following steps to re-enable editing:</p><ol><li>Disable or delete user accounts</li><li>Re-login to UMC for changes to take effect</li></ol><p>If a new license is needed, contact your UCS partner.</p>');
						dialog.alert(msg, _('<b>Warning!</b>'));
					}
				}), function() {
					console.log('WARNING: An error occurred while verifying the license. Ignoring error.');
				});
			}

			this.renderGrid();
			this.renderSearchForm(containers, hasSuperordinates);

			if (hasTree) {
				this.renderTree();
			}

			if (this._tree) {
				this._searchForm.region = 'main';
				this._searchPage.addChild(this._tree);
			}
			this._searchPage.addChild(this._searchForm);
			this._searchPage.addChild(this._grid);

			// register to onShow as well as onFilterDone events in order on focus to the
			// input widget when the tab is changed
			this.own(aspect.after(this._searchPage, '_onShow', lang.hitch(this, '_selectInputText')));
			this._grid.on('filterDone', lang.hitch(this, function() {
				if (!this._newObjectDialog) {
					// not during "wizard phase"
					this._selectInputText();
				}
			}));

			// register event to update hiding/showing of form fields
			this._searchForm.ready().then(lang.hitch(this, '_updateSearch'));
			this._grid.on('filterDone', lang.hitch(this, '_updateSearch'));

			// focus and select text when the objectPropertyValue has been loaded
			// at the beginning
			var propertyValueHandle = this._searchForm._widgets.objectPropertyValue.watch('value', lang.hitch(this, function() {
				propertyValueHandle.remove();
				this._finishedDeferred.then(lang.hitch(this, '_selectInputText'));
			}));
			this.own(propertyValueHandle);

			// show/hide object property filter for the navigation
			if ('navigation' == this.moduleFlavor) {
				this.own(this._searchForm._widgets.objectType.watch('value', lang.hitch(this, function(attr, oldval, val) {
					this._searchForm._widgets.objectProperty.set('visible', 'None' != val && '$containers$' != val);
					this._searchForm._widgets.objectPropertyValue.set('visible', 'None' != val && '$containers$' != val);
					this.layout();
				})));
			}

			// check whether we have autosearch activated
			if ('navigation' != this.moduleFlavor) {
				if (tools.isTrue(this._autoSearch)) {
					// connect to the onValuesInitialized event of the form
					on.once(this._searchForm, 'valuesInitialized', lang.hitch(this, function() {
						this.filter();
					}));
				}
			}

			this._searchPage.startup();
			this.addChild(this._searchPage);
			this._checkMissingApp();
			this._loadUCRVariables().then(lang.hitch(this, '_preloadDetailPage'));
			if (this.moduleFlavor === 'users/user') {
				_loadGridViewPreference().then(lang.hitch(this, function(view) {
					this._setGridView(view);
				}));
			}
		},

		renderGrid: function() {
			var _addDescriptionText = lang.hitch(this, function() {
				var text = {
					'users/user'          : _('Add a new user.'),
					'groups/group'        : _('Add a new group.'),
					'computers/computer'  : _('Add a new computer.'),
					'networks/network'    : _('Add a new network object.'),
					'dns/dns'             : _('Add a new DNS object.'),
					'dhcp/dhcp'           : _('Add a new DHCP object.'),
					'shares/share'        : _('Add a new share.'),
					'shares/print'        : _('Add a new printer.'),
					'mail/mail'           : _('Add a new mail object.'),
					'nagios/nagios'       : _('Add a new Nagios object.'),
					'policies/policy'     : _('Add a new policy.'),
					'settings/portal_all' : _('Add a new portal object.') 
				}[this.moduleFlavor];
				if (!text) {
					text = _('Add a new LDAP object.');
				}
				return text;
			});
			var _editDescriptionText = lang.hitch(this, function() {
				var text = {
					'users/user'          : _('Edit the user.'),
					'groups/group'        : _('Edit the group.'),
					'computers/computer'  : _('Edit the computer.'),
					'networks/network'    : _('Edit the network object.'),
					'dns/dns'             : _('Edit the DNS object.'),
					'dhcp/dhcp'           : _('Edit the DHCP object.'),
					'shares/share'        : _('Edit the share.'),
					'shares/print'        : _('Edit the printer.'),
					'mail/mail'           : _('Edit the mail object.'),
					'nagios/nagios'       : _('Edit the Nagios object.'),
					'policies/policy'     : _('Edit the policy.'),
					'settings/portal_all' : _('Edit the portal object.') 
				}[this.moduleFlavor];
				if (!text) {
					text = _('Edit the LDAP object.');
				}
				return text;
			});
			var _deleteDescriptionText = lang.hitch(this, function() {
				var text = {
					'users/user'          : _('Delete the selected users.'),
					'groups/group'        : _('Delete the selected groups.'),
					'computers/computer'  : _('Delete the selected computers.'),
					'networks/network'    : _('Delete the selected network objects.'),
					'dns/dns'             : _('Delete the selected DNS objects.'),
					'dhcp/dhcp'           : _('Delete the selected DHCP objects.'),
					'shares/share'        : _('Delete the selected shares.'),
					'shares/print'        : _('Delete the selected printers.'),
					'mail/mail'           : _('Delete the selected mail objects.'),
					'nagios/nagios'       : _('Delete the selected Nagios objects.'),
					'policies/policy'     : _('Delete the selected policies.'),
					'settings/portal_all' : _('Delete the selected portal object.') 
				}[this.moduleFlavor];
				if (!text) {
					text = _('Delete the selected LDAP objects.');
				}
				return text;
			});
			var _footerFormatter = lang.hitch(this, function(nItems, nItemsTotal) {
				var text = '';
				// generate the caption for the grid footer
				if (0 === nItemsTotal) {
					text = {
						'users/user'          : _('No users could be found.'),
						'groups/group'        : _('No groups could be found.'),
						'computers/computer'  : _('No computers could be found.'),
						'networks/network'    : _('No network objects could be found.'),
						'dns/dns'             : _('No DNS objects could be found.'),
						'dhcp/dhcp'           : _('No DHCP objects could be found.'),
						'shares/share'        : _('No shares could be found.'),
						'shares/print'        : _('No printers could be found.'),
						'mail/mail'           : _('No mail objects could be found.'),
						'nagios/nagios'       : _('No Nagios objects could be found.'),
						'policies/policy'     : _('No policies could be found.'),
						'settings/portal_all' : _('No portal object could be found.') 
					}[this.moduleFlavor];
					if (!text) {
						text = _('No LDAP objects could be found.');
					}
				} else {
					text = {
						'users/user'          : _.ngettext('One user of %d selected.', '%d users of %d selected.', nItems, nItemsTotal),
						'groups/group'        : _.ngettext('One group of %d selected.', '%d groups of %d selected.', nItems, nItemsTotal),
						'computers/computer'  : _.ngettext('One computer of %d selected.', '%d computers of %d selected.', nItems, nItemsTotal),
						'networks/network'    : _.ngettext('One network object of %d selected.', '%d network objects of %d selected.', nItems, nItemsTotal),
						'dns/dns'             : _.ngettext('One DNS object of %d selected.', '%d DNS objects of %d selected.', nItems, nItemsTotal),
						'dhcp/dhcp'           : _.ngettext('One DHCP object of %d selected.', '%d DHCP objects of %d selected.', nItems, nItemsTotal),
						'shares/share'        : _.ngettext('One share of %d selected.', '%d shares of %d selected.', nItems, nItemsTotal),
						'shares/print'        : _.ngettext('One printer of %d selected.', '%d printers of %d selected.', nItems, nItemsTotal),
						'mail/mail'           : _.ngettext('One mail object of %d selected.', '%d mail objects of %d selected.', nItems, nItemsTotal),
						'nagios/nagios'       : _.ngettext('One Nagios object of %d selected.', '%d Nagios objects of %d selected.', nItems, nItemsTotal),
						'policies/policy'     : _.ngettext('One policy of %d selected.', '%d policies of %d selected.', nItems, nItemsTotal),
						'settings/portal_all' : _.ngettext('One portal object of %d selected.', '%d portal objects of %d selected.', nItems, nItemsTotal)
					}[this.moduleFlavor];
					if (!text) {
						text = _.ngettext('One LDAP object of %d selected.', '%d LDAP objects of %d selected.', nItems, nItemsTotal);
					}
				}

				return text;
			});

			// define actions
			var actions = [{
				name: 'workaround',
				showAction: false, // this action is just used as a defaultAction in a special case
				isContextAction: false,
				callback: lang.hitch(this, function(keys, items) {
					this._tree.set('path', this._ldapDN2TreePath(keys[0]));
					this.filter();
				})
			}, {
				name: 'parentcontainer',
				label: _('Parent container'),
				callback: lang.hitch(this, function() {
					var path = this._tree.get('path');
					var ldapDN = path[ path.length - 2 ].id;
					this._tree.set('path', this._ldapDN2TreePath(ldapDN));
				}),
				isContextAction: false,
				isStandardAction: true,
				showAction: lang.hitch(this, function() {
					if (this._tree) {
						return this.moduleFlavor === 'navigation' && this._tree.get('path').length > 1;
					}
					return false;
				})
			}, {
				name: 'add',
				label: _('Add'),
				description: _addDescriptionText(),
				iconClass: 'umcIconAdd',
				isContextAction: false,
				isStandardAction: true,
				callback: lang.hitch(this, 'showNewObjectDialog')
			}, {
				name: 'edit',
				label: _('Edit'),
				description: _editDescriptionText(),
				iconClass: 'umcIconEdit',
				isStandardAction: true,
				isMultiAction: true,
				canExecute: lang.hitch(this, '_canEdit'),
				callback: lang.hitch(this, function(ids, items) {
					if (items.length == 1 && items[0].objectType) {
						this.createDetailPage('edit', items[0].objectType, ids[0]);
					} else if (items.length >= 1 && items[0].objectType) {
						// make sure that all objects do have the same type
						var sameType = true;
						array.forEach(items, function(iitem) {
							sameType = sameType && iitem.objectType == items[0].objectType;
							return sameType;
						});
						if (!sameType) {
							dialog.alert(_('Only objects of the same type can be edited together'));
							return;
						}

						// everything ok, load detail page
						this.createDetailPage('edit', items[0].objectType, ids);
					}
				})
			}, {
				name: 'editNewTab',
				label: _('Edit in new tab'),
				description: _('Open a new tab in order to edit the UDM-object'),
				isMultiAction: false,
				canExecute: lang.hitch(this, '_canEdit'),
				callback: lang.hitch(this, function(ids, items) {
					var moduleProps = {
						openObject: {
							objectType: items[0].objectType,
							objectDN: ids[0]
						},
						onCloseTab: lang.hitch(this, function() {
							try {
								this.focusModule();
							}
							catch (e) { }
						})
					};
					topic.publish('/umc/modules/open', this.moduleID, this.moduleFlavor, moduleProps);
				})
			}, {
				name: 'delete',
				label: _('Delete'),
				description: _deleteDescriptionText(),
				isStandardAction: true,
				isMultiAction: true,
				iconClass: 'umcIconDelete',
				canExecute: lang.hitch(this, '_canDelete'),
				callback: lang.hitch(this, function(ids, objects) {
					this.removeObjects(objects);
				})
			}, {
				name: 'move',
				label: _('Move to...'),
				description: _('Move objects to a different LDAP position.'),
				isMultiAction: true,
				canExecute: lang.hitch(this, '_canMove'),
				callback: lang.hitch(this, function(ids, objects) {
					this.moveObjects(objects);
				})
			}, {
				name: 'copy',
				label: _('Copy'),
				description: _('Create a copy of the LDAP object.'),
				isMultiAction: false,
				canExecute: lang.hitch(this, '_canCopy'),
				callback: lang.hitch(this, function(ids, items) {
					this._showNewObjectDialog({
						args: {
							wizardsDisabled: true,
							defaultObjectType: items[0].objectType,
							showObjectType: false,
							showObjectTemplate: false
						},
						callback: lang.hitch(this, function(options) {
							this.createDetailPage('copy', items[0].objectType, ids[0], lang.mixin(options, {objectTemplate: null}));
						})
					});
				})
			}];

			if ('navigation' !== this.moduleFlavor && this._reports.length) {
				actions.push({
					name: 'report',
					isStandardAction: false,
					isMultiAction: true,
					label: _('Create report'),
					iconClass: 'umcIconReport',
					callback: lang.hitch(this, '_createReport')
				});
			}

			// the navigation needs a slightly modified store that uses the UMCP query
			// function 'udm/nav/object/query'
			var _store = this.moduleStore;
			if ('navigation' == this.moduleFlavor) {
				_store = store(this.idProperty, 'udm/nav/object', this.moduleFlavor);
			}

			var additionalGridViews = {};
			if (this.moduleFlavor === 'users/user') {
				additionalGridViews = {tile: new TileView()};
			}

			// generate the data grid
			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: this._default_columns,
				moduleStore: _store,
				footerFormatter: _footerFormatter,
				additionalViews: additionalGridViews,
				defaultAction: lang.hitch(this, function(keys, items) {
					if ('navigation' == this.moduleFlavor && (this._searchForm._widgets.objectType.get('value') == '$containers$' || items[0].$childs$ === true)) {
						return 'workaround';
					}
					return 'edit';
				})
			});
		},

		_toggleGridView: function() {
			var view = this._grid.activeViewMode === 'tile' ? 'default' : 'tile';
			this._setGridView(view);
		},

		_setGridView: function(view) {
			view = view == 'tile' ? 'tile' : 'default';
			if (view != this._grid.activeViewMode) {
				_saveGridViewPreference(view);
				this._grid.changeView(view);
				this._searchForm._buttons.changeView.set('iconClass', lang.replace('umcGridViewIcon-{activeViewMode}', this._grid));
			}
		},

		renderSearchForm: function(containers, hasSuperordinates) {
			var _objectPropertyInlineLabelText = lang.hitch(this, function() {
				var text = {
					'users/user'          : _('Search users...'),
					'groups/group'        : _('Search groups...'),
					'computers/computer'  : _('Search computers...'),
					'networks/network'    : _('Search network objects...'),
					'dns/dns'             : _('Search DNS objects...'),
					'dhcp/dhcp'           : _('Search DHCP objects...'),
					'shares/share'        : _('Search shares...'),
					'shares/print'        : _('Search printers...'),
					'mail/mail'           : _('Search mail objects...'),
					'nagios/nagios'       : _('Search Nagios objects...'),
					'policies/policy'     : _('Search policies...'),
					'settings/portal_all' : _('Search portal objects...')
				}[this.moduleFlavor];
				if (!text) {
					text = _('Search LDAP objects...');
				}
				return text;
			});

			// get configured search values
			var autoObjProperty = this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/search/default'] ||
				this._ucr['directory/manager/web/modules/default'];
			this._autoSearch = this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/search/autosearch'] ||
				this._ucr['directory/manager/web/modules/autosearch'];
			this._wizardsDisabled = this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/wizard/disabled'] ||
				this._ucr['directory/manager/web/modules/wizard/disabled'];
			if (this.moduleFlavor == 'navigation') {
				this._wizardsDisabled = 'yes';
			}
			var _isAdvancedSearch = this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/search/advanced_on_open'] ||
				this._ucr['directory/manager/web/modules/search/advanced_on_open'];
			this._isAdvancedSearch = tools.isTrue(_isAdvancedSearch);

			var umcpCmd = lang.hitch(this, 'umcpCommand');
			var widgets = [];
			var layout = [ [], [] ]; // layout with three rows

			// check whether we need to display containers or superordinates
			var objTypeDependencies = [];
			var objTypes = [];
			var objProperties = [];
			if ('navigation' == this.moduleFlavor) {
				// add the types 'None'  and '$containers$' to objTypes
				objTypes.push({ id: 'None', label: _('All types') });
				objTypes.push({ id: '$containers$', label: _('All containers') });
			} else if ('settings/portal_all' === this.moduleFlavor) {
				objTypes.push({ id: this.moduleFlavor, label: _('All types') });
			} else if (hasSuperordinates) {
				// superordinates...
				widgets.push({
					type: SuperordinateWidget,
					udm: this,
					name: 'superordinate',
					label: _('Superordinate'),
					umcpCommand: umcpCmd
				});
				layout[0].push('superordinate');
				//objTypeDependencies.push('superordinate');  // FIXME: HiddenInput doesn't support to be dependency
				objTypes.push({ id: this.moduleFlavor, label: _('All types') });
			} else if (containers && containers.length) {
				// containers...
				containers.unshift({ id: 'all', label: _('All containers') });
				widgets.push({
					type: ComboBox,
					name: 'container',
					autoHide: true,
					label: _('Search in:'),
					value: containers[0].id || containers[0],
					staticValues: containers,
					umcpCommand: umcpCmd
				});
				layout[0].push('container');
				objTypes.push({ id: this.moduleFlavor, label: _('All types') });
			}
			objProperties.push({ id: 'None', label: _('Default properties') });

			// add remaining elements of the search form
			widgets = widgets.concat([{
				type: CheckBox,
				name: 'hidden',
				visible: false,
				label: _('Include hidden objects'),
				value: this.moduleFlavor == 'navigation'
			}, {
				type: ComboBox,
				name: 'objectType',
				autoHide: true,
				label: _('Type'),
				//value: objTypes.length ? this.moduleFlavor : undefined,
				// ComboBox.set('staticValues') seems broken. We need to remove 'All types' from the values in case there is only one object type (e.g. dns/ptr_record in a dns/reverse_zone).
//				staticValues: objTypes,
				sortDynamicValues: false,
				dynamicOptions: lang.hitch(this, function() {
					return this._searchForm.get('value');
				}),
				dynamicValues: lang.hitch(this, function(options) {
					var moduleCache = cache.get(this.moduleFlavor);
					return moduleCache.getChildModules(options.superordinate, null, true).then(lang.hitch(this, function(result) {
						result.sort(tools.cmpObjects({
							attribute: 'label',
							ignoreCase: true
						}));
						return array.filter(objTypes, lang.hitch(this, function(value) {
							return (result.length == 1) ? value.id !== this.moduleFlavor : true;
						})).concat(result);
					}));
				}),
				umcpCommand: umcpCmd,
				depends: objTypeDependencies,
				onChange: lang.hitch(this, function(newObjType) {
					var widget = this._searchForm.getWidget('objectType');
					if (!newObjType) {
						// object type is ''
						//   -> leads to traceback in the backend (module is None)
						widget.set('value', 'None'); // 'Default properties'
						return;
					}
					// update the object property depending on the updated object type
					var newObjProperty = this._ucr['directory/manager/web/modules/' + newObjType + '/search/default'] || '';
					var objPropertyWidget = this._searchForm._widgets.objectProperty;
					objPropertyWidget.setInitialValue(newObjProperty || undefined, false);
					widget.setInitialValue(null, false);
				})
			}, {
				type: ComboBox,
				autoHide: true,
				name: 'objectProperty',
				label: _('Property'),
				staticValues: objProperties,
				dynamicValues: lang.hitch(this, function(options) {
					var moduleCache = cache.get(this.moduleFlavor);
					return moduleCache.getProperties(options.objectType || this.moduleFlavor).then(function(properties) {
						return array.filter(properties, function(iprop) {
							return iprop.searchable;
						});
					});
				}),
				umcpCommand: umcpCmd,
				depends: 'objectType',
				value: autoObjProperty,
				onChange: lang.hitch(this, function(newVal) {
					var widget = this._searchForm.getWidget('objectProperty');
					if (!newVal) {
						// object property is ''
						//   probably because of invalid autoObjProperty
						//   -> leads to traceback in the backend (LDAP filter)
						widget.set('value', 'None'); // 'Default properties'
						return;
					}
					// get the current label of objectPropertyValue
					var label = _('Property value');
					array.some(widget.getAllItems(), function(iitem) {
						if (newVal == iitem.id) {
							label = iitem.label;
							return true;
						}
					});
					if (newVal == 'None') {
						// "Default properties" is not very catchy
						label = '&nbsp;';
					}

					// update the label of objectPropertyValue
					widget = this._searchForm.getWidget('objectPropertyValue');
					widget.set('label', label);
					this._updateSearch();
				})
			}, {
				type: MixedInput,
				name: 'objectPropertyValue',
				label: '&nbsp;',
				inlineLabel: _objectPropertyInlineLabelText(),
				dynamicValues: lang.hitch(this, function(options) {
					var moduleCache = cache.get(this.moduleFlavor);
					return moduleCache.getValues(this._searchForm.getWidget('objectType').get('value'), options.objectProperty);
				}),
				umcpCommand: umcpCmd,
				depends: 'objectProperty'
			}]);
			layout[0].push('objectType');
			if (hasSuperordinates) {
				layout[0].push('hidden');
				layout[1].push('objectProperty', 'objectPropertyValue');
			} else {
				layout[0].push('hidden');
				layout[1].push('objectProperty', 'objectPropertyValue');
			}

			// add also the buttons (specified by the search form itself) to the layout
			var buttons = [];
			if ('navigation' == this.moduleFlavor) {
				// put the buttons in the first row for the navigation
				layout[0].push('submit');
			} else {
				// append the buttons to the last row otherwise
				layout[1].push('submit');

				// add an additional button to toggle between advanced and simplified search
				buttons.push({
					name: 'toggleSearch',
					showLabel: false,
					labelConf: {
						'class': 'umcSearchFormSubmitButton'
					},
					iconClass: 'umcDoubleRightIcon',
					label: '',  // label will be set in toggleSearch
					callback: lang.hitch(this, function() {
						this._isAdvancedSearch = !this._isAdvancedSearch;
						// reset all widgets if the search is toggled back to simple
						if (!this._isAdvancedSearch) {
							array.forEach(this._searchForm.widgets, lang.hitch(this, function(iWidget) {
								if (iWidget.name === 'objectPropertyValue') {
									return;
								}
								this._searchForm.getWidget(iWidget.name).reset();
							}));
						}
						domClass.toggle(this._searchForm.domNode, 'umcUDMSearchFormSimpleTextBox', (!this._isAdvancedSearch && this._searchForm._widgets.objectPropertyValue._widget instanceof TextBox));

						var search = this._isAdvancedSearch ? 'toggle-search-advanced' : 'toggle-search-simple';
						topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, search);
						this._updateSearch();
					})
				});
				layout[1].push('toggleSearch');
				if (this.moduleFlavor === 'users/user') {
					buttons.push({
						name: 'changeView',
						showLabel: false,
						label: _('Toggle visual presentation'),
						iconClass: 'umcGridViewIcon-default',
						'class': 'umcSearchFormChangeViewButton umcFlatButton',
						callback: lang.hitch(this, '_toggleGridView')
					});
					layout.push(['changeView']);
				}
			}


			// generate the search widget
			this._searchForm = new SearchForm({
				region: 'nav',
				'class': 'umcUDMSearchForm',
				widgets: widgets,
				layout: layout,
				buttons: buttons,
				_getValueAttr: lang.hitch(this, '_getValueAttr'),
				onSearch: lang.hitch(this, 'filter')
			});
			domClass.toggle(this._searchForm.domNode, 'umcUDMSearchFormSimpleTextBox', (!this._isAdvancedSearch && this._searchForm._widgets.objectPropertyValue._widget instanceof TextBox));
			// only allow _updateVisibility calls on ComboBoxes if search is advanced.
			// prevents ComboBoxes from being shown when the values are loaded and then
			// immediately hidden again because the search form is in simple mode.
			var comboBoxWidgets = ['container', 'objectProperty'];
			if ('navigation' != this.moduleFlavor) {
				comboBoxWidgets.push('objectType');
			}
			array.forEach(comboBoxWidgets, lang.hitch(this, function(widgetName) {
				if (!this._searchForm._widgets[widgetName]) {
					return;
				}

				aspect.around(this._searchForm._widgets[widgetName], '_updateVisibility', lang.hitch(this, function(origFunction) {
					return lang.hitch(this, function() {
						if (this._isAdvancedSearch) {
							origFunction.apply(this._searchForm._widgets[widgetName]);
						}
					});
				}));
			}));
		},

		renderTree: function() {
			var _superordinateNameText = lang.hitch(this, function() {
				var text = {
					'users/user'        : _('Users'),
					'groups/group'      : _('Groups'),
					'computers/computer': _('Computers'),
					'networks/network'  : _('Network objects'),
					'dns/dns'           : _('DNS zones'),
					'dhcp/dhcp'         : _('DHCP services'),
					'shares/share'      : _('Shares'),
					'shares/print'      : _('Printers'),
					'mail/mail'         : _('Mail objects'),
					'nagios/nagios'     : _('Nagios objects'),
					'policies/policy'   : _('Policies')
				}[this.moduleFlavor];
				if (!text) {
					text = _('LDAP Objects');
				}
				return text;
			});
			// generate the navigation pane for the navigation module
			if ('navigation' == this.moduleFlavor) {
				this._navUpButton = this.own(new Button({
					label: _('Parent container'),
					callback: lang.hitch(this, function() {
						var path = this._tree.get('path');
						var ldapDN = path[ path.length - 2 ].id;
						this._tree.set('path', this._ldapDN2TreePath(ldapDN));
					})
				}))[0];
			}

			var model = new TreeModel({
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				moduleFlavor: this.moduleFlavor
			});

			this._tree = new Tree({
				model: model,
				persist: false,
				region: 'nav',
//				showRoot: 'navigation' == this.moduleFlavor,
				// customize the method getIconClass()
				getIconClass: function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
					return tools.getIconClass((item.icon || 'udm-container-cn') + '.png');
				}
			});
			if ('navigation' !== this.moduleFlavor) {
				// don't indent superordinates
				domStyle.set(this._tree.indentDetector, 'width', '1px');
			}
			this.own(this._tree.watch('path', lang.hitch(this, function(attr, oldVal, newVal) {
				this._searchForm.getWidget('objectType').reloadDynamicValues();
				// register for changes of the selected item (= path)
				// only take them into account in case the tree is not reloading
				if (!this._reloadingPath) {
					this._searchForm.ready().then(lang.hitch(this, 'filter'));
				} else if (this._reloadingPath == this._path2str(this._tree.get('path'))) {
					// tree has been reloaded to its last position
					this._reloadingPath = '';
				}
				this._grid.updateActionsVisibility();
			})));

			// add a context menu to edit/delete items
			var menu = new Menu({});
			menu.addChild(this._menuEdit = new MenuItem({
				label: _('Edit'),
				iconClass: 'umcIconEdit',
				onClick: lang.hitch(this, function() {
					this.createDetailPage('edit', this._navContextItem.objectType, this._navContextItem.id);
				})
			}));
			menu.addChild(this._menuDelete = new MenuItem({
				label: _('Delete'),
				iconClass: 'umcIconDelete',
				onClick: lang.hitch(this, function() {
					this.removeObjects([this._navContextItem]);
				})
			}));
			menu.addChild(this._menuMove = new MenuItem({
				label: _('Move to...'),
				onClick: lang.hitch(this, function() {
					this.moveObjects([this._navContextItem]);
				})
			}));
			menu.addChild(new MenuItem({
				label: _('Reload'),
				iconClass: 'umcIconRefresh',
				onClick: lang.hitch(this, 'reloadTree')
			}));

			// when we right-click anywhere on the tree, make sure we open the menu
			menu.bindDomNode(this._tree.domNode);
			this.own(menu);

			// disables items in the menu if the LDAP base is selected
			this.own(aspect.before(menu, '_openMyself', lang.hitch(this, function() {
				this._updateMenuAvailability();
			})));

			// remember on which item the context menu has been opened
			this.own(aspect.after(this._tree, '_onNodeMouseEnter', lang.hitch(this, function(node) {
				this._navContextItemFocused = node.item;
			}), true));
			this.own(aspect.before(menu, '_openMyself', lang.hitch(this, function() {
				this._navContextItem = this._navContextItemFocused;
			})));
			// in the case of changes, reload the navigation, as well (could have
			// changes referring to container objects)
			this.on('objectsaved', lang.hitch(this, function(dn, objectType) {
				this.resetPathAndReloadTreeAndFilter([dn]);
			}));

			// as the menu is displayed above the grid with the tree,
			// we need to adjust the dynamic size class of the grid
			// to account for this via an offset
			domClass.remove(this._grid._grid.domNode, 'umcDynamicHeight');
			domClass.add(this._grid._grid.domNode, 'umcDynamicHeight-55');
		},

		_canEdit: function(item) {
			return item.$operations$.indexOf('edit') !== -1;
		},

		_canMove: function(item) {
			if (tools.isTrue(this._ucr['ad/member'])) {
				return -1 === array.indexOf(item.$flags$, 'synced');
			}
			return item.$operations$.indexOf('move') !== -1;
		},

		_canCopy: function(item) {
			return item.$operations$.indexOf('copy') !== -1;
		},

		_canDelete: function(item) {
			if (tools.isTrue(this._ucr['ad/member'])) {
				return -1 === array.indexOf(item.$flags$, 'synced');
			}
			return item.$operations$.indexOf('remove') !== -1;
		},

		_updateMenuAvailability: function() {
			var operations = this._navContextItemFocused.$operations$;
			this._menuEdit.set('disabled', operations.indexOf('edit') === -1);
			this._menuDelete.set('disabled', operations.indexOf('remove') === -1 || !this._canDelete(this._navContextItemFocused));
			this._menuMove.set('disabled', operations.indexOf('move') === -1 || !this._canMove(this._navContextItemFocused));
		},

		_selectInputText: function() {
			if (has('touch')) {
				// ignore touch devices
				return;
			}

			// focus on input widget
			var widget = this._searchForm.getWidget('objectPropertyValue');
			widget.focus();

			// select the text
			var textbox = lang.getObject('_widget.textbox', false, widget);
			if (textbox) {
				try {
					_TextBoxMixin.selectInputText(textbox);
				}
				catch (err) { }
			}
		},

		_updateSearch: function() {
			// TODO: if we have "only" 2 object types and one is the virtual flavor we should select the other one!
			if ('navigation' != this.moduleFlavor) {
				var widgets = this._searchForm._widgets;
				var toggleButton = this._searchForm._buttons.toggleSearch;
				if (this._isAdvancedSearch) {
					widgets.objectType.set('visible', widgets.objectType.getAllItems().length > 1 /*2*/); // if 2 we have to select != all object types
					// now it gets dirty
					//   we do not have a fluid or dynamic layout
					//   DNS: we have the tree on the left -> only space for two widgets per row
					//        we want ['objectType', 'objectProperty', 'hidden'] normally but here
					//        only ['objectType', 'hidden'], ['objectProperty']
					//        we do this by switching hidden to the middle. objectProperty will
					//        be in the next row because of space limitations...
					//        but in DHCP we want ['objectProperty', 'hidden']...
					if (this._tree) {
						var hiddenLabel = widgets.hidden.getParent();
						if (widgets.objectType.get('visible') && this._tree) {
							var objectTypeLabel = widgets.objectType.getParent();
							hiddenLabel.placeAt(objectTypeLabel.domNode, 'after');
						} else {
							var objectPropertyLabel = widgets.objectProperty.getParent();
							hiddenLabel.placeAt(objectPropertyLabel.domNode, 'after');
						}
					}
					if ('container' in widgets) {
						widgets.container.set('visible', true);
						widgets.container._updateVisibility();
					}
					widgets.objectProperty.set('visible', true);
					widgets.objectProperty._updateVisibility();
					widgets.hidden.set('visible', true);
					//widgets.objectPropertyValue.set('visible', true);
					toggleButton.set('label', _('Simplified options'));
					toggleButton.set('iconClass', 'umcDoubleLeftIcon');
				} else {
					widgets.objectType.set('visible', false);
					if ('container' in widgets) {
						widgets.container.set('visible', false);
					}
					widgets.objectProperty.set('visible', false);
					widgets.hidden.set('visible', false);
					toggleButton.set('label', _('Advanced options'));
					toggleButton.set('iconClass', 'umcDoubleRightIcon');
				}
				this.layout();
			}

			// GUI setup is done when this method has been called for the first time
			if (!this._finishedDeferred.isFulfilled()) {
				this._finishedDeferred.resolve();
			}
		},

		_createReport: function (ids) {
			// open the dialog
			topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'grid', 'report');
			var _dialog = new CreateReportDialog( {
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring'),
				moduleFlavor: this.moduleFlavor,
				objects: ids,
				reports: this._reports
			});
			this.own(_dialog);
			_dialog.show();
		},

		moveObjects: function(ids) {
			var _selectLdapPosText = lang.hitch(this, function(n) {
				var text = {
					'users/user'          : _.ngettext('Please select an LDAP destination for the user:',
					                                    'Please select an LDAP destination for the %d selected users:', n),
					'groups/group'        : _.ngettext('Please select an LDAP destination for the group:',
					                                    'Please select an LDAP destination for the %d selected groups:', n),
					'computers/computer'  : _.ngettext('Please select an LDAP destination for the computer:',
					                                    'Please select an LDAP destination for the %d selected computers:', n),
					'networks/network'    : _.ngettext('Please select an LDAP destination for the network object:',
					                                    'Please select an LDAP destination for the %d selected network objects:', n),
					'dns/dns'             : _.ngettext('Please select an LDAP destination for the DNS object:',
					                                    'Please select an LDAP destination for the %d selected DNS objects:', n),
					'dhcp/dhcp'           : _.ngettext('Please select an LDAP destination for the DHCP object:',
					                                    'Please select an LDAP destination for the %d selected DHCP objects:', n),
					'shares/share'        : _.ngettext('Please select an LDAP destination for the share:',
					                                    'Please select an LDAP destination for the %d selected shares:', n),
					'shares/print'        : _.ngettext('Please select an LDAP destination for the printer:',
					                                    'Please select an LDAP destination for the %d selected printers:', n),
					'mail/mail'           : _.ngettext('Please select an LDAP destination for the mail object:',
					                                    'Please select an LDAP destination for the %d selected mail objects:', n),
					'nagios/nagios'       : _.ngettext('Please select an LDAP destination for the Nagios object:',
					                                    'Please select an LDAP destination for the %d selected Nagios objects:', n),
					'policies/policy'     : _.ngettext('Please select an LDAP destination for the policy:',
					                                    'Please select an LDAP destination for the %d selected policies:', n),
					'settings/portal_all' : _.ngettext('Please select an LDAP destination for the portal object:',
					                                    'Please select an LDAP destination for the %d selected portal objects:', n)
				}[this.moduleFlavor];
				if (!text) {
					text = _.ngettext('Please select an LDAP destination for the LDAP object:',
					                   'Please select an LDAP destination for the %d selected LDAP objects:', n);
				}
				return text;
			});
			var _moveLabelText = lang.hitch(this, function(n) {
				var text = {
					'users/user'          : _.ngettext('Move user', 'Move users', n),
					'groups/group'        : _.ngettext('Move group', 'Move groups', n),
					'computers/computer'  : _.ngettext('Move computer', 'Move computers', n),
					'networks/network'    : _.ngettext('Move network object', 'Move network objects', n),
					'dns/dns'             : _.ngettext('Move DNS object', 'Move DNS objects', n),
					'dhcp/dhcp'           : _.ngettext('Move DHCP object', 'Move DHCP objects', n),
					'shares/share'        : _.ngettext('Move share', 'Move shares', n),
					'shares/print'        : _.ngettext('Move printer', 'Move printers', n),
					'mail/mail'           : _.ngettext('Move mail object', 'Move mail objects', n),
					'nagios/nagios'       : _.ngettext('Move Nagios object', 'Move Nagios objects', n),
					'policies/policy'     : _.ngettext('Move policy', 'Move policies', n),
					'settings/portal_all' : _.ngettext('Move portal object', 'Move portal objects', n)
				}[this.moduleFlavor];
				if (!text) {
					text = _.ngettext('Move LDAP object', 'Move LDAP objects', n);
				}
				return text;
			});

			if (!ids.length) {
				return;
			}
			var objects = ids;
			ids = array.map(objects, function(object) { return object.id || object.$dn$; });

			var container = new ContainerWidget({});

			// add message to container widget
			var _content = _selectLdapPosText(ids.length);
			if (objects.length == 1) {
				var detail = lang.replace('<div>{0}</div>', [this.iconFormatter(objects[0])]);
				_content += detail;
			}
			container.addChild(new Text({
				content: '<p>' + _content + '</p>',
				style: 'width:300px;'
			}));

			// create the tree
			var model = new TreeModel({
				command: 'udm/move/container/query',
				umcpCommand: lang.hitch(this, 'umcpCommand')
			});
			var tree = new Tree({
				model: model,
				persist: false,
				style: 'width: 300px; height: 350px; margin-bottom: 20px;', // TODO does not work good on mobile
				// customize the method getIconClass()
				getIconClass: function(/*dojo.data.Item*/ item, /*Boolean*/ opened) {
					return tools.getIconClass((item.icon || 'udm-container-cn') + '.png');
				}
			});
			domStyle.set(tree._gridTree.domNode, 'height', '100%');
			container.addChild(tree);

			// add footer message
			container.addChild(new Text({
				content: '<p>' + _('Note that moving a container can take some time.') + '</p>',
				style: 'width:300px;'
			}));
			container.startup();

			// cleanup function
			var _cleanup = function() {
				container.destroyRecursive();
			};

			// ask for confirmation
			dialog.confirm(container, [{
				name: 'cancel',
				'default': true,
				label: _('Cancel')
			}, {
				name: 'move',
				label: _moveLabelText(objects.length)
			}]).then(lang.hitch(this, function(response) {
				if (response != 'move') {
					_cleanup();
					return;
				}

				// check whether a LDAP position has been selected
				var path = tree.get('path');
				if (!path || !path.length) {
					dialog.alert(_('No LDAP position has been selected.'));
					_cleanup();
					return;
				}

				// reset cache if extended attribute or user template is being moved
				this._reloadCache(objects);

				// prepare data array
				var params = [];
				array.forEach(ids, function(idn) {
					params.push({
						'object': idn,
						options: { container: path[path.length - 1].id }
					});
				}, this);

				// send UMCP command to move the objects
				this._progressBar.reset();
				var moveOperation = this.umcpProgressCommand(this._progressBar, 'udm/move', params).then(
					lang.hitch(this, function(result) {

						// check whether everything went alright
						var allSuccess = true;
						var msg = '<p>' + _('Failed to move the following objects:') + '</p><ul>';
						array.forEach(result, function(iresult) {
							allSuccess = allSuccess && iresult.success;
							if (!iresult.success) {
								msg += '<li>' + iresult.$dn$ + ': ' + iresult.details + '</li>';
							}
						}, this);
						msg += '</ul>';
						if (!allSuccess) {
							dialog.alert(msg);
						}

						// clear the selected objects
						this.moduleStore.onChange();
						this.resetPathAndReloadTreeAndFilter(ids);
					})
				);
				this.standbyDuring(moveOperation, this._progressBar);

				_cleanup();
			}));
		},

		// helper function that converts a path into a string
		// store original path and reload tree
		_path2str: function(path) {
			if (!(path instanceof Array)) {
				return '';
			}
			return json.stringify(array.map(path, function(i) {
				return i.id;
			}));
		},

		resetPathAndReloadTreeAndFilter: function(modifiedDNs) {
			if (this._tree && modifiedDNs.length) {
				var notTouched = true;
				var path = array.filter(this._tree.get('path'), function(part) {
					if (modifiedDNs.indexOf(part.id) > -1) {
						// if touched, set notTouched
						// to false for this and every
						// following part
						notTouched = false;
					}
					return notTouched;
				});
				if (path.length === 0) {
					// user modified the root
					path = [ this._tree.model.root ];
				}
				this._tree.set('path', path);
				this.reloadTree();
			}
			this.filter();
		},

		reloadTree: function() {
			// set the internal variable that indicates whether the tree is reloading
			// or not to 'false' as soon as the tree has been reloaded
			this._reloadingPath = this._path2str(this._tree.get('path'));
			this._tree.reload();
		},

		iconFormatter: function(value, item) {
			// summary:
			//		Formatter method that adds in a given column of the search grid icons
			//		according to the object types.

			if (item === undefined) {
				item = value;
				value = lang.replace('{0} (<em>{1}</em>)', [item.name || item.label, item.path || item.id]);
			}
			// get the iconName
			var iconName = item.objectType || '';
			iconName = iconName.replace('/', '-');

			// create an HTML image that contains the icon (if we have a valid iconName)
			var result = value;
			if (iconName) {
				result = lang.replace('<img src="{src}" height="{height}" width="{width}" style="float:left; margin-right: 5px" /> {value}', {
					icon: iconName,
					height: '16px',
					width: '16px',
					value: value,
					src: require.toUrl(lang.replace('dijit/themes/umc/icons/16x16/udm-{0}.png', [iconName]))
				});
			}
			return result;
		},

		identityProperty: function() {
			return array.filter(this._searchForm._widgets.objectProperty.getAllItems(), function(item) {
				return item.identifies;
			})[0] || null;
		},

		getDefaultColumns: function() {
			var objectType = this._searchForm ? this._searchForm._widgets.objectType.get('value') : (this.moduleFlavor == 'navigation' ? 'container/cn' : this.moduleFlavor);
			return cache.get(this.moduleFlavor).getMetaInfo(objectType).then(lang.hitch(this, function(metaInfo) {
				var customColumns = (metaInfo ? metaInfo.columns : []) || [];
				var defaultFormatter = function(value) {
					if (value instanceof Array) {
						var tooMuch = value.length > 3;
						value = array.map(value.slice(0, 3), function(v) { return entities.encode(String(v)); }).join('<br>');
						if (tooMuch) {
							value += ', …';
						}
					}
					return value;
				};
				var nameColumn = {
					name: 'name',
					label: _('Name'),
					description: _('Name of the LDAP object.'),
					formatter: lang.hitch(this, 'iconFormatter')
				};
				var typeColumn = {
					name: 'labelObjectType',
					label: _('Type')
				};
				var pathColumn = {
					name: 'path',
					label: _('Path'),
					description: _('Path of the LDAP object.')
				};
				var valueColumn = {
					name: '$value$',
					label: _('Value'),
					formatter: function(value) {
						if (value instanceof Array) {
							value = array.map(array.filter(value, function(v) { return v; }), function(v) { return defaultFormatter(v).replace(/<br>/g, ', '); });
							value = array.filter(value, function(v) { return v; }).join('<br>');
						}
						return value;
					},
					description: _('Value of the LDAP object.')
				};

				var identifies = this._searchForm ? this.identityProperty() : null;
				var selected_value = this._searchForm ? this._searchForm._widgets.objectProperty.get('value') : 'None';
				var numObjTypes = this._searchForm ? this._searchForm._widgets.objectType.getNumItems() : 3;
				var columns = [nameColumn];
				// if we are searching for a specific property add it to the columns
				if ('None' != selected_value && (identifies === null || selected_value != identifies.id) && array.every(customColumns, function(column) { return column.name != selected_value; })) {
					columns.push({
						name: selected_value,
						label: this._searchForm._widgets.objectProperty.get('displayedValue')
					});
				}
				columns = columns.concat(array.map(customColumns, function(col) { return lang.mixin({formatter: defaultFormatter}, col); }));
				if (~array.indexOf(['dns/dns'/*, 'dhcp/dhcp'*/], objectType)) {
//				if (customColumns.length) {
					columns.push(valueColumn);
				}
				if (this._tree || numObjTypes > 2) {
					columns.push(typeColumn);
				}
				if (!(~columns.indexOf(valueColumn))) {
					columns.push(pathColumn);
				}
				return columns;
			}));
		},

		_getValueAttr: function() {
			var values = this._searchForm.inherited(arguments);
			if (this._tree) {
				// the tree view (navigation, DHCP, DNS) might contain containers (e.g. also underneath of a superordinate!)
				// we need to set the currently selected container if it's not a superordinate
				var path = lang.clone(this._tree.get('path'));
				if (path.length) {
					values.container = path[path.length - 1].id;
				}
			}
			if (values.superordinate) {
				// a superordinate is selected in the tree. only show the direct children of it!
				values.scope = 'one';
			}
			return values;
		},

		filter: function() {
			// summary:
			//		Send a new query with the given filter options as specified in the search form
			//		and (for the UDM navigation) the selected container.

			this.getDefaultColumns().then(lang.hitch(this, function(columns) {
				var vals = this._searchForm.get('value');
				vals.fields = array.map(columns, function(column) { return column.name; });
				if ('navigation' != this.moduleFlavor || this._tree.get('path').length) {
					this._grid.filter(vals);
				}
				this._grid.set('columns', columns);
			}));
		},

		removeObjects: function(/*String|String[]*/ _ids, /*Boolean?*/ isContainer, /*Boolean?*/ cleanup, /*Boolean?*/ recursive) {
			var _msg = lang.hitch(this, function(n) {
				var text = {
					'users/user'          : _.ngettext('Please confirm the removal of the user:',
					                                    'Please confirm the removal of the %d selected users', n),
					'groups/group'        : _.ngettext('Please confirm the removal of the group:',
					                                    'Please confirm the removal of the %d selected groups', n),
					'computers/computer'  : _.ngettext('Please confirm the removal of the computer:',
					                                    'Please confirm the removal of the %d selected computers', n),
					'networks/network'    : _.ngettext('Please confirm the removal of the network object:',
					                                    'Please confirm the removal of the %d selected network objects', n),
					'dns/dns'             : _.ngettext('Please confirm the removal of the DNS object:',
					                                    'Please confirm the removal of the %d selected DNS objects', n),
					'dhcp/dhcp'           : _.ngettext('Please confirm the removal of the DHCP object:',
					                                    'Please confirm the removal of the %d selected DHCP objects', n),
					'shares/share'        : _.ngettext('Please confirm the removal of the share:',
					                                    'Please confirm the removal of the %d selected shares', n),
					'shares/print'        : _.ngettext('Please confirm the removal of the printer:',
					                                    'Please confirm the removal of the %d selected printers', n),
					'mail/mail'           : _.ngettext('Please confirm the removal of the mail object:',
					                                    'Please confirm the removal of the %d selected mail objects', n),
					'nagios/nagios'       : _.ngettext('Please confirm the removal of the Nagios object:',
					                                    'Please confirm the removal of the %d selected Nagios objects', n),
					'policies/policy'     : _.ngettext('Please confirm the removal of the policy:',
					                                    'Please confirm the removal of the %d selected ploicies', n),
					'settings/portal_all' : _.ngettext('Please confirm the removal of the portal object:',
					                                    'Please confirm the removal of the %d selected portal objects', n)
				}[this.moduleFlavor];
				if (!text) {
					text = _.ngettext('Please confirm the removal of the LDAP object:',
					                   'Please confirm the removal of the %d selected LDAP objects', n);
				}
				return text;
			});
			// summary:
			//		Remove the selected LDAP objects.

			// default values
			isContainer = isContainer === undefined ? false : isContainer;
			cleanup = cleanup === undefined ? true : cleanup;
			recursive = undefined === recursive ? true : recursive;

			// get an object
			var objects = _ids instanceof Array ? _ids : (_ids ? [ _ids ] : []);
			var ids = array.map(objects, function(object) { return object.id || object.$dn$; });

			// ignore empty array
			if (!objects.length) {
				return;
			}

			// let user confirm deletion
			var msg = _msg(objects.length);
			if (objects.length == 1) {
				msg += lang.replace('<div>{0}</div>', [this.iconFormatter(objects[0])]);
			}

			var _dialog = null, form = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
				form.destroyRecursive();
			};

			var _remove = lang.hitch(this, function() {
				// enable standby animation
				this.standby(true);

				// reset cache if extended attribute or user template is being removed
				this._reloadCache(objects);

				// set the options
				var options = {
					cleanup: form.getWidget('deleteReferring').get('value'),
					recursive: recursive
				};

				if (this._tree && this._tree.get('selectedItems')[0].id == ids[0]) {
					// when we are removing objects which are selected in the tree
					// a reload would fail... reset the tree path to the top/root element
					this._tree.set('path', [this._tree.model.root]);
				}

				// remove the selected elements via a transaction on the module store
				var transaction = this.moduleStore.transaction();
				array.forEach(ids, function(iid) {
					this.moduleStore.remove(iid, options);
				}, this);
				this.standbyDuring(transaction.commit()).then(lang.hitch(this, function(data) {

					// see whether all objects could be removed successfully
					var success = true;
					var message = '<p>' + _('The following object(s) could not be deleted:') + '</p><ul>';
					array.forEach(data, function(iresult) {
						if (!iresult.success) {
							success = false;
							message += '<li>' + iresult.$dn$ + ': ' + iresult.details;
						}
					}, this);
					message += '</ul>';

					// show an alert in case something went wrong
					if (!success) {
						dialog.alert(message);
					}

					this.resetPathAndReloadTreeAndFilter(ids);
				}));

				// remove dialog
				_cleanup();
			});

			// build a small form with a checkbox to mark whether or not referring
			// objects are deleted, as well
			form = new Form({
				widgets: [{
					type: Text,
					label: '',
					name: 'text',
					content: '<p>' + msg + '</p>'
				}, {
					type: CheckBox,
					label: _('Delete referring objects.'),
					name: 'deleteReferring',
					value: cleanup
				}],
				buttons: [{
					name: 'submit',
					label: _('Cancel'),
					callback: _cleanup
				}, {
					name: 'remove',
					label: _('Delete'),
					callback: _remove
				}]
				//layout: [ 'text', [ 'deleteReferring', 'submit' ] ]
			});

			_dialog = new Dialog({
				title: _('Delete objects'),
				content: form,
				'class': 'umcPopup'
			});
			_dialog.show();
		},

		showNewObjectDialog: function() {
			this._showNewObjectDialog({
				args: {},
				callback: lang.hitch(this, function(options) {
					this.createDetailPage('add', options.objectType, undefined, options);
				})
			});
		},

		_showNewObjectDialog: function(args) {
			// summary:
			//		Open a user dialog for creating a new LDAP object.

			// when we are in navigation mode, make sure the user has selected a container
			var selectedContainer = { id: '', label: '', path: '' };
			var superordinate = { id: '', label: '', path: '' };

			if (this._tree) {
				var items = this._tree.get('selectedItems');
				if (!items.length) {
					dialog.alert(_('Please select a container in the LDAP directory tree. The new object will be placed at this location.'));
					return;  // cannot happen!?
				}
				if (this.moduleFlavor == 'navigation' || this._tree.get('path').length >= 2) {
					// the tree root is not a default container of DHCP / DNS !
					selectedContainer = items[0];
				}
			}

			var superordinateWidget = this._searchForm.getWidget('superordinate');
			if (superordinateWidget && superordinateWidget.get('value')) {  // validate that the selected item in the tree is a superordinate
				superordinate = superordinateWidget.get('value');
				superordinate = {id: superordinate, label: superordinate, path: superordinate};
			}

			// open the dialog
			var onHandlerRegistered = new Deferred();
			this._newObjectDialog = new NewObjectDialog(lang.mixin({
				addNotification: lang.hitch(this, 'addNotification'),
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				wizardsDisabled: tools.isTrue(this._wizardsDisabled),
				mayCreateWizard: onHandlerRegistered,
				moduleFlavor: this.moduleFlavor,
				moduleCache: cache.get(this.moduleFlavor),
				selectedContainer: selectedContainer,
				selectedSuperordinate: superordinate,
				defaultObjectType: this._ucr['directory/manager/web/modules/' + this.moduleFlavor + '/add/default'] || null
			}, args.args));
			this._newObjectDialog.on('FirstPageFinished', args.callback);
			this._newObjectDialog.on('Done', lang.hitch(this, function() {
				if (this._newObjectDialog) {
					this._newObjectDialog.destroyRecursive();
					this._newObjectDialog = null;
				}
				this.selectChild(this._detailPage);
			}));
			this._newObjectDialog.on('hide', lang.hitch(this, function() {
				this._newObjectDialog.destroyRecursive();
				this._newObjectDialog = null;
			}));
			this._newObjectDialog.on('cancel', lang.hitch(this, function() {
				this.closeDetailPage();
			}));
			onHandlerRegistered.resolve();
			if (!this._newObjectDialog) {
				return; // already destroyed
			}
			this.standbyDuring(this._newObjectDialog.canContinue);
			this._newObjectDialog.canContinue.then(
				lang.hitch(this, function() {
					// wizard continues immediately! Show only
					// if (and only if) the createWizard is ready
					this.standbyDuring(this._newObjectDialog.createWizardAdded);
					this._newObjectDialog.createWizardAdded.then(lang.hitch(this, function() {
						this._newObjectDialog.show();
					}));
				}),
				lang.hitch(this, function() {
					// canContinue.rejected! Ask the user
					this._newObjectDialog.show().then(lang.hitch(this, function() {
						this._newObjectDialog.focusNextOnFirstPage();
					}));
				})
			);
		},

		_preloadDetailPage: function() {
			if (this._detailPage) {
				return;
			}
			this._ldapNameDeferred = new Deferred();
			if (this.moduleFlavor != this._preloadedObjectType || this.openObject) {
				// make sure that only users/user is preloaded
				// but do not preload if the module is opened with an user object to edit directly
				return;
			}

			this._setDetailPage(
				'edit',
				this._preloadedObjectType,
				this._ldapNameDeferred,
				/*newObjectOptions*/ null,
				/*isClosable*/ false,
				/*note*/ null
			);
		},

		_setDetailPage: function(operation, objectType, ldapName, newObjOptions, /*Boolean*/ isClosable, /*String*/ note) {
			this._destroyDetailPage();
			this._detailPage = new DetailPage({
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				addWarning: lang.hitch(this, 'addWarning'),
				addNotification: lang.hitch(this, 'addNotification'),
				moduleStore: this.moduleStore,
				moduleFlavor: this.moduleFlavor,
				objectType: objectType,
				operation: operation,
				ldapBase: this._ucr['ldap/base'],
				ldapName: ldapName,
				newObjectOptions: newObjOptions,
				moduleWidget: this,
				isClosable: isClosable,
				note: note || null
			});
			this.addChild(this._detailPage);
		},

		createDetailPage: function(operation, objectType, ldapName, newObjOptions, /*Boolean?*/ isClosable, /*String?*/ note) {
			// summary:
			//		Creates and views the detail page for editing LDAP objects if it doesn't exists. Afterwards it opens the detailpage.
			if (!this._ldapNameDeferred) {
				this._preloadDetailPage();
			}
			if (operation === 'copy') {
				this._setDetailPage(operation, objectType, ldapName, newObjOptions, isClosable, note);
				this._ldapNameDeferred.resolve(ldapName);
			} else if (this._detailPage && this._preloadedObjectType == this.moduleFlavor && ldapName && !(ldapName instanceof Array)) {
				// use pre-rendered detail page when loading a (single) object
				this._ldapNameDeferred.resolve(ldapName);
			} else {
				this._setDetailPage(operation, objectType, ldapName, newObjOptions, isClosable, note);
				this._ldapNameDeferred.resolve(null);
			}

			this._detailPage.on('closeTab', lang.hitch(this, 'closeDetailPage'));
			this._detailPage.on('save', lang.hitch(this, 'onObjectSaved'));
			this._detailPage.on('focusModule', lang.hitch(this, 'focusModule'));
			if (this._newObjectDialog) {
				var getFromDetailPage = {
					properties: this._detailPage.propertyQuery,
					template: this._detailPage.templateQuery
				};
				all(getFromDetailPage).then(lang.hitch(this, function(results) {
					var properties = results.properties;
					var template = results.template && results.template.result;
					if (template && template.length > 0) {
						template = template[0];
					} else {
						template = null;
					}
					this._newObjectDialog.setDetails(this._detailPage, template, properties);
				}));
			} else {
				this.selectChild(this._detailPage);
			}

			// close detailPage if something failed
			this._detailPage.ready().then(
				null,
				lang.hitch(this, 'closeDetailPage')
			);

		},

		_destroyDetailPage: function() {
			if (this._detailPage) {
				var oldDetailPage = this._detailPage;
				this.removeChild(oldDetailPage);
				this._detailPage = null;
				tools.defer(function() {
					oldDetailPage.destroyRecursive();
				}, 10);
			}
		},

		closeDetailPage: function() {
			// summary:
			//		Closes the detail page for editing LDAP objects.

			// in case the detail page was "closable", we need to close the module
			if (this._detailPage && this._detailPage.isClosable) {
				topic.publish('/umc/tabs/close', this);
				return;
			}

			this._destroyDetailPage();
			this.selectChild(this._searchPage);
			this._preloadDetailPage();
			this.resetTitle();
		},

		focusModule: function() {
			// focus this module tab
			topic.publish("/umc/tabs/focus", this);
		},

		onObjectSaved: function(dn, objectType) {
			// event stub
		},

		onCloseTab: function() {
			// event stub
		}
	});
	return {
		load: function (params, req, load, config) {
			if (params == 'license-import') {
				require(['umc/modules/udm/license'], function(license) {
					load(license);
				});
				return;
			}
			load(udm);
		}
	};
});

// add pseudo translations for UDM tab names in order to enable
// resolving tab names for umc/actions publishing...
// the tab names are already translated in the backend and javascript
// has otherwise no mean to find the corresponding English original

/***** BEGIN *****
_('Access control');
_('Access Rights');
_('Account');
_('Allow/Deny');
_('Boot');
_('Change password');
_('Contact');
_('Data type');
_('DHCP statements');
_('DNS Update');
_('Employee');
_('General');
_('Groups');
_('Hosts');
_('IP addresses');
_('KDE Profiles');
_('LDAP');
_('Lease Time');
_('License');
_('Linux');
_('Mail');
_('MX records');
_('Netbios');
_('NFS');
_('Primary Groups');
_('Samba');
_('Start of authority');
_('TXT records');
_('UDM General');
_('UDM Web');
_('User Account');
_('User Contact');
_('Windows');
****** END ******/
