/**
 * DimpBase.js - Javascript used in the base DIMP page.
 *
 * $Horde: dimp/js/src/DimpBase.js,v 1.1.2.118 2009-05-20 18:27:51 slusarz Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var DimpBase = {
    // Vars used and defaulting to null/false:
    //   filtertoggle, fl_visible, folder, folderswitch, fspecial, isvisible,
    //   message_list_template, offset, pollpe, pp, searchobserve, uid,
    //   viewport
    bcache: $H(),
    delay_onload: (!Prototype.Browser.Gecko && !Prototype.Browser.Opera),
    lastrow: -1,
    mo_sidebar: $H(),
    pivotrow: -1,
    ppcache: $H(),
    ppfifo: [],
    showPreview: DIMP.conf.preview_pref,

    sfiltersfolder: $H({ sf_all: 'all', sf_current: 'current' }),
    sfilters: $H({ sf_msgall: 'msgall', sf_from: 'from', sf_to: 'to', sf_subject: 'subject' }),

    unseen_regex: new RegExp("(^|\\s)unseen(\\s|$)"),

    // Message selection functions

    // vs = (ViewPort_Selection) A ViewPort_Selection object.
    // opts = (object) Boolean options [delay, right]
    _select: function(vs, opts)
    {
        var d = vs.get('rownum');
        if (d.size() == 1) {
            this.lastrow = this.pivotrow = d.first();
        }

        this.toggleButtons();

        if ($('previewPane').visible()) {
            if (opts.right) {
                this.clearPreviewPane();
            } else {
                if (opts.delay) {
                    (this.bcache.get('initPP') || this.bcache.set('initPP', this.initPreviewPane.bind(this))).delay(opts.delay);
                } else {
                    this.initPreviewPane();
                }
            }
        }
    },

    // vs = (ViewPort_Selection) A ViewPort_Selection object.
    // opts = (object) Boolean options [right]
    _deselect: function(vs, opts)
    {
        var sel = this.viewport.getSelected(),
            count = sel.size();
        if (!count) {
            this.lastrow = this.pivotrow = -1;
        }

        this.toggleButtons();
        if (opts.right || !count) {
            this.clearPreviewPane();
        } else if ((count == 1) && $('previewPane').visible()) {
            this._loadPreview(sel.get('dataob').first());
        }
    },

    // id = (string) DOM ID
    // opts = (Object) Boolean options [ctrl, right, shift]
    msgSelect: function(id, opts)
    {
        var bounds,
            row = this.viewport.createSelection('domid', id),
            rownum = row.get('rownum').first(),
            sel = this.isSelected('domid', id),
            selcount = this.selectedCount();

        this.lastrow = rownum;

        // Some browsers need to stop the mousedown event before it propogates
        // down to the browser level in order to prevent text selection on
        // drag/drop actions.  Clicking on a message should always lose focus
        // from the search input, because the user may immediately start
        // keyboard navigation after that. Thus, we need to ensure that a
        // message click loses focus on the search input.
        $('msgList_filter').blur();

        if (opts.shift) {
            if (selcount) {
                if (!sel || selcount != 1) {
                    bounds = [ rownum, this.pivotrow ];
                    this.viewport.select($A($R(bounds.min(), bounds.max())), { range: true });
                }
                return;
            }
        } else if (opts.ctrl) {
            this.pivotrow = rownum;
            if (sel) {
                this.viewport.deselect(row, { right: opts.right });
                return;
            } else if (opts.right || selcount) {
                this.viewport.select(row, { add: true, right: opts.right });
                return;
            }
        }

        this.viewport.select(row, { right: opts.right });
    },

    selectAll: function()
    {
        this.viewport.select($A($R(1, this.viewport.getMetaData('total_rows'))), { range: true });
    },

    isSelected: function(format, data)
    {
        return this.viewport.getSelected().contains(format, data);
    },

    selectedCount: function()
    {
        return (this.viewport) ? this.viewport.getSelected().size() : 0;
    },

    resetSelected: function()
    {
        if (this.viewport) {
            this.viewport.deselect(this.viewport.getSelected(), { clearall: true });
        }
        this.toggleButtons();
        this.clearPreviewPane();
    },

    // absolute = Is num an absolute row number - from 1 -> page_size (true) -
    //            or a relative change from the current selected value (false)
    //            If no current selected value, the first message in the
    //            current viewport is selected.
    moveSelected: function(num, absolute)
    {
        var curr, curr_row, row, row_data, sel;

        if (absolute) {
            if (!this.viewport.getMetaData('total_rows')) {
                return;
            }
            curr = num;
        } else {
            if (num == 0) {
                return;
            }

            sel = this.viewport.getSelected();
            switch (sel.size()) {
            case 0:
                curr = this.viewport.currentOffset();
                curr += (num > 0) ? 1 : this.viewport.getPageSize('current');
                break;

            case 1:
                curr_row = sel.get('dataob').first();
                curr = curr_row.rownum + num;
                break;

            default:
                sel = sel.get('rownum');
                curr = (num > 0 ? sel.max() : sel.min()) + num;
                break;
            }
            curr = (num > 0) ? Math.min(curr, this.viewport.getMetaData('total_rows')) : Math.max(curr, 1);
        }

        row = this.viewport.createSelection('rownum', curr);
        if (row.size()) {
            row_data = row.get('dataob').first();
            if (!curr_row || row_data.imapuid != curr_row.imapuid) {
                this.viewport.scrollTo(row_data.rownum);
                this.viewport.select(row, { delay: 0.3 });
            }
        } else {
            this.offset = curr;
            this.viewport.requestContentRefresh(curr - 1);
        }
    },
    // End message selection functions

    go: function(loc, data)
    {
        var app, f, separator;

        if (loc.startsWith('compose:')) {
            return;
        }

        if (loc.startsWith('msg:')) {
            separator = loc.indexOf(':', 4);
            f = loc.substring(4, separator);
            this.uid = loc.substring(separator + 1);
            loc = 'folder:' + f;
            // Now fall through to the 'folder:' check below.
        }

        if (loc.startsWith('folder:')) {
            f = loc.substring(7);
            if (this.folder != f || !$('dimpmain_folder').visible()) {
                this.highlightSidebar(this.getFolderId(f));
                if (!$('dimpmain_folder').visible()) {
                    $('dimpmain_portal').hide();
                    $('dimpmain_folder').show();
                }
                // This catches the refresh case - no need to re-add to history
                if (!Object.isUndefined(this.folder)) {
                    this._addHistory(loc);
                }
            }
            this.loadFolder(f);
            return;
        }

        this.folder = null;
        $('dimpmain_folder').hide();
        $('dimpmain_portal').update(DIMP.text.loading).show();

        if (loc.startsWith('app:')) {
            app = loc.substr(4);
            if (app == 'imp' || app == 'dimp') {
                this.go('folder:INBOX');
                return;
            }
            this.highlightSidebar('app' + app);
            this._addHistory(loc, data);
            if (data) {
                this.iframeContent(loc, data);
            } else if (DIMP.conf.app_urls[app]) {
                this.iframeContent(loc, DIMP.conf.app_urls[app]);
            }
            return;
        }

        switch (loc) {
        case 'portal':
            this.highlightSidebar('appportal');
            this._addHistory(loc);
            DimpCore.setTitle(DIMP.text.portal);
            DimpCore.doAction('ShowPortal', {}, [], this.bcache.get('portalC') || this.bcache.set('portalC', this._portalCallback.bind(this)));
            break;

        case 'options':
            this.highlightSidebar('appoptions');
            this._addHistory(loc);
            DimpCore.setTitle(DIMP.text.prefs);
            this.iframeContent(loc, DIMP.conf.prefs_url);
            break;
        }
    },

    _addHistory: function(loc, data)
    {
        if (Horde.dhtmlHistory.getCurrentLocation() != loc) {
            Horde.dhtmlHistory.add(loc, data);
        }
    },

    highlightSidebar: function(id)
    {
        // Folder bar may not be fully loaded yet.
        if ($('foldersLoading').visible()) {
            this.highlightSidebar.bind(this, id).defer();
            return;
        }

        $('sidebarPanel').select('.on').invoke('removeClassName', 'on');

        var elt = $(id);
        if (!elt) {
            return;
        }
        if (!elt.match('LI')) {
            elt = elt.up();
            if (!elt) {
                return;
            }
        }
        elt.addClassName('on');

        // Make sure all subfolders are expanded
        elt.ancestors().find(function(n) {
            if (n.hasClassName('subfolders')) {
                this._toggleSubFolder(n.id.substring(3), 'exp');
            } else {
                return (n.id == 'foldersSidebar');
            }
        }, this);
    },

    iframeContent: function(name, loc)
    {
        if (name === null) {
            name = loc;
        }

        var container = $('dimpmain_portal'), iframe;
        if (!container) {
            DimpCore.showNotifications([ { type: 'horde.error', message: 'Bad portal!' } ]);
            return;
        }

        iframe = new Element('IFRAME', { id: 'iframe' + name, className: 'iframe', frameBorder: 0, src: loc });
        this._resizeIE6Iframe(iframe);

        // Hide menu in prefs pages.
        if (name == 'options') {
            iframe.observe('load', function() { $('iframeoptions').contentWindow.document.getElementById('menu').style.display = 'none'; });
        }

        container.insert(iframe);
    },

    // r = ViewPort row data
    msgWindow: function(r)
    {
        this.updateUnseenUID(r, 0);
        var url = DIMP.conf.message_url;
        url += (url.include('?') ? '&' : '?') +
               $H({ folder: r.view,
                    uid: r.imapuid }).toQueryString();
        DimpCore.popupWindow(url, 'msgview' + r.view + r.imapuid);
    },

    composeMailbox: function(type)
    {
        var sel = this.viewport.getSelected();
        if (!sel.size()) {
            return;
        }
        sel.get('dataob').each(function(s) {
            DimpCore.compose(type, { folder: s.view, uid: s.imapuid });
        });
    },

    loadFolder: function(f, background)
    {
        if (!this.viewport) {
            this._createViewPort();
        }

        if (!background) {
            this.resetSelected();

            if (this.folder == f) {
                this.searchfilterClear(false);
                return;
            }

            this.searchfilterClear(true);
            $('folderName').update(DIMP.text.loading);
            $('msgHeader').update();
            this.folderswitch = true;
            this.folder = f;
        }

        this.viewport.loadView(f, { folder: f }, this.uid ? { imapuid: DimpCore.toUIDString(this.uid, f) } : null, background);
    },

    _createViewPort: function()
    {
        var mf = $('msgList_filter'),
            // No need to cache - this function only called once.
            settitle = this.setMessageListTitle.bind(this);

        this.viewport = new ViewPort({
            content_container: 'msgList',
            empty_container: 'msgList_empty',
            error_container: 'msgList_error',
            fetch_action: 'ListMessages',
            template: this.message_list_template,
            buffer_pages: DIMP.conf.buffer_pages,
            limit_factor: DIMP.conf.limit_factor,
            viewport_wait: DIMP.conf.viewport_wait,
            show_split_pane: this.showPreview,
            split_pane: 'previewPane',
            splitbar: 'splitBar',
            content_class: 'msglist',
            row_class: 'msgRow',
            selected_class: 'selectedRow',
            ajaxRequest: DimpCore.doAction.bind(DimpCore),
            norows: true,
            onScrollIdle: settitle,
            onSlide: settitle,
            onViewChange: function() {
                DimpCore.addGC(this.viewport.visibleRows());
            }.bind(this),
            onContent: function(rows) {
                var mf, search,
                    thread = ((this.viewport.getMetaData('sortby') == DIMP.conf.sortthread) && this.viewport.getMetaData('thread'));
                if (this.viewport.isFiltering()) {
                    search = this.sfilters.get(this._getSearchfilterField()).capitalize();
                    mf = new RegExp("(" + $F('msgList_filter') + ")", "i");
                }
                rows.get('dataob').each(function(row) {
                    var elt, tmp, u,
                        r = $(row.domid);
                    // Add thread graphics
                    if (thread && thread[row.imapuid]) {
                        elt = r.down('.msgSubject');
                        tmp = elt.cloneNode(false);
                        u = thread[row.imapuid];
                        $R(0, u.length, true).each(function(i) {
                            tmp.insert($($('thread_img_' + u.charAt(i)).cloneNode(false)).writeAttribute('id', ''));
                        });
                        elt.replace(tmp.insert(elt.getText().escapeHTML()));
                    }
                    // Add attachment graphics
                    if (row.atc) {
                        r.down('.msgSize').insert({ top: $($('atc_img_' + row.atc).cloneNode(false)).writeAttribute('id', '') });
                    }

                    // Add context menu.
                    DimpCore.addMouseEvents({ id: row.domid, type: row.menutype });

                    // Highlight search terms
                    if (search == 'From' || search == 'Subject') {
                        elt = r.down('.msg' + search);
                        elt.update(elt.getText().escapeHTML().gsub(mf, '<span class="searchMatch">#{1}</span>'));
                    }
                }, this);
                this.setMessageListTitle();
            }.bind(this),
            onComplete: function() {
                var row, ssc,
                    l = this.viewport.getMetaData('label');

                if (this.uid) {
                    row = this.viewport.getViewportSelection().search({ imapuid: { equal: [ this.uid ] }, view: { equal: [ this.folder ] } });
                    if (row.size()) {
                        this.viewport.scrollTo(row.get('rownum').first());
                        this.viewport.select(row);
                    }
                } else if (this.offset) {
                    this.viewport.select(this.viewport.createSelection('rownum', this.offset));
                }
                this.offset = this.uid = null;

                // 'label' will not be set if there has been an error
                // retrieving data from the server.
                l = this.viewport.getMetaData('label');
                if (l) {
                    $('folderName').update(l);
                }

                if (this.folderswitch) {
                    this.folderswitch = false;
                    if (this.folder == DIMP.conf.spam_folder) {
                        if (!DIMP.conf.spam_spamfolder &&
                            DimpCore.buttons.indexOf('button_spam') != -1) {
                            [ $('button_spam').up(), $('ctx_message_spam') ].invoke('hide');
                        }
                        if (DimpCore.buttons.indexOf('button_ham') != -1) {
                            [ $('button_ham').up(), $('ctx_message_ham') ].invoke('show');
                        }
                    } else {
                        if (DimpCore.buttons.indexOf('button_spam') != -1) {
                            [ $('button_spam').up(), $('ctx_message_spam') ].invoke('show');
                        }
                        if (DimpCore.buttons.indexOf('button_ham') != -1) {
                            if (DIMP.conf.ham_spamfolder) {
                                [ $('button_ham').up(), $('ctx_message_ham') ].invoke('hide');
                            } else {
                                [ $('button_ham').up(), $('ctx_message_ham') ].invoke('show');
                            }
                        }
                    }
                } else if (this.filtertoggle) {
                    if (this.filtertoggle == 1 &&
                        this.viewport.getMetaData('sortby') == DIMP.conf.sortthread) {
                        ssc = DIMP.conf.sortdate;
                    }
                    this.filtertoggle = 0;
                }

                this.setSortColumns(ssc);

                if (this.viewport.isFiltering()) {
                    this.resetSelected();
                    this.updateTitle();
                } else {
                    this.setFolderLabel(this.folder, this.viewport.getMetaData('unseen'));
                }
            }.bind(this),
            onFetch: this.msgListLoading.bind(this, true),
            onEndFetch: this.msgListLoading.bind(this, false),
            onWait: function() {
                if ($('dimpmain_folder').visible()) {
                    DimpCore.showNotifications([ { type: 'horde.warning', message: DIMP.text.listmsg_wait } ]);
                }
            },
            onFail: function() {
                if ($('dimpmain_folder').visible()) {
                    DimpCore.showNotifications([ { type: 'horde.error', message: DIMP.text.listmsg_timeout } ]);
                }
                this.msgListLoading(false);
            }.bind(this),
            onFirstContent: function() {
                this.clearPreviewPane();
                $('msgList').observe('dblclick', this._handleMsgListDblclick.bindAsEventListener(this));
            }.bind(this),
            onClearRows: function(r) {
                r.each(function(row) {
                    var c = $(row).down('div.msCheck');
                    if (c) {
                        DimpCore.addGC(c);
                    }
                    if (row.id) {
                        DimpCore.removeMouseEvents(row);
                    }
                });
            },
            onBeforeResize: function() {
                var sel = this.viewport.getSelected();
                this.isvisible = (sel.size() == 1) && (this.viewport.isVisible(sel.get('rownum').first()) == 0);
            }.bind(this),
            onAfterResize: function() {
                if (this.isvisible) {
                    this.viewport.scrollTo(this.viewport.getSelected().get('rownum').first());
                }
            }.bind(this),
            selectCallback: this._select.bind(this),
            deselectCallback: this._deselect.bind(this)
        });

        // If starting in no preview mode, need to set the no preview class
        if (!this.showPreview) {
            $('msgList').addClassName('msglistNoPreview');
        }

        // Set up viewport filter events.
        this.viewport.addFilter('ListMessages', this._addSearchfilterParams.bind(this));
        mf.observe('keyup', this._searchfilterOnKeyup.bind(this));
        mf.observe('focus', this._searchfilterOnFocus.bind(this));
        mf.observe('blur', this._searchfilterOnBlur.bind(this));
        mf.addClassName('msgFilterDefault');
    },

    _addMouseEvents: function(parentfunc, p)
    {
        var elt;

        switch (p.type) {
        case 'draft':
        case 'message':
            new Drag(p.id, this._msgDragConfig);
            elt = $(p.id).down('div.msCheck');
            if (elt.visible()) {
                elt.observe('mousedown', this.bcache.get('handleMLC') || this.bcache.set('handleMLC', this._handleMsgListCheckbox.bindAsEventListener(this)));
                elt.observe('contextmenu', Event.stop);
            }
            break;

        case 'container':
        case 'folder':
            new Drag(p.id, this._folderDragConfig);
            break;

        case 'special':
            // For purposes of the contextmenu, treat special folders
            // like regular folders.
            p.type = 'folder';
            break;
        }
        p.onShow = this.bcache.get('onMS') || this.bcache.set('onMS', this._onMenuShow.bind(this));
        parentfunc(p);
    },

    _removeMouseEvents: function(parentfunc, elt)
    {
        var d, id = $(elt).readAttribute('id');
        if (id && (d = DragDrop.Drags.get_drag(id))) {
            d.destroy();
        }
        parentfunc(elt);
    },

    _onMenuShow: function(ctx)
    {
        var elts, folder, ob, sel;

        switch (ctx.ctx) {
        case 'ctx_folder':
            elts = $('ctx_folder_create', 'ctx_folder_rename', 'ctx_folder_delete');
            folder = DimpCore.DMenu.element();
            if (folder.readAttribute('mbox') == 'INBOX') {
                elts.invoke('hide');
            } else if (DIMP.conf.fixed_folders.indexOf(folder.readAttribute('mbox')) != -1) {
                elts.shift();
                elts.invoke('hide');
            } else {
                elts.invoke('show');
            }

            if (folder.hasAttribute('u')) {
                $('ctx_folder_poll').hide();
                $('ctx_folder_nopoll').show();
            } else {
                $('ctx_folder_poll').show();
                $('ctx_folder_nopoll').hide();
            }
            break;

        case 'ctx_message':
            [ $('ctx_message_reply_list') ].invoke( this.viewport.createSelection('domid', ctx.id).get('dataob').first().listmsg ? 'show' : 'hide');
            break;

        case 'ctx_reply':
            sel = this.viewport.getSelected();
            if (sel.size() == 1) {
                ob = sel.get('dataob').first();
            }
            [ $('ctx_reply_reply_list') ].invoke(ob && ob.listmsg ? 'show' : 'hide');
            break;

        case 'ctx_otheractions':
            $('oa_seen', 'oa_unseen', 'oa_flagged', 'oa_clear', 'oa_sep1', 'oa_blacklist', 'oa_whitelist', 'oa_sep2', 'oa_undelete').compact().invoke(this.viewport.getSelected().size() ? 'show' : 'hide');
            break;
        }
        return true;
    },

    _onResize: function()
    {
        if (this.viewport) {
            this.viewport.onResize();
        }
        this._resizeIE6();
    },

    _handleMsgListDblclick: function(e)
    {
        var elt = this._getMsgRow(e);
        if (!elt) {
            return;
        }
        var row = this.viewport.createSelection('domid', elt.id).get('dataob').first();
        row.draft ? DimpCore.compose('resume', { folder: row.view, uid: row.imapuid }) : this.msgWindow(row);
        e.stop();
    },

    _handleMsgListCheckbox: function(e)
    {
        var elt = this._getMsgRow(e);
        if (!elt) {
            return;
        }
        this.msgSelect(elt.readAttribute('id'), { ctrl: true, right: true });
        e.stop();
    },

    _getMsgRow: function(e)
    {
        e = e.element();
        if (e && !e.hasClassName('msgRow')) {
            e = e.up('.msgRow');
        }
        return e;
    },

    updateTitle: function()
    {
        var elt, label, unseen;
        if (this.viewport.isFiltering()) {
            label = DIMP.text.search + ' :: ' + this.viewport.getMetaData('total_rows') + ' ' + DIMP.text.resfound;
        } else {
            elt = $(this.getFolderId(this.folder));
            if (elt) {
                unseen = elt.readAttribute('u');
                label = elt.readAttribute('l');
                if (unseen > 0) {
                    label += ' (' + unseen + ')';
                }
            } else {
                label = this.viewport.getMetaData('label');
            }
        }
        DimpCore.setTitle(label);
    },

    sort: function(e)
    {
        // Don't change sort if we are past the sortlimit
        if (this.viewport.getMetaData('sortlimit')) {
            return;
        }

        var s, sortby,
            elt = e.element();
        if (!elt.hasAttribute('sortby')) {
            elt = elt.up('[sortby]');
            if (!elt) {
                return;
            }
        }
        sortby = parseInt(elt.readAttribute('sortby'), 10);

        if (sortby == this.viewport.getMetaData('sortby')) {
            s = { sortdir: (this.viewport.getMetaData('sortdir') ? 0 : 1) };
            this.viewport.setMetaData({ sortdir: s.sortdir });
        } else {
            s = { sortby: sortby };
            this.viewport.setMetaData({ sortby: s.sortby });
        }
        this.setSortColumns(sortby);
        this.viewport.reload(s);
    },

    setSortColumns: function(sortby)
    {
        var tmp,
            m = $('msglistHeader');

        if (Object.isUndefined(sortby)) {
            sortby = this.viewport.getMetaData('sortby');
        }

        tmp = m.down('small[sortby=' + sortby + ']');
        if (tmp && tmp.up().visible()) {
           tmp.up(1).childElements().invoke('toggle');
        }

        tmp = m.down('div.msgFrom a');
        if ((this.viewport.isFiltering() && this.fspecial) ||
            this.viewport.getMetaData('special')) {
            tmp.hide().next().show();
        } else {
            tmp.show().next().hide();
        }

        tmp = m.down('div.msgSubject a');
        if (this.viewport.isFiltering() ||
            this.viewport.getMetaData('nothread') ||
            this.viewport.getMetaData('sortlimit')) {
            tmp.show().next().hide();
            tmp.down().hide();
        } else {
            tmp.down().show();
        }

        m.childElements().invoke('removeClassName', 'sortup').invoke('removeClassName', 'sortdown');
        m.down('div a[sortby=' + sortby + ']').up().addClassName(this.viewport.getMetaData('sortdir') ? 'sortup' : 'sortdown');
    },

    // Preview pane functions
    togglePreviewPane: function()
    {
        this.showPreview = !this.showPreview;
        $('previewtoggle').setText(this.showPreview ? DIMP.text.hide_preview : DIMP.text.show_preview);
        [ $('msgList') ].invoke(this.showPreview ? 'removeClassName' : 'addClassName', 'msglistNoPreview');
        new Ajax.Request(DimpCore.addSID(DIMP.conf.URI_PREFS), { parameters: { app: 'dimp', pref: 'show_preview', value: this.showPreview ? 1 : 0 } });
        this.viewport.showSplitPane(this.showPreview);
        if (this.showPreview) {
            this.initPreviewPane();
        }
        this.updateTitle();
    },

    _loadPreview: function(data)
    {
        var pp = $('previewPane'), pp_offset;
        if (!pp.visible()) {
            return;
        }
        if (this.pp &&
            this.pp == data) {
            return;
        }
        this.pp = data;

        if (this.ppfifo.indexOf(data.vp_id) != -1) {
            return this._loadPreviewCallback(this.ppcache.get(data.vp_id));
        }

        pp_offset = pp.positionedOffset();
        $('msgLoading').setStyle({ position: 'absolute', top: (pp_offset.top + 10) + 'px', left: (pp_offset.left + 10) + 'px' }).show();

        DimpCore.doAction('ShowPreview', {}, DimpCore.toUIDArray(this.viewport.createSelection('dataob', data)), this.bcache.get('loadPC') || this.bcache.set('loadPC', this._loadPreviewCallback.bind(this)));
    },

    _loadPreviewCallback: function(resp)
    {
        var row, search, tmp, tmp2,
            pm = $('previewMsg'),
            r = resp.response;

        if (!r.error) {
            search = this.viewport.getViewportSelection(r.view).search({ vp_id: { equal: [ r.uid ] } });
            if (search.size()) {
                row = search.get('dataob').first();
                this.updateUnseenUID(row, 0);
            }
        }

        if (this.pp &&
            this.pp.vp_id != r.uid) {
            return;
        }

        if (r.error || this.viewport.getSelected().size() != 1) {
            if (r.error) {
                DimpCore.showNotifications([ { type: r.errortype, message: r.error } ]);
            }
            this.clearPreviewPane();
            return;
        }

        // Store in cache.
        this._expirePPCache([ r.uid ]);
        this.ppcache.set(r.uid, resp);
        this.ppfifo.push(r.uid);

        DimpCore.removeAddressLinks(pm);

        DIMP.conf.msg_index = r.index;
        DIMP.conf.msg_folder = r.folder;
        DIMP.conf.msg_source_link = r.source_link;

        // Add subject/priority
        tmp = pm.select('.subject');
        tmp.invoke('update', r.subject);
        switch (r.priority) {
        case 'high':
        case 'low':
            tmp.invoke('insert', { top: $($(r.priority + '_priority_img').cloneNode(false)).writeAttribute('id', false) });
            break;
        }

        // Add from/date
        pm.select('.from').invoke('update', r.from);
        $('msgHeadersColl').select('.date').invoke('update', r.minidate);
        $('msgHeaderDate').select('.date').invoke('update', r.fulldate);

        // Add to/cc
        [ 'to', 'cc' ].each(function(a) {
            if (r[a]) {
                pm.select('.' + a).invoke('update', r[a]);
            }
            [ $('msgHeader' + a.capitalize()) ].invoke(r[a] ? 'show' : 'hide');
        });

        // Add attachment information
        $('msgHeadersColl').select('.attachmentImage').invoke(r.atc_label ? 'show' : 'hide');
        if (r.atc_label) {
            tmp = $('msgAtc').show().down('.label');
            tmp2 = $('partlist');
            tmp2.hide().previous().update(r.atc_label + ' ' + r.atc_download);
            if (r.atc_list) {
                $('partlist_col').show();
                $('partlist_exp').hide();
                tmp.down().hide().next().show();
                tmp2.update(r.atc_list);
            } else {
                tmp.down().show().next().hide();
            }
        } else {
            $('msgAtc').hide();
        }

        $('msgBody').down().update(r.msgtext);
        $('msgLoading', 'previewInfo').invoke('hide');
        $('previewPane').scrollTop = 0;
        pm.show();

        if (r.js) {
            eval(r.js.join(';'));
        }
        DimpCore.buildAddressLinks(pm);
        this._addHistory('msg:' + row.view + ':' + row.imapuid);
    },

    initPreviewPane: function()
    {
        var sel = this.viewport.getSelected();
        if (sel.size() != 1) {
            this.clearPreviewPane();
        } else {
            this._loadPreview(sel.get('dataob').first());
        }
    },

    clearPreviewPane: function()
    {
        $('msgLoading', 'previewMsg').invoke('hide');
        $('previewInfo').show();
        this.pp = null;
    },

    _expirePPCache: function(ids)
    {
        this.ppfifo = this.ppfifo.without(ids);
        ids.each(this.ppcache.unset.bind(this.ppcache));
        // Preview pane cache size is 20 entries. Given that a reasonable guess
        // of an average e-mail size is 10 KB (including headers), also make
        // an estimate that the JSON data size will be approx. 10 KB. 200 KB
        // should be a fairly safe caching value for any recent browser.
        if (this.ppfifo.size() > 20) {
            this.ppcache.unset(this.ppfifo.shift());
        }
    },

    // Labeling functions
    updateUnseenUID: function(r, setflag)
    {
        var sel, unseenset,
            unseen = 0;
        if (!r.bg) {
            return false;
        }
        unseenset = r.bg.match(this.unseen_regex);
        if ((setflag && unseenset) || (!setflag && !unseenset)) {
            return false;
        }

        sel = this.viewport.createSelection('dataob', r);
        if (setflag) {
            this.viewport.updateFlag(sel, 'unseen', true);
            ++unseen;
        } else {
            this.viewport.updateFlag(sel, 'unseen', false);
            --unseen;
        }

        return this.updateUnseenStatus(r.view, unseen);
    },

    updateUnseenStatus: function(mbox, change)
    {
        if (change == 0) {
            return false;
        }
        var unseen = parseInt($(this.getFolderId(mbox)).readAttribute('u')) + change;
        this.viewport.setMetaData({ unseen: unseen });
        this.setFolderLabel(mbox, unseen);
        return true;
    },

    setMessageListTitle: function()
    {
        var offset,
            rows = this.viewport.getMetaData('total_rows');
        if (rows > 0) {
            offset = this.viewport.currentOffset();
            $('msgHeader').update(DIMP.text.messages + ' ' + (offset + 1) + ' - ' + (Math.min(offset + this.viewport.getPageSize(), rows)) + ' ' + DIMP.text.of + ' ' + rows);
        } else {
            $('msgHeader').update(DIMP.text.nomessages);
        }
    },

    setFolderLabel: function(f, unseen)
    {
        var elt, fid = this.getFolderId(f);
        elt = $(fid);
        if (!elt || !elt.hasAttribute('u')) {
            return;
        }

        unseen = parseInt(unseen);
        elt.writeAttribute('u', unseen);

        if (f == 'INBOX' && window.fluid) {
            window.fluid.setDockBadge(unseen ? unseen : '');
        }

        $(fid + '_label').update((unseen > 0) ?
            new Element('STRONG').insert(elt.readAttribute('l')).insert('&nbsp;').insert(new Element('SPAN', { className: 'count', dir: 'ltr' }).insert('(' + unseen + ')')) :
            elt.readAttribute('l'));

        if (this.folder == f) {
            this.updateTitle();
        }
    },

    getFolderId: function(f)
    {
        return 'fld' + decodeURIComponent(f).replace(/_/g,'__').replace(/\W/g, '_');
    },

    getSubFolderId: function(f)
    {
        return 'sub' + f;
    },

    /* Folder list updates. */
    pollFolders: function()
    {
        // Reset poll folder counter.
        this.setPollFolders();
        var args = {};
        if (this.folder && $('dimpmain_folder').visible()) {
            args = this.viewport.addRequestParams({});
        }
        $('button_checkmail').setText('[' + DIMP.text.check + ']');
        DimpCore.doAction('PollFolders', args, [], this.bcache.get('pollFC') || this.bcache.set('pollFC', this._pollFoldersCallback.bind(this)));
    },

    _pollFoldersCallback: function(r)
    {
        r = r.response;
        if (r.poll) {
            $H(r.poll).each(function(u) {
                this.setFolderLabel(u.key, u.value);
                if (this.viewport) {
                    this.viewport.setMetaData({ unseen: u.value }, u.key);
                }
            }, this);
        }
        if (r.quota) {
            $('quota').update(r.quota);
        }
        $('button_checkmail').setText(DIMP.text.getmail);
    },

    setPollFolders: function()
    {
        if (DIMP.conf.refresh_time) {
            if (this.pollPE) {
                this.pollPE.stop();
            }
            // Don't cache - this code is only run once.
            this.pollPE = new PeriodicalExecuter(this.pollFolders.bind(this), DIMP.conf.refresh_time);
        }
    },

    _portalCallback: function(r)
    {
        if (r.response.linkTags) {
            var head = $$('HEAD').first();
            r.response.linkTags.each(function(newLink) {
                var link = new Element('LINK', { type: 'text/css', rel: 'stylesheet', href: newLink.href });
                if (newLink.media) {
                    link.media = newLink.media;
                }
                head.insert(link);
            });
        }
        $('dimpmain_portal').update(r.response.portal);

        /* Link portal block headers to the application. */
        $('dimpmain_portal').select('h1.header a').each(this.bcache.get('portalClkLink') || this.bcache.set('portalClkLink', function(d) {
            d.observe('click', function(e, d) {
                this.go('app:' + d.readAttribute('app'));
                e.stop();
            }.bindAsEventListener(this, d));
        }.bind(this)));
    },

    /* Search filter functions. */
    _searchfilterOnKeyup: function()
    {
        if (this.searchobserve) {
            clearTimeout(this.searchobserve);
        }
        this.searchobserve = (this.bcache.get('searchfilterR') || this.bcache.set('searchfilterR', this.searchfilterRun.bind(this))).delay(0.5);
    },

    searchfilterRun: function()
    {
        if (!this.viewport.isFiltering()) {
            this.filtertoggle = 1;
            this.fspecial = this.viewport.getMetaData('special');
        }
        this.viewport.runFilter($F('msgList_filter'));
    },

    _searchfilterOnFocus: function()
    {
        var q = $('qoptions');

        if ($('msgList_filter').hasClassName('msgFilterDefault')) {
            this._setFilterText(false);
        }

        if (!q.visible()) {
            $('sf_current').update(this.viewport.getMetaData('label'));
            this._setSearchfilterParams(this.viewport.getMetaData('special') ? 'to' : 'from', 'msg');
            this._setSearchfilterParams('current', 'folder');
            q.show();
            this.viewport.onResize();
        }
    },

    _searchfilterOnBlur: function()
    {
        if (!$F('msgList_filter')) {
            this._setFilterText(true);
        }
    },

    // reset = (boolean) TODO
    searchfilterClear: function(reset)
    {
        if (!$('qoptions').visible()) {
            return;
        }
        if (this.searchobserve) {
            clearTimeout(this.searchobserve);
            this.searchobserve = null;
        }
        this._setFilterText(true);
        $('qoptions').hide();
        this.filtertoggle = 2;
        this.resetSelected();
        this.viewport.onResize(reset);
        this.viewport.stopFilter(reset);
    },

    // d = (boolean) Deactivate filter input?
    _setFilterText: function(d)
    {
        var mf = $('msgList_filter');
        if (d) {
            mf.setValue(DIMP.text.search);
            mf.addClassName('msgFilterDefault');
        } else {
            mf.setValue('');
            mf.removeClassName('msgFilterDefault');
        }
    },

    // type = 'folder' or 'msg'
    _setSearchfilterParams: function(id, type)
    {
        var c = (type == 'folder') ? this.sfiltersfolder : this.sfilters;
        c.keys().each(function(i) {
            $(i).writeAttribute('className', (id == c.get(i)) ? 'qselected' : '');
        });
    },

    updateSearchfilter: function(id, type)
    {
        this._setSearchfilterParams(id, type);
        if ($F('msgList_filter')) {
            this.viewport.runFilter();
        }
    },

    _addSearchfilterParams: function()
    {
        var sf = this.sfiltersfolder.keys().find(function(s) {
                return $(s).hasClassName('qselected');
            });
        return { searchfolder: this.sfiltersfolder.get(sf), searchmsg: this.sfilters.get(this._getSearchfilterField()) };
    },

    _getSearchfilterField: function()
    {
        return this.sfilters.keys().find(function(s) {
            return $(s).hasClassName('qselected');
        });
    },

    /* Enable/Disable DIMP action buttons as needed. */
    toggleButtons: function()
    {
        var disable = (this.selectedCount() == 0);
        DimpCore.buttons.each(function(b) {
            var elt = $(b);
            if (elt) {
                [ elt.up() ].invoke(disable ? 'addClassName' : 'removeClassName', 'disabled');
                DimpCore.DMenu.disable(b + '_img', true, disable);
            }
        });
    },

    /* Drag/Drop handler. */
    _folderDropHandler: function(drop, drag)
    {
        var dropbase, sel, uids,
            foldername = drop.readAttribute('mbox'),
            ftype = drop.readAttribute('ftype');

        if (drag.hasClassName('folder')) {
            dropbase = (drop == $('dropbase'));
            if (dropbase ||
                (ftype != 'special' && !this.isSubfolder(drag, drop))) {
                DimpCore.doAction('RenameFolder', { old_name: drag.readAttribute('mbox'), new_parent: dropbase ? '' : foldername, new_name: drag.readAttribute('l') }, [], this.bcache.get('folderC') || this.bcache.set('folderC', this._folderCallback.bind(this)));
            }
        } else if (ftype != 'container') {
            sel = this.viewport.getSelected();

            if (sel.size()) {
                // Dragging multiple selected messages.
                uids = sel;
            } else if (drag.readAttribute('mbox') != foldername) {
                // Dragging a single unselected message.
                uids = this.viewport.createSelection('domid', drag.id);
            }

            // Don't allow drag/drop to the current folder.
            if (uids.size() && this.folder != foldername) {
                this.viewport.updateFlag(uids, 'deletedmsg', true);
                DimpCore.doAction('MoveMessage', this.viewport.addRequestParams({ tofld: foldername }), DimpCore.toUIDArray(uids), this.bcache.get('deleteC') || this.bcache.set('deleteC', this._deleteCallback.bind(this)));
            }
        }
    },

    _dragCaption: function()
    {
        var cnt = this.selectedCount();
        return cnt + ' ' + (cnt == 1 ? DIMP.text.message : DIMP.text.messages);
    },

    /* Keydown event handler */
    _keydownHandler: function(e)
    {
        // Only catch keyboard shortcuts in message list view. Disable catching
        // when in form elements or the RedBox overlay is visible.
        if (!$('dimpmain_folder').visible() ||
            e.findElement('FORM') ||
            RedBox.overlayVisible()) {
            return;
        }

        var co, ps, r, row, rowoff,
            kc = e.keyCode || e.charCode,
            sel = this.viewport.getSelected();

        switch (kc) {
        case Event.KEY_DELETE:
        case Event.KEY_BACKSPACE:
            r = sel.get('dataob');
            if (e.shiftKey) {
                this.moveSelected((r.last().rownum == this.viewport.getMetaData('total_rows')) ? (r.first().rownum - 1) : (r.last().rownum + 1), true);
            }
            this.flag('deleted', r);
            e.stop();
            break;

        case Event.KEY_UP:
        case Event.KEY_DOWN:
            if (e.shiftKey && this.lastrow != -1) {
                row = this.viewport.createSelection('rownum', this.lastrow + ((kc == Event.KEY_UP) ? -1 : 1));
                if (row.size()) {
                    row = row.get('dataob').first();
                    this.viewport.scrollTo(row.rownum);
                    this.msgSelect(row.domid, { shift: true });
                }
            } else {
                this.moveSelected(kc == Event.KEY_UP ? -1 : 1);
            }
            e.stop();
            break;

        case Event.KEY_PAGEUP:
        case Event.KEY_PAGEDOWN:
            if (!e.ctrlKey && !e.shiftKey && !e.altKey && !e.metaKey) {
                ps = this.viewport.getPageSize() - 1;
                move = ps * (kc == Event.KEY_PAGEUP ? -1 : 1);
                if (sel.size() == 1) {
                    co = this.viewport.currentOffset();
                    rowoff = sel.get('rownum').first() - 1;
                    switch (kc) {
                    case Event.KEY_PAGEUP:
                        if (co != rowoff) {
                            move = co - rowoff;
                        }
                        break;

                    case Event.KEY_PAGEDOWN:
                        if ((co + ps) != rowoff) {
                            move = co + ps - rowoff;
                        }
                        break;
                    }
                }
                this.moveSelected(move);
                e.stop();
            }
            break;

        case Event.KEY_HOME:
        case Event.KEY_END:
            this.moveSelected(kc == Event.KEY_HOME ? 1 : this.viewport.getMetaData('total_rows'), true);
            e.stop();
            break;

        case Event.KEY_RETURN:
            if (!e.element().match('input')) {
                // Popup message window if single message is selected.
                if (sel.size() == 1) {
                    this.msgWindow(sel.get('dataob').first());
                }
            }
            e.stop();
            break;

        case 65: // A
        case 97: // a
            if (e.ctrlKey) {
                this.selectAll();
                e.stop();
            }
            break;
        }
    },

    /* Handle rename folder actions. */
    renameFolder: function(folder)
    {
        if (Object.isUndefined(folder)) {
            return;
        }

        folder = $(folder);
        var n = this._createFolderForm(function(e) { this._folderAction(folder, e, 'rename'); return false; }.bindAsEventListener(this), DIMP.text.rename_prompt);
        n.down('input').setValue(folder.readAttribute('l'));
    },

    /* Handle insert folder actions. */
    createBaseFolder: function()
    {
        this._createFolderForm(function(e) { this._folderAction('', e, 'create'); return false; }.bindAsEventListener(this), DIMP.text.create_prompt);
    },

    createSubFolder: function(folder)
    {
        if (Object.isUndefined(folder)) {
            return false;
        }

        this._createFolderForm(function(e) { this._folderAction($(folder), e, 'createsub'); return false; }.bindAsEventListener(this), DIMP.text.createsub_prompt);
    },

    _createFolderForm: function(action, text)
    {
        var n = new Element('FORM', { action: '#', id: 'RB_folder' }).insert(
                    new Element('P').insert(text)
                ).insert(
                    new Element('INPUT', { type: 'text', size: 15 })
                ).insert(
                    new Element('INPUT', { type: 'button', className: 'button', value: DIMP.text.ok }).observe('click', action)
                ).insert(
                    new Element('INPUT', { type: 'button', className: 'button', value: DIMP.text.cancel }).observe('click', this.bcache.get('closeRB') || this.bcache.set('closeRB', this._closeRedBox.bind(this)))
                ).observe('keydown', function(e) { if ((e.keyCode || e.charCode) == Event.KEY_RETURN) { e.stop(); action(e); } });

        RedBox.overlay = true;
        RedBox.onDisplay = Form.focusFirstElement.curry(n);
        RedBox.showHtml(n);
        return n;
    },

    _closeRedBox: function()
    {
        var c = RedBox.getWindowContents();
        DimpCore.addGC([ c, c.descendants() ].flatten());
        RedBox.close();
    },

    _folderAction: function(folder, e, mode)
    {
        this._closeRedBox();

        var action, params, val,
            form = e.findElement('form');
        val = $F(form.down('input'));

        if (val) {
            switch (mode) {
            case 'rename':
                if (folder.readAttribute('l') != val) {
                    action = 'RenameFolder';
                    params = { old_name: folder.readAttribute('mbox'),
                               new_parent: folder.up().hasClassName('folderlist') ? '' : folder.up(1).previous().readAttribute('mbox'),
                               new_name: val };
                }
                break;

            case 'create':
            case 'createsub':
                action = 'CreateFolder';
                params = { folder: val };
                if (mode == 'createsub') {
                    params.parent = folder.readAttribute('mbox');
                }
                break;
            }
            if (action) {
                DimpCore.doAction(action, params, [], this.bcache.get('folderC') || this.bcache.set('folderC', this._folderCallback.bind(this)));
            }
        }
    },

    /* Folder action callback functions. */
    _folderCallback: function(r)
    {
        r = r.response;
        r.d.each(this.deleteFolder.bind(this));
        r.c.each(this.changeFolder.bind(this));
        r.a.each(this.createFolder.bind(this));
    },

    _deleteCallback: function(r)
    {
        this.msgListLoading(false);
        this._pollFoldersCallback(r);

        if (!r.response.uids ||
            r.response.folder != this.folder) {
            return;
        }

        var search = this.viewport.getViewportSelection().search({ view: { equal: [ r.response.folder ] }, imapuid: { equal: r.response.uids[r.response.folder] } });
        if (search.size()) {
            if (r.response.remove) {
                this.viewport.remove(search, { cacheid: r.response.cacheid, noupdate: r.response.viewport });
                this._expirePPCache(search.get('uid'));
            } else {
                // Need this to catch spam deletions.
                this.viewport.updateFlag(search, 'deletedmsg', true);
            }
        }
    },

    _emptyFolderCallback: function(r)
    {
        if (r.response.mbox) {
            if (this.folder == r.response.mbox) {
                this.viewport.reload();
                this.clearPreviewPane();
            }
            this.setFolderLabel(r.response.mbox, 0);
        }
    },

    _flagAllCallback: function(r)
    {
        if (r.response.mbox) {
            this.setFolderLabel(r.response.mbox, r.response.u);
        }
    },

    _folderLoadCallback: function(r)
    {
        this._folderCallback(r);

        var elts = $('specialfolders', 'normalfolders').compact(),
            nf = $('normalfolders'),
            nfheight = nf.getStyle('max-height');

        elts.invoke('observe', 'click', this._handleFolderMouseEvent.bindAsEventListener(this, 'click'));
        elts.invoke('observe', 'mouseover', this._handleFolderMouseEvent.bindAsEventListener(this, 'over'));
        if (DIMP.conf.is_ie6) {
            elts.invoke('observe', 'mouseout', this._handleFolderMouseEvent.bindAsEventListener(this, 'out'));
        }

        $('foldersLoading').hide();
        $('foldersSidebar').show();

        // Fix for IE6 - which doesn't support max-height.  We need to search
        // for height: 0px instead (comment in IE 6 CSS explains this is
        // needed for auto sizing).
        if (nfheight !== null ||
            (Prototype.Browser.IE &&
             Object.isUndefined(nfheight) &&
             (nf.getStyle('height') == '0px'))) {
            this._sizeFolderlist();
            Event.observe(window, 'resize', this._sizeFolderlist.bind(this));
        }

        if (r.response.quota) {
            $('quota').update(r.response.quota);
        }
    },

    _handleFolderMouseEvent: function(e, action)
    {
        var type,
            elt = e.element(),
            li = elt.up('.folder') || elt.up('.custom');
        if (!li) {
            return;
        }
        type = li.readAttribute('ftype');

        switch (action) {
        case 'over':
            if (DIMP.conf.is_ie6) {
                li.addClassName('over');
            }
            if (type && !this.mo_sidebar.get(li.id)) {
                DimpCore.addMouseEvents({ id: li.id, type: type });
                this.mo_sidebar.set(li.id, 1);
            }
            break;

        case 'out':
            li.removeClassName('over');
            break;

        case 'click':
            if (elt.hasClassName('exp') || elt.hasClassName('col')) {
                this._toggleSubFolder(li.id, 'tog');
            } else {
                switch (type) {
                case 'container':
                    e.stop();
                    break;

                case 'folder':
                case 'special':
                    e.stop();
                    return this.go('folder:' + li.readAttribute('mbox'));
                    break;
                }
            }
            break;
        }
    },

    _toggleSubFolder: function(base, mode)
    {
        base = $(base);
        var s = $(this.getSubFolderId(base.id));
        if (s &&
            (mode == 'tog' ||
             (mode == 'exp' && !s.visible()) ||
             (mode == 'col' && s.visible()))) {
            base.firstDescendant().writeAttribute({ className: s.toggle().visible() ? 'col' : 'exp' });
        }
        if (base.descendantOf('specialfolders')) {
            this._sizeFolderlist();
        }
    },

    // Folder actions.
    // For format of the ob object, see DIMP::_createFolderElt().
    createFolder: function(ob)
    {
        var div, f_node, li, ll, parent_e,
            fid = this.getFolderId(ob.m),
            mbox = decodeURIComponent(ob.m),
            submboxid = this.getSubFolderId(fid),
            submbox = $(submboxid);

        li = new Element('LI', { className: 'folder', id: fid, l: ob.l, mbox: mbox, ftype: ((ob.co) ? 'container' : ((ob.s) ? 'special' : 'folder')) });

        div = new Element('DIV', { className: ob.cl || 'base', id: fid + '_div' });
        if (ob.i) {
            div.setStyle({ backgroundImage: 'url("' + ob.i + '")' });
        }
        if (ob.ch) {
            div.writeAttribute({ className: 'exp' }).observe('mouseover', this.bcache.get('mo_folder') || this.bcache.set('mo_folder', function(e) {
                e = e.element();
                if (DragDrop.Drags.drag && e.hasClassName('exp')) {
                    this._toggleSubFolder(e.up(), 'exp');
                }
            }.bindAsEventListener(this)));
        }

        li.insert(div).insert(new Element('A', { id: fid + '_label', title: ob.l }).insert(ob.l));

        // Now walk through the parent <ul> to find the right place to
        // insert the new folder.
        if (submbox) {
            if (submbox.insert({ before: li }).visible()) {
                // If an expanded parent mailbox was deleted, we need to toggle
                // the icon accordingly.
                div.removeClassName('exp').addClassName('col');
            }
        } else {
            if (ob.s) {
                parent_e = $('specialfolders');
            } else {
                parent_e = $(this.getSubFolderId(this.getFolderId(ob.pa)));
                parent_e = (parent_e) ? parent_e.down('UL') : $('normalfolders');
            }

            ll = mbox.toLowerCase();
            f_node = parent_e.childElements().find(function(node) {
                var nodembox = node.readAttribute('mbox');
                return nodembox &&
                       (!ob.s || nodembox != 'INBOX') &&
                       (ll < nodembox.toLowerCase());
            });

            if (f_node) {
                f_node.insert({ before: li });
            } else {
                parent_e.insert(li);
            }

            // Make sure the sub<mbox> ul is created if necessary.
            if (ob.ch) {
                li.insert({ after: new Element('LI', { className: 'subfolders', id: submboxid }).insert(new Element('UL')).hide() });
            }
        }

        // Make the new folder a drop target.
        new Drop(li, this._folderDropConfig);

        // Check for unseen messages
        if (ob.po) {
            li.writeAttribute('u', '');
            this.setFolderLabel(mbox, ob.u);
        }
    },

    deleteFolder: function(folder)
    {
        var f = decodeURIComponent(folder), fid;
        if (this.folder == f) {
            this.go('folder:INBOX');
        }

        fid = this.getFolderId(folder);
        this.deleteFolderElt(fid, true);
    },

    changeFolder: function(ob)
    {
        var fid = this.getFolderId(ob.m),
            fdiv = $(fid + '_div'),
            oldexpand = fdiv && fdiv.hasClassName('col');
        this.deleteFolderElt(fid, !ob.ch);
        if (ob.co && this.folder == ob.m) {
            this.go('folder:INBOX');
        }
        this.createFolder(ob);
        if (ob.ch && oldexpand) {
            fdiv.removeClassName('exp').addClassName('col');
        }
    },

    deleteFolderElt: function(fid, sub)
    {
        var f = $(fid);
        DimpCore.addGC($(f, fid + '_div', fid + '_label'));
        if (sub) {
            var submbox = $(this.getSubFolderId(fid));
            if (submbox) {
                submbox.remove();
            }
        }
        [ DragDrop.Drags.get_drag(fid), DragDrop.Drops.get_drop(fid) ].compact().invoke('destroy');
        DimpCore.removeMouseEvents(f);
        this.mo_sidebar.unset(fid, 1);
        DimpCore.addGC(f);
        if (this.viewport) {
            this.viewport.deleteView(fid);
        }
        f.remove();
    },

    _sizeFolderlist: function()
    {
        var nf = $('normalfolders');
        nf.setStyle({ height: (document.viewport.getHeight() - nf.cumulativeOffset()[1] - 10) + 'px' });
    },

    /* Flag actions for message list. */
    flag: function(action, index, folder)
    {
        var actionCall, args, vs,
            obs = [],
            unseenstatus = 1;

        if (index) {
            if (Object.isUndefined(folder)) {
                vs = this.viewport.createSelection('dataob', index);
            } else {
                vs = this.viewport.getViewportSelection().search({ imapuid: { equal: [ index ] }, view: { equal: [ folder ] } });
                if (!vs.size() && folder != this.folder) {
                    vs = this.viewport.getViewportSelection(folder).search({ imapuid: { equal: [ index ] } });
                }
            }
        } else {
            vs = this.viewport.getSelected();
        }

        switch (action) {
        case 'allUnseen':
        case 'allSeen':
            DimpCore.doAction((action == 'allUnseen') ? 'MarkFolderUnseen' : 'MarkFolderSeen', { folder: folder }, [], this.bcache.get('flagAC') || this.bcache.set('flagAC', this._flagAllCallback.bind(this)));
            if (folder == this.folder) {
                this.viewport.updateFlag(this.createSelection('rownum', $A($R(1, this.viewport.getMetaData('total_rows')))), 'unseen', action == 'allUnseen');
            }
            break;

        case 'deleted':
        case 'undeleted':
        case 'spam':
        case 'ham':
        case 'blacklist':
        case 'whitelist':
            if (!vs.size()) {
                break;
            }

            // Make sure that any given row is not deleted more than once.
            // Need to explicitly mark here because message may already be
            // flagged deleted when we load page (i.e. switching to using
            // trash folder).
            if (action == 'deleted') {
                vs = vs.search({ isdel: { not: [ true ] } });
                if (!vs.size()) {
                    break;
                }
                vs.set({ isdel: true });
            } else if (action == 'undeleted') {
                vs.set({ isdel: false });
            }

            args = this.viewport.addRequestParams({});
            if (action == 'deleted' || action == 'undeleted') {
                this.viewport.updateFlag(vs, 'deletedmsg', action == 'deleted');            }

            if (action == 'undeleted') {
                DimpCore.doAction('UndeleteMessage', args, DimpCore.toUIDArray(vs));
            } else {
                actionCall = { deleted: 'DeleteMessage', spam: 'ReportSpam', ham: 'ReportHam', blacklist: 'Blacklist', whitelist: 'Whitelist' };
                // This needs to be synchronous Ajax if we are calling from a
                // popup window because Mozilla will not correctly call the
                // callback function if the calling window has been closed.
                DimpCore.doAction(actionCall[action], args, DimpCore.toUIDArray(vs), this.bcache.get('deleteC') || this.bcache.set('deleteC', this._deleteCallback.bind(this)), { asynchronous: !(index && folder) });

                // If reporting spam, to indicate to the user that something is
                // happening (since spam reporting may not be instantaneous).
                if (action == 'spam' || action == 'ham') {
                    this.msgListLoading(true);
                }
            }
            break;

        case 'unseen':
        case 'seen':
            if (!vs.size()) {
                break;
            }
            args = { folder: this.folder, messageFlag: '-seen' };
            if (action == 'seen') {
                unseenstatus = 0;
                args.messageFlag = 'seen';
            }
            vs.get('dataob').each(function(s) {
                if (this.updateUnseenUID(s, unseenstatus)) {
                    obs.push(s);
                }
            }, this);

            if (obs.size()) {
                DimpCore.doAction('MarkMessage', args, DimpCore.toUIDArray(this.viewport.createSelection('dataob', obs)));
            }
            break;

        case 'flagged':
        case 'clear':
            if (!vs.size()) {
                break;
            }
            args = {
                folder: this.folder,
                messageFlag: ((action == 'flagged') ? 'flagged' : '-flagged')
            };
            this.viewport.updateFlag(vs, 'flagged', action == 'flagged');
            DimpCore.doAction('MarkMessage', args, DimpCore.toUIDArray(vs));
            break;

        case 'answered':
            this.viewport.updateFlag(vs, 'answered', true);
            this.viewport.updateFlag(vs, 'flagged', false);
            break;
        }
    },

    /* Miscellaneous folder actions. */
    purgeDeleted: function()
    {
        DimpCore.doAction('PurgeDeleted', this.viewport.addRequestParams({}), [], this.bcache.get('deleteC') || this.bcache.set('deleteC', this._deleteCallback.bind(this)));
    },

    modifyPollFolder: function(folder, add)
    {
        DimpCore.doAction('ModifyPollFolder', { folder: folder, add: (add) ? 1 : 0 }, [], this.bcache.get('modifyPFC') || this.bcache.set('modifyPFC', this._modifyPollFolderCallback.bind(this)));
    },

    _modifyPollFolderCallback: function(r)
    {
        r = r.response;
        var f = r.folder, fid, p = { response: { poll: {} } };
        fid = $(this.getFolderId(f));

        if (r.add) {
            p.response.poll[f] = r.poll.u;
            fid.writeAttribute('u', 0);
        } else {
            p.response.poll[f] = 0;
        }

        this._pollFoldersCallback(p);

        if (!r.add) {
            fid.removeAttribute('u');
        }
    },

    msgListLoading: function(show)
    {
        var ml_offset;

        if (this.fl_visible != show) {
            this.fl_visible = show;
            if (show) {
                ml_offset = $('msgList').positionedOffset();
                $('folderLoading').setStyle({ position: 'absolute', top: (ml_offset.top + 10) + 'px', left: (ml_offset.left + 10) + 'px' });
                Effect.Appear('folderLoading', { duration: 0.2 });
                $(document.body).setStyle({ cursor: 'progress' });
            } else {
                Effect.Fade('folderLoading', { duration: 0.2 });
                $(document.body).setStyle({ cursor: 'default' });
            }
        }
    },

    // p = (element) Parent element
    // c = (element) Child element
    isSubfolder: function(p, c)
    {
        var sf = $(this.getSubFolderId(p.readAttribute('id')));
        return sf && c.descendantOf(sf);
    },

    /* Onload function. */
    _onLoad: function() {
        var C = DimpCore.clickObserveHandler, tmp;

        if (Horde.dhtmlHistory.initialize()) {
            Horde.dhtmlHistory.addListener(this.go.bind(this));
        }

        this._setFilterText(true);

        /* Initialize the starting page if necessary. addListener() will have
         * already fired if there is a current location so only do a go()
         * call if there is no current location. */
        if (!Horde.dhtmlHistory.getCurrentLocation()) {
            if (DIMP.conf.login_view == 'inbox') {
                this.go('folder:INBOX');
            } else {
                this.go('portal');
                if (DIMP.conf.background_inbox) {
                    this.loadFolder('INBOX', true);
                }
            }
        }

        /* Add popdown menus. */
        DimpCore.addPopdown('button_reply', 'reply');
        DimpCore.DMenu.disable('button_reply_img', true, true);
        DimpCore.addPopdown('button_forward', 'forward');
        DimpCore.DMenu.disable('button_forward_img', true, true);
        DimpCore.addPopdown('button_other', 'otheractions');

        /* Set up click event observers for elements on main page. */
        tmp = $('logo');
        if (tmp.visible()) {
            C({ d: tmp.down('a'), f: this.go.bind(this, 'portal') });
        }

        tmp = $('dimpbarActions');
        C({ d: tmp.down('.composelink'), f: DimpCore.compose.bind(DimpCore, 'new') });
        C({ d: tmp.down('.refreshlink'), f: this.pollFolders.bind(this) });

        tmp = $('serviceActions');
        [ 'portal', 'options' ].each(function(a) {
            var d = $('app' + a);
            if (d) {
                C({ d: d, f: this.go.bind(this, a) });
            }
        }, this);
        tmp = $('applogout');
        if (tmp) {
            C({ d: tmp, f: DimpCore.logout.bind(DimpCore) });
        }

        tmp = $('applicationfolders');
        if (tmp) {
            tmp.select('ul li.custom a').each(function(s) {
                C({ d: s, f: this.go.bind(this, 'app:' + s.readAttribute('app')) });
            }, this);
        }

        C({ d: $('newfolder'), f: this.createBaseFolder.bind(this) });
        new Drop('dropbase', this._folderDropConfig);
        tmp = $('hometab');
        if (tmp) {
            C({ d: tmp, f: this.go.bind(this, 'portal') });
        }
        $('tabbar').select('a.applicationtab').each(function(a) {
            C({ d: a, f: this.go.bind(this, 'app:' + a.readAttribute('app')) });
        }, this);
        C({ d: $('button_reply'), f: this.composeMailbox.bind(this, 'reply'), ns: true });
        C({ d: $('button_forward'), f: this.composeMailbox.bind(this, DIMP.conf.forward_default), ns: true });
        [ 'spam', 'ham', 'deleted' ].each(function(a) {
            var d = $('button_' + a);
            if (d) {
                C({ d: d, f: this.flag.bind(this, a) });
            }
        }, this);
        C({ d: $('button_compose'), f: DimpCore.compose.bind(DimpCore, 'new') });
        C({ d: $('button_other'), f: function(e) { DimpCore.DMenu.trigger(e.findElement('A').next(), true); }, p: true });
        C({ d: $('qoptions').down('.qclose a'), f: this.searchfilterClear.bind(this, false) });
        [ 'all', 'current' ].each(function(a) {
            var d = $('sf_' + a);
            if (d) {
                C({ d: d, f: this.updateSearchfilter.bind(this, a, 'folder') });
            }
        }, this);
        [ 'msgall', 'from', 'to', 'subject' ].each(function(a) {
            C({ d: $('sf_' + a), f: this.updateSearchfilter.bind(this, a, 'msg') });
        }, this);
        C({ d: $('msglistHeader'), f: this.sort.bind(this), p: true });
        C({ d: $('ctx_folder_create'), f: function() { this.createSubFolder(DimpCore.DMenu.element()); }.bind(this), ns: true });
        C({ d: $('ctx_folder_rename'), f: function() { this.renameFolder(DimpCore.DMenu.element()); }.bind(this), ns: true });
        C({ d: $('ctx_folder_empty'), f: function() { if (window.confirm(DIMP.text.empty_folder)) { DimpCore.doAction('EmptyFolder', { folder: DimpCore.DMenu.element().readAttribute('mbox') }, [], this._emptyFolderCallback.bind(this)); } }.bind(this), ns: true });
        C({ d: $('ctx_folder_delete'), f: function() { if (window.confirm(DIMP.text.delete_folder)) { DimpCore.doAction('DeleteFolder', { folder: DimpCore.DMenu.element().readAttribute('mbox') }, [], this.bcache.get('folderC') || this.bcache.set('folderC', this._folderCallback.bind(this))); } }.bind(this), ns: true });
        [ 'ctx_folder_seen', 'ctx_folder_unseen' ].each(function(a) {
            C({ d: $(a), f: function(type) { this.flag(type, null, DimpCore.DMenu.element().readAttribute('mbox')); }.bind(this, a == 'ctx_folder_seen' ? 'allSeen' : 'allUnseen'), ns: true });
        }, this);
        [ 'ctx_folder_poll', 'ctx_folder_nopoll' ].each(function(a) {
            C({ d: $(a), f: function(modify) { this.modifyPollFolder(DimpCore.DMenu.element().readAttribute('mbox'), modify); }.bind(this, a == 'ctx_folder_poll'), ns: true });
        }, this);
        C({ d: $('ctx_container_create'), f: function() { this.createSubFolder(DimpCore.DMenu.element()); }.bind(this), ns: true });
        C({ d: $('ctx_container_rename'), f: function() { this.renameFolder(DimpCore.DMenu.element()); }.bind(this), ns: true });
        [ 'reply', 'reply_all', 'reply_list', 'forward_all', 'forward_body', 'forward_attachments' ].each(function(a) {
            C({ d: $('ctx_message_' + a), f: this.composeMailbox.bind(this, a), ns: true });
        }, this);
        [ 'seen', 'unseen', 'flagged', 'clear', 'spam', 'ham', 'blacklist', 'whitelist', 'deleted', 'undeleted' ].each(function(a) {
            var d = $('ctx_message_' + a);
            if (d) {
                C({ d: d, f: this.flag.bind(this, a), ns: true });
            }
        }, this);
        C({ d: $('ctx_draft_resume'), f: this.composeMailbox.bind(this, 'resume') });
        [ 'flagged', 'clear', 'deleted', 'undeleted' ].each(function(a) {
            var d = $('ctx_draft_' + a);
            if (d) {
                C({ d: d, f: this.flag.bind(this, a), ns: true });
            }
        }, this);
        [ 'reply', 'reply_all', 'reply_list' ].each(function(a) {
            C({ d: $('ctx_reply_' + a), f: this.composeMailbox.bind(this, a), ns: true });
        }, this);
        [ 'forward_all', 'forward_body', 'forward_attachments' ].each(function(a) {
            C({ d: $('ctx_forward_' + a), f: this.composeMailbox.bind(this, a), ns: true });
        }, this);
        C({ d: $('previewtoggle'), f: this.togglePreviewPane.bind(this), ns: true });
        [ 'seen', 'unseen', 'flagged', 'clear', 'blacklist', 'whitelist', 'undeleted' ].each(function(a) {
            var d = $('oa_' + a);
            if (d) {
                C({ d: d, f: this.flag.bind(this, a), ns: true });
            }
        }, this);
        C({ d: $('oa_selectall'), f: this.selectAll.bind(this), ns: true });

        tmp = $('oa_purge_deleted');
        if (tmp) {
            C({ d: tmp, f: this.purgeDeleted.bind(this), ns: true });
        }

        $('expandHeaders', 'collapseHeaders').each(function(a) {
            C({ d: a, f: function() { $('msgHeadersColl', 'msgHeaders').invoke('toggle'); }, ns: true });
        }, this);
        $('msg_newwin', 'msg_newwin_options').compact().each(function(a) {
            C({ d: a, f: function() { this.msgWindow(this.viewport.getViewportSelection().search({ imapuid: { equal: [ DIMP.conf.msg_index ] } , view: { equal: [ DIMP.conf.msg_folder ] } }).get('dataob').first()); }.bind(this) });
        }, this);
        DimpCore.messageOnLoad();
        this._resizeIE6();
    },

    // IE 6 width fixes (See Bug #6793)
    _resizeIE6: function()
    {
        if (DIMP.conf.is_ie6) {
            var tmp = parseInt($('sidebarPanel').getStyle('width'), 10),
                tmp1 = document.viewport.getWidth() - tmp - 30;
            $('normalfolders').setStyle({ width: tmp + 'px' });
            $('dimpmain').setStyle({ width: tmp1 + 'px' });
            $('msglist').setStyle({ width: (tmp1 - 5) + 'px' });
            $('msgBody').setStyle({ width: (tmp1 - 25) + 'px' });
            tmp = $('dimpmain_portal').down('IFRAME');
            if (tmp) {
                this._resizeIE6Iframe(tmp);
            }
        }
    },

    _resizeIE6Iframe: function(iframe)
    {
        if (DIMP.conf.is_ie6) {
            iframe.setStyle({ width: $('dimpmain').getStyle('width'), height: (document.viewport.getHeight() - 20) + 'px' });
        }
    }
};

/* Need to add after DimpBase is defined. */
DimpBase._msgDragConfig = {
    scroll: 'normalfolders',
    threshold: 5,
    caption: DimpBase._dragCaption.bind(DimpBase),
    onStart: function(d, e) {
        var args = { right: e.isRightClick() },
            id = d.element.id;

        d.selectIfNoDrag = false;

        // Handle selection first.
        if (!args.right && (e.ctrlKey || e.metaKey)) {
            this.msgSelect(id, $H({ ctrl: true }).merge(args).toObject());
        } else if (e.shiftKey) {
            this.msgSelect(id, $H({ shift: true }).merge(args).toObject());
        } else if (this.isSelected('domid', id)) {
            if (!args.right && this.selectedCount()) {
                d.selectIfNoDrag = true;
            }
        } else {
            this.msgSelect(id, args);
        }
    }.bind(DimpBase),
    onEnd: function(d, e) {
        if (d.selectIfNoDrag && !d.wasDragged) {
            this.msgSelect(d.element.id, { right: e.isRightClick() });
        }
    }.bind(DimpBase)
};

DimpBase._folderDragConfig = {
    ghosting: true,
    offset: { x: 5, y: 5 },
    scroll: 'normalfolders',
    threshold: 5,
    onDrag: function(d, e) {
        if (!d.wasDragged) {
            $('newfolder').hide();
            $('dropbase').show();
            d.ghost.removeClassName('on');
        }
    },
    onEnd: function(d, e) {
        if (d.wasDragged) {
            $('newfolder').show();
            $('dropbase').hide();
        }
    }
};

DimpBase._folderDropConfig = {
    hoverclass: 'dragdrop',
    caption: function(drop, drag) {
        var d = drag.readAttribute('l'),
            ftype = drop.readAttribute('ftype'),
            l = drop.readAttribute('l'),
            m = DIMP.text.moveto;
        if (drop == $('dropbase')) {
            return m.replace(/%s/, d).replace(/%s/, DIMP.text.baselevel);
        } else if (drag.hasClassName('folder')) {
            return (ftype != 'special' && !this.isSubfolder(drag, drop)) ? m.replace(/%s/, d).replace(/%s/, l) : '';
        } else {
            return ftype != 'container' ? m.replace(/%s/, this._dragCaption()).replace(/%s/, l) : '';
        }
    }.bind(DimpBase),
    onDrop: DimpBase._folderDropHandler.bind(DimpBase)
};

/* Stuff to do immediately when page is ready. */
document.observe('dom:loaded', function() {
    $('dimpLoading').hide();
    $('dimpPage').show();

    /* Create the folder list. Any pending notifications will be caught via
     * the return from this call. */
    DimpCore.doAction('ListFolders', {}, [], DimpBase._folderLoadCallback.bind(DimpBase));

    /* Start message list loading as soon as possible. */
    if (!DimpBase.delay_onload) {
        DimpBase._onLoad();
    }

    /* Disable text selection in preview pane for IE 6. */
    if (DIMP.conf.is_ie6) {
        document.observe('selectstart', Event.stop);
    }

    /* Remove unneeded search folders. */
    if (!DIMP.conf.search_all) {
        DimpBase.sfiltersfolder.unset('sf_all');
    }

    /* Check for new mail. */
    DimpBase.setPollFolders();

    /* Bind key shortcuts. */
    document.observe('keydown', DimpBase._keydownHandler.bind(DimpBase));

    /* Resize elements on window size change. */
    Event.observe(window, 'resize', DimpBase._onResize.bind(DimpBase));

    /* Since IE 6 doesn't support hover over non-links, use javascript events
     * to replicate mouseover CSS behavior. */
    if (DIMP.conf.is_ie6) {
        var links = [], tmp;
        if (tmp = $('dimpbarActions')) {
            links.push(tmp.select('SPAN'));
        }
        if (tmp = $('serviceActions')) {
            links.push(tmp.select('LI.servicelink'));
        }
        if (tmp = $('applicationfolders')) {
            links.push(tmp.select('UL LI'));
        }
        links.flatten().compact().each(function(e) {
            e.observe('mouseover', e.addClassName.curry('over')).observe('mouseout', e.removeClassName.curry('over'));
        });
    }
});

/* Stuff to do after window is completely loaded. Don't init viewport until
 * now for non-Gecko/Opera browsers since sizing functions might not work
 * properly before. */
if (DimpBase.delay_onload) {
    Event.observe(window, 'load', DimpBase._onLoad.bind(DimpBase));
}

/* Need to register a callback function for doAction to catch viewport
 * information returned from the server. */
DimpCore.onDoActionComplete = function(r) {
    if (DimpBase.viewport && r.response.viewport) {
        DimpBase.viewport.ajaxResponse(r.response.viewport);
    }
};

/* Extend these functions from DimpCore since additional processing needs to
 * be done re: drag/drop and menu manipulation. */
DimpCore.addMouseEvents = DimpCore.addMouseEvents.wrap(DimpBase._addMouseEvents.bind(DimpBase));
DimpCore.removeMouseEvents = DimpCore.removeMouseEvents.wrap(DimpBase._removeMouseEvents.bind(DimpBase));
