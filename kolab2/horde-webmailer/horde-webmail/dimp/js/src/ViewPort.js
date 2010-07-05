/**
 * ViewPort.js - Code to create a viewport window in a web browser.
 *
 * Requires prototypejs 1.6+, DimpSlider.js, scriptaculous 1.8+ (effects.js
 * only), and DIMP's dragdrop.js.
 *
 * $Horde: dimp/js/src/ViewPort.js,v 1.194.2.57 2009-01-06 15:22:37 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

/**
 * ViewPort
 */
var ViewPort = Class.create({

    // Required: content_container, lines, fetch_action, template,
    //           cachecheck_action, ajaxRequest, buffer_pages,
    //           limit_factor, content_class, row_class, selected_class
    // Optional: norows, show_split_pane
    initialize: function(opts)
    {
        opts.content = $(opts.content_container);
        opts.empty = opts.empty_container ? $(opts.empty_container) : null;
        opts.error = opts.error_container ? $(opts.error_container) : null;
        this.opts = opts;

        this.scroller = new ViewPort_Scroller(this);
        this.template = new Template(opts.template);

        this.current_req_lookup = $H();
        this.current_req = $H();
        this.fetch_hash = $H();
        this.slice_hash = $H();
        this.views = $H();

        this.showSplitPane(opts.show_split_pane);

        // Initialize all other variables
        this.isbusy = this.line_height = this.page_size = this.splitbar = this.splitbar_loc = this.uc_run = this.view = this.viewport_init = null;
        this.request_num = 1;
    },

    // view = ID of view. Can not contain a '%' character.
    // params = TODO
    // search = (object) Search parameters
    // background = Load view in background?
    loadView: function(view, params, search, background)
    {
        var buffer, curr, init, opts = {}, ps;

        this._clearWait();

        // Need a page size before we can continue - this is what determines
        // the slice size to request from the server.
        if (this.page_size === null) {
            ps = this.getPageSize(this.show_split_pane ? 'default' : 'max');
            if (isNaN(ps)) {
                this.loadView.bind(this, view, params, search, background).defer();
                return;
            }
            this.page_size = ps;
        }

        buffer = this._getBuffer();
        if (buffer) {
            if (!background && this.view) {
                // Need to store current buffer to save current offset
                this.views.set(this.view, { buffer: buffer, offset: this.currentOffset() });
            }
            curr = this.views.get(view);
        } else {
            init = true;
        }

        if (background) {
            opts = { background: true, view: view };
        } else {
            this.view = view;
            if (!this.viewport_init) {
                this.viewport_init = 1;
                this._renderViewport();
            }
        }

        if (curr) {
            this.setMetaData({ additional_params: $H(params) }, view);
            this._updateContent(curr.offset, opts);
            if (!background) {
                if (this.opts.onComplete) {
                    this.opts.onComplete();
                }
                this.opts.ajaxRequest(this.opts.fetch_action, this.addRequestParams({ checkcache: 1, rownum: this.currentOffset() + 1 }));
            }
            return true;
        } else if (!init) {
            if (this.opts.onClearRows) {
                this.opts.onClearRows(this.opts.content.childElements());
            }
            this.opts.content.update();
            this.scroller.clear();
        }

        buffer = this._getBuffer(null, true);
        this.views.set(view, { buffer: buffer, offset: 0 });
        this.setMetaData({ additional_params: $H(params) }, view);
        if (search) {
            opts.search = search;
        } else {
            opts.offset = 0;
        }
        this._fetchBuffer(opts);

        return false;
    },

    // view = ID of view
    deleteView: function(view)
    {
        this.views.unset(view);
    },

    // rownum = Row number
    // noupdate = boolean
    scrollTo: function(rownum, noupdate)
    {
        var s = this.scroller;

        s.noupdate = noupdate;

        switch (this.isVisible(rownum)) {
        case -1:
            s.moveScroll(rownum - 1);
            break;

        // case 0:
        // noop

        case 1:
            s.moveScroll(Math.min(rownum, this.getMetaData('total_rows') - this.getPageSize() + 1));
            break;
        }

        s.noupdate = false;
    },

    // rownum = Row number
    isVisible: function(rownum)
    {
        var offset = this.currentOffset();
        return (rownum < offset + 1) ? -1 :
               ((rownum > (offset + this.getPageSize('current'))) ? 1 : 0);
    },

    // params = TODO
    reload: function(params)
    {
        if (this.isFiltering()) {
            this.filter.filter(null, params);
        } else {
            this._fetchBuffer({ offset: this.currentOffset(), purge: true, params: params });
        }
    },

    // vs = (Viewport_Selection) A Viewport_Selection object.
    // opts = (object) TODO [cacheid, noupdate, view]
    remove: function(vs, opts)
    {
        if (this.isbusy) {
            this.remove.bind(this, vs, cacheid, view).defer();
            return;
        }

        if (!vs.size()) {
            return;
        }

        opts = opts || {};
        this.isbusy = true;

        var args,
            i = 0,
            visible = vs.get('div'),
            vsize = visible.size();

        this.deselect(vs);

        if (opts.cacheid) {
            this.setMetaData({ cacheid: opts.cacheid }, opts.view);
        }

        // If we have visible elements to remove, only call refresh after
        // the last effect has finished.
        if (vsize) {
            // Set 'to' to a value slightly above 0 to prevent Effect.Fade
            // from auto hiding.  Hiding is unnecessary, since we will be
            // removing from the document shortly.
            args = { duration: 0.3, to: 0.01 };
            visible.each(function(v) {
                if (++i == vsize) {
                    args.afterFinish = this._removeids.bind(this, vs, opts);
                }
                Effect.Fade(v, args);
            }, this);
        } else {
            this._removeids(vs, opts);
        }
    },

    // vs = (Viewport_Selection) A Viewport_Selection object.
    // opts = (object) TODO [noupdate, view]
    _removeids: function(vs, opts)
    {
        this.setMetaData({ total_rows: this.getMetaData('total_rows', opts.view) - vs.size() }, opts.view);

        if (this.opts.onRemoveRows) {
            this.opts.onRemoveRows(vs);
        }

        this._getBuffer().remove(vs.get('rownum'));
        if (!opts.noupdate) {
            this.requestContentRefresh(this.currentOffset());
        }
        this.isbusy = false;
    },

    // action = TODO
    // callback = TODO
    addFilter: function(action, callback)
    {
        this.filter = new ViewPort_Filter(this, action, callback);
    },

    // val = TODO
    // params = TODO
    runFilter: function(val, params)
    {
        if (this.filter) {
            this.filter.filter(Object.isUndefined(val) ? null : val, params);
        }
    },

    // Return: (boolean) Is filtering currently active?
    isFiltering: function()
    {
        return this.filter ? this.filter.isFiltering() : false;
    },

    // reset = (boolean) If true, don't update the viewport
    stopFilter: function(reset)
    {
        if (this.filter) {
            this.filter.clear(reset);
        }
    },

    // noupdate = (boolean) TODO
    // nowait = (boolean) TODO
    onResize: function(noupdate, nowait)
    {
        if (!this.uc_run || !this.opts.content.visible()) {
            return;
        }

        if (this.resizefunc) {
            clearTimeout(this.resizefunc);
        }

        if (nowait) {
            this._onResize(noupdate);
        } else {
            this.resizefunc = this._onResize.bind(this, noupdate).delay(0.1);
        }
    },

    _onResize: function(noupdate)
    {
        if (this.opts.onBeforeResize) {
            this.opts.onBeforeResize();
        }

        this._renderViewport(noupdate);

        if (this.opts.onAfterResize) {
            this.opts.onAfterResize();
        }
    },

    // offset = (integer) TODO
    requestContentRefresh: function(offset)
    {
        if (this._updateContent(offset)) {
            var limit = this._getBuffer().isNearingLimit(offset);
            if (limit) {
                this._fetchBuffer({ offset: offset, background: true, nearing: limit });
            }
            return true;
        }

        return false;
    },

    // opts = (object) The following parameters are used
    // One of the following:
    //   offset: (integer) Value of offset
    //   search: (object) List of search keys/values
    // Optional:
    //   background: (boolean) Do fetch in background
    //   purge: (boolean) TODO
    //   nearing: (string) TODO [only used w/offset]
    //   params: (object) Parameters to add to outgoing URL
    //   view: (string) The view to retrieve. Defaults to current view.
    //
    // Outgoing request has the following params:
    //   rownum: (integer) TODO
    //   request_id: (string) TODO
    //   rows: (JSON array) TODO [optional]
    //
    //   search: (JSON object)
    //   search_after: (integer)
    //   search_before: (integer)
    _fetchBuffer: function(opts)
    {
        if (this.isbusy) {
            this._fetchBuffer.bind(this, opts).defer();
            return;
        }

        this.isbusy = true;

        // Only call onFetch() if we are loading in foreground.
        if (this.opts.onFetch && !opts.background) {
            this.opts.onFetch();
        }

        var view = (opts.view || this.view),
            action = this.opts.fetch_action,
            allrows,
            b = this._getBuffer(view),
            cr,
            lb,
            params = $H(opts.params),
            request_id,
            request_string,
            request_old,
            request_vals,
            rlist,
            rowlist,
            type,
            value,
            viewable;

        // If asking for an explicit purge, add to the request.
        if (opts.purge) {
            params.set('purge', true);
        }

        // Determine if we are querying via offset or a search query
        if (opts.search) {
            type = 'search';
            value = opts.search;
            lb = this._lookbehind(view);

            params.update({ search_before: lb, search_after: b.bufferSize() - lb });
        } else {
            type = 'rownum';
            value = opts.offset + 1;

            // This gets the list of rows needed which do not already appear
            // in the buffer.
            allrows = b.getAllRows();
            rowlist = this._getSliceBounds(value, opts.nearing, view);
            rlist = $A($R(rowlist.start, rowlist.end)).diff(allrows);
            if (!opts.purge && !rlist.size()) {
                this.isbusy = false;
                return;
            }

            params.update({ slice_start: rowlist.start, slice_end: rowlist.end });
        }
        params.set(type, Object.toJSON(value));
        request_vals = [ view, type, value ];

        // Are we currently filtering results?
        if (this.isFiltering()) {
            action = this.filter.getAction();
            params = this.filter.addFilterParams(params);
            // Need to capture filter params changes in the request ID
            request_vals.push(params);
        }

        // Generate a unique request ID value based on the search params.
        // Since javascript does not have a native hashing function, use a
        // local lookup table instead.
        request_string = request_vals.toJSON();
        request_id = this.fetch_hash.get(request_string);

        // If we have a current request pending in the current view, figure
        // out if we need to send a new request
        cr = this.current_req.get(view);
        if (cr) {
            if (request_id && cr.get(request_id)) {
                // Check for repeat request.  We technically should never
                // reach here but if we do, make sure we don't go into an
                // infinite loop.
                if (++cr.get(request_id).count == 4) {
                    this._displayFetchError();
                    this._removeRequest(view, request_id);
                    this.isbusy = false;
                    return;
                }
            } else if (type == 'rownum') {
                // Check for message list requests that are requesting
                // (essentially) the same message slice - such as two
                // scroll down requests sent in quick succession.  If the
                // original request contains the viewable slice needed by the
                // second request, ignore the later request and just
                // reposition the viewport on display.
                viewable = $A($R(value, value + this.getPageSize())).diff(allrows);
                if (!viewable.size()) {
                    this.isbusy = false;
                    return;
                }
                request_old = cr.keys().numericSort().find(function(k) {
                    var r = cr.get(k).rlist;
                    viewable = viewable.diff(r);
                    if (!viewable.size()) {
                        return true;
                    }
                    rlist = rlist.diff(r);
                });
                if (request_old) {
                    if (!opts.background) {
                        this._addRequest(view, request_old, { background: false, offset: value - 1 });
                    }
                    this.isbusy = false;
                    return;
                } else if (!opts.background) {
                    // Set all other pending requests to background, since the
                    // current request is now the active request.
                    cr.keys().each(function(k) {
                        this._addRequest(view, k, { background: true });
                    }, this);
                }
            }
            // If we are in search mode, we must bite the bullet and simply
            // accept the entire slice back from the server.
        }

        // We don't need to send row information to the server if the server
        // is keeping track of what has been sent to the browser.
        if (!this.opts.norows && rlist) {
            params.set('rows', rlist.toJSON());
        }

        if (!request_id) {
            request_id = this.fetch_hash.set(request_string, this.request_num++);
        }
        params.set('request_id', request_id);
        this._addRequest(view, request_id, { background: opts.background, offset: value - 1, rlist: rlist });

        this.opts.ajaxRequest(action, this.addRequestParams(params, { noslice: true, view: view }));
        this._handleWait();
        this.isbusy = false;
    },

    // rownum = (integer) Row number
    // nearing = (string) 'bottom', 'top', null
    // view = (string) The view to retrieve. Defaults to current view.
    _getSliceBounds: function(rownum, nearing, view)
    {
        var b_size = this._getBuffer(view).bufferSize(),
            ob = {};

        switch (nearing) {
        case 'bottom':
            ob.start = rownum + this.getPageSize();
            ob.end = ob.start + b_size;
            break;

        case 'top':
            ob.start = Math.max(rownum - b_size, 1);
            ob.end = rownum;
            break;

        default:
            ob.start = Math.max(rownum - this._lookbehind(view), 1);
            ob.end = ob.start + b_size;
            break;
        }

        return ob;
    },

    // view = (string) The view to retrieve. Defaults to current view.
    _lookbehind: function(view)
    {
        return parseInt(0.4 * this._getBuffer(view).bufferSize(), 10);
    },

    // args = (object) The list of parameters.
    // opts = (object) [noslice, view]
    // Returns a Hash object
    addRequestParams: function(args, opts)
    {
        opts = opts || {};
        var cid = this.getMetaData('cacheid', opts.view),
            params = this.getMetaData('additional_params', opts.view),
            rowlist;
        if (cid) {
            params.update({ cacheid: cid });
        }
        if (!opts.noslice) {
            rowlist = this._getSliceBounds(this.currentOffset(), null, opts.view);
            params.update({ slice_start: rowlist.start, slice_end: rowlist.end });
        }
        return params.merge(args);
    },

    // r = (Object) viewport response object.
    //     Common properties:
    //         id
    //         request_id
    //         type: 'list', 'slice' (DEFAULT: list)
    //
    //     Properties needed for type 'list':
    //         cacheid
    //         data
    //         label
    //         total_rows
    //         other
    //         rowlist
    //         rownum (optional)
    //         totalrows
    //         update (optional)
    //
    //     Properties needed for type 'slice':
    //         data (object) - rownum is the only required property
    ajaxResponse: function(r)
    {
        if (this.isbusy) {
            this.ajaxResponse.bind(this, r).defer();
            return;
        }

        this.isbusy = true;
        this._clearWait();

        var buffer, cr, cr_id, data, datakeys, id, rowlist = {};

        if (r.type == 'slice') {
            data = r.data;
            datakeys = Object.keys(data);
            datakeys.each(function(k) {
                data[k].view = r.id;
                rowlist[k] = data[k].rownum;
            });
            buffer = this._getBuffer(r.id);
            buffer.update(data, rowlist, { slice: true });
            if (this.opts.onEndFetch) {
                this.opts.onEndFetch();
            }
            cr = this.slice_hash.get(r.request_id);
            if (cr) {
                cr(new ViewPort_Selection(buffer, 'uid', datakeys));
                this.slice_hash.unset(r.request_id);
            }
            this.isbusy = false;
            return;
        }

        id = (r.request_id) ? this.current_req_lookup.get(r.request_id) : r.id;
        cr = this.current_req.get(id);
        if (cr && r.request_id) {
            cr_id = cr.get(r.request_id);
        }

        if (this.viewport_init) {
            this.viewport_init = 2;
        }

        buffer = this._getBuffer(id);
        buffer.update(r.data, r.rowlist, { update: r.update });
        buffer.setMetaData($H(r.other).merge({
            cacheid: r.cacheid,
            label: r.label,
            total_rows: r.totalrows
        }));

        if (r.request_id) {
            this._removeRequest(id, r.request_id);
        }

        this.isbusy = false;

        // Don't update the viewport if we are now in a different view, or if
        // we are loading in the background.
        if (!(this.view == id || r.search) ||
            (cr_id && cr_id.background) ||
            !this._updateContent((cr_id && cr_id.offset) ? cr_id.offset : (r.rownum ? parseInt(r.rownum) - 1 : this.currentOffset()))) {
            return;
        }

        if (this.opts.onComplete) {
            this.opts.onComplete();
        }

        if (this.opts.onEndFetch) {
            this.opts.onEndFetch();
        }
    },

    // Adds a request to the current request queue.
    // Requests are stored by view ID. Under each ID is the following:
    //   count: (integer) Number of times slice has attempted to be loaded
    //   background: (boolean) Do not update current view
    //   offset: (integer) The offset to use
    //   rlist: (array) The row list
    // params = (object) [background, offset, rlist]
    _addRequest: function(view, r_id, params)
    {
        var req_view = this.current_req.get(view), req;
        if (!req_view) {
            req_view = this.current_req.set(view, $H());
        }

        req = req_view.get(r_id);
        if (!req) {
            req = req_view.set(r_id, { count: 1 });
        }
        ['background', 'offset', 'rlist'].each(function(p) {
            if (!Object.isUndefined(params[p])) {
                req[p] = params[p];
            }
        });

        this.current_req_lookup.set(r_id, view);
    },

    // Removes a request to the current request queue.
    // view = (string) The view to remove a request for
    // r_id = (string) The request ID to remove
    _removeRequest: function(view, r_id)
    {
        var cr = this.current_req.get(view);
        if (cr) {
            cr.unset(r_id);
            if (!cr.size()) {
                this.current_req.unset(view);
            }
        }
        this.current_req_lookup.unset(r_id);
    },

    // offset = (integer) TODO
    // opts = (object) TODO [view]
    _updateContent: function(offset, opts)
    {
        opts = opts || {};

        if (!this._getBuffer(opts.view).sliceLoaded(offset)) {
            this._fetchBuffer($H(opts).merge({ offset: offset }).toObject());
            return false;
        }

        if (!this.uc_run) {
            // Code for viewport that only needs to be initialized once.
            this.uc_run = true;
            if (this.opts.onFirstContent) {
                this.opts.onFirstContent();
            }
        }

        var c = this.opts.content,
            c_nodes = [],
            page_size = this.getPageSize(),
            rows,
            sel = this.getSelected();

        if (this.opts.onClearRows) {
            this.opts.onClearRows(c.childElements());
        }

        this.scroller.updateSize();
        this.scrollTo(offset + 1, true);

        offset = this.currentOffset();
        rows = this.createSelection('rownum', $A($R(offset + 1, offset + page_size)));

        if (rows.size()) {
            rows.get('dataob').each(function(row) {
                var bg = $w(row.bg).without(this.opts.selected_class);
                if (sel.contains('uid', row.vp_id)) {
                    bg.push(this.opts.selected_class);
                }
                row.bg = bg.join(' ');
                c_nodes.push(this.template.evaluate(row));
            }, this);
            c.update(c_nodes.join(''));
        } else {
            // If loading a viewport for the first time, show a blank
            // viewport rather than the empty viewport status message.
            c.update((this.opts.empty && this.viewport_init != 1) ? this.opts.empty.innerHTML : '');
        }

        if (this.opts.onContent) {
            this.opts.onContent(rows);
        }

        return true;
    },

    _displayFetchError: function()
    {
        if (this.opts.onFail) {
            this.opts.onFail();
        }
        if (this.opts.error) {
            this.opts.content.update(this.opts.error.innerHTML);
        }
    },

    // rows = (array) An array of row numbers
    // callback = (function; optional) A callback function to run after we
    //            retrieve list of rows from server. Callback function
    //            receives one parameter - a ViewPort_Selection object
    //            containing the slice.
    // Return: Either a ViewPort_Selection object or false if the server needs
    //         to be queried.
    _getSlice: function(rows, callback)
    {
        var params = { rangeslice: 1, start: rows.min(), length: rows.size() },
            r_id,
            slice;

        slice = this.createSelection('rownum', rows);
        if (rows.size() == slice.size()) {
            return slice;
        }

        if (this.opts.onFetch) {
            this.opts.onFetch();
        }
        if (callback) {
            r_id = this.request_num++;
            params.request_id = r_id;
            this.slice_hash.set(r_id, callback);
        }
        this.opts.ajaxRequest(this.opts.fetch_action, this.addRequestParams(params, { noslice: true }));
        return false;
    },

    _handleWait: function(call)
    {
        this._clearWait();

        // Server did not respond in defined amount of time.  Alert the
        // callback function and set the next timeout.
        if (call && this.opts.onWait) {
            this.opts.onWait();
        }

        // Call wait handler every x seconds
        if (this.opts.viewport_wait) {
            this.waitHandler = this._handleWait.bind(this, true).delay(this.opts.viewport_wait);
        }
    },

    _clearWait: function()
    {
        if (this.waitHandler) {
            clearTimeout(this.waitHandler);
            this.waitHandler = null;
        }
    },

    visibleRows: function()
    {
        return this.opts.content.childElements();
    },

    getMetaData: function(id, view)
    {
        return this._getBuffer(view).getMetaData(id);
    },

    setMetaData: function(vals, view)
    {
        this._getBuffer(view).setMetaData(vals);
    },

    _getBuffer: function(view, create)
    {
        if (!create) {
            var b = this.views.get(view || this.view);
            if (b) {
                return b.buffer;
            }
        }
        return new ViewPort_Buffer(this, this.opts.buffer_pages, this.opts.limit_factor);
    },

    currentOffset: function()
    {
        return this.scroller.currentOffset();
    },

    // vs = (Viewport_Selection) A Viewport_Selection object.
    // flag = (string) Flag name.
    // add = (boolean) Whether to set/unset flag.
    updateFlag: function(vs, flag, add)
    {
        this._updateFlag(vs, flag, add, this.isFiltering());
        this._updateClass(vs, flag, add);
    },

    // vs = (Viewport_Selection) A Viewport_Selection object.
    // flag = (string) Flag name.
    // add = (boolean) Whether to set/unset flag.
    // filter = (boolean) Are we filtering results?
    _updateFlag: function(vs, flag, add, filter)
    {
        vs.get('dataob').each(function(r) {
            r.bg = (add) ? $w(r.bg).concat([ flag ]).join(' ') : $w(r.bg).without(flag).join(' ');
            if (filter) {
                this._updateFlag(this.createSelection('uid', r.vp_id, r.view), flag, add);
            }
        }, this);
    },

    // vs = (Viewport_Selection) A Viewport_Selection object.
    // flag = (string) Flag name.
    // add = (boolean) Whether to set/unset flag.
    _updateClass: function(vs, flag, add)
    {
        vs.get('div').each(function(d) {
            if (add) {
                d.addClassName(flag);
            } else {
                d.removeClassName(flag);
            }
        });
    },

    _getLineHeight: function()
    {
        if (this.line_height) {
            return this.line_height;
        }

        // To avoid hardcoding the line height, create a temporary row to
        // figure out what the CSS says.
        var d = new Element('DIV', { className: this.opts.content_class }).insert(new Element('DIV', { className: this.opts.row_class })).hide();
        $(document.body).insert(d);
        this.line_height = d.getHeight();
        d.remove();

        return this.line_height;
    },

    // (type) = (string) [null (DEFAULT), 'current', 'default', 'max']
    getPageSize: function(type)
    {
        switch (type) {
        case 'current':
            return Math.min(this.page_size, this.getMetaData('total_rows'));

        case 'default':
            return Math.max(parseInt(this.getPageSize('max') * 0.45), 5);

        case 'max':
            return parseInt(this._getMaxHeight() / this._getLineHeight());

        default:
            return this.page_size;
        }
    },

    _getMaxHeight: function()
    {
        return document.viewport.getHeight() - this.opts.content.viewportOffset()[1];
    },

    showSplitPane: function(show)
    {
        this.show_split_pane = show;
        this.onResize(false, true);
    },

    _renderViewport: function(noupdate)
    {
        if (!this.viewport_init) {
            return;
        }

        // This is needed for IE 6 - or else horizontal scrolling can occur.
        if (!this.opts.content.offsetHeight) {
            return this._renderViewport.bind(this, noupdate).defer();
        }

        var diff, h, pane, setpane,
            c = $(this.opts.content),
            de = document.documentElement,
            lh = this._getLineHeight();

        // Get split pane dimensions
        if (this.opts.split_pane) {
            pane = $(this.opts.split_pane);
            if (this.show_split_pane) {
                if (!pane.visible()) {
                    this._initSplitBar();
                    this.page_size = (this.splitbar_loc) ? this.splitbar_loc : this.getPageSize('default');
                }
                setpane = true;
            } else if (pane.visible()) {
                this.splitbar_loc = this.page_size;
                $(pane, this.splitbar).invoke('hide');
            }
        }

        if (!setpane) {
            this.page_size = this.getPageSize('max');
        }

        // Do some magic to ensure we never cause a horizontal scroll.
        h = lh * this.page_size;
        c.setStyle({ height: h + 'px' });
        if (setpane) {
            pane.setStyle({ height: (this._getMaxHeight() - h - lh) + 'px' }).show();
            this.splitbar.show();
        } else {
            if (diff = de.scrollHeight - de.clientHeight) {
                c.setStyle({ height: (lh * (this.page_size - 1)) + 'px' });
            }
        }

        if (!noupdate) {
            this.scroller.onResize();
        }
    },

    _initSplitBar: function()
    {
        if (this.splitbar) {
            return;
        }

        this.splitbar = $(this.opts.splitbar);
        new Drag(this.splitbar, {
            constraint: 'vertical',
            ghosting: true,
            onStart: function() {
                // Cache these values since we will be using them multiple
                // times in snap().
                var lh = this._getLineHeight();
                this.sp = { lh: lh, pos: $(this.opts.content).positionedOffset()[1], max: parseInt((this._getMaxHeight() - 100) / lh), lines: this.page_size };
            }.bind(this),
            snap: function(x, y, elt) {
                var l = parseInt((y - this.sp.pos) / this.sp.lh);
                if (l < 1) {
                    l = 1;
                } else if (l > this.sp.max) {
                    l = this.sp.max;
                }
                this.sp.lines = l;
                return [ x, this.sp.pos + (l * this.sp.lh) ];
            }.bind(this),
            onEnd: function() {
                this.page_size = this.sp.lines;
                this._renderViewport();
            }.bind(this)
        });
        this.splitbar.observe('dblclick', function() {
            this.page_size = this.getPageSize('default');
            this._renderViewport();
        }.bind(this));
    },

    createSelection: function(format, data, view)
    {
        var buffer = this._getBuffer(view);
        return buffer ? new ViewPort_Selection(buffer, format, data) : new ViewPort_Selection(this._getBuffer(this.view));
    },

    getViewportSelection: function(view)
    {
        var buffer = this._getBuffer(view);
        return this.createSelection('uid', buffer ? buffer.getAllUIDs() : [], view);
    },

    // vs = (Viewport_Selection | array) A Viewport_Selection object -or-, if
    //       opts.range is set, an array of row numbers.
    // opts = (object) TODO [add, range]
    select: function(vs, opts)
    {
        opts = opts || {};

        if (opts.range) {
            vs = this._getSlice(vs, this.select.bind(this));
            if (vs === false) {
                return;
            }
        }

        var b = this._getBuffer(),
            sel;

        if (!opts.add) {
            sel = this.getSelected();
            b.deselect(sel, true);
            this._updateClass(sel, this.opts.selected_class, false);
        }
        b.select(vs);
        this._updateClass(vs, this.opts.selected_class, true);
        if (this.opts.selectCallback) {
            this.opts.selectCallback(vs, opts);
        }
    },

    // vs = (Viewport_Selection) A Viewport_Selection object.
    // opts = (object) TODO [clearall]
    deselect: function(vs, opts)
    {
        opts = opts || {};

        if (!vs.size()) {
            return;
        }

        if (this._getBuffer().deselect(vs, opts && opts.clearall)) {
            this._updateClass(vs, this.opts.selected_class, false);
            if (this.opts.deselectCallback) {
                this.opts.deselectCallback(vs, opts)
            }
        }
    },

    getSelected: function()
    {
        return Object.clone(this._getBuffer().getSelected());
    }

}),

/**
 * ViewPort_Scroller
 */
ViewPort_Scroller = Class.create({

    initialize: function(vp)
    {
        this.vp = vp;
    },

    _createScrollBar: function()
    {
        if (this.scrollDiv) {
            return false;
        }

        var c = this.vp.opts.content;

        // Create the outer div.
        this.scrollDiv = new Element('DIV', { className: 'sbdiv', style: 'height:' + c.getHeight() + 'px;' }).hide();

        // Add scrollbar to parent viewport and give our parent a right
        // margin just big enough to accomodate the scrollbar.
        c.insert({ after: this.scrollDiv }).setStyle({ marginRight: '-' + this.scrollDiv.getWidth() + 'px' });

        // Create scrollbar object.
        this.scrollbar = new DimpSlider(this.scrollDiv, { buttonclass: { up: 'sbup', down: 'sbdown' }, cursorclass: 'sbcursor', onChange: this._onScroll.bind(this), onSlide: this.vp.opts.onSlide ? this.vp.opts.onSlide : null, pagesize: this.vp.getPageSize(), totalsize: this.vp.getMetaData('total_rows') });

        // Mouse wheel handler.
        c.observe(Prototype.Browser.Gecko ? 'DOMMouseScroll' : 'mousewheel', function(e) {
            // Fix issue on FF 3 (as of 3.0) that triggers two events
            if (Prototype.Browser.Gecko && e.eventPhase == 2) {
                return;
            }
            var move_num = this.vp.getPageSize();
            move_num = (move_num > 3) ? 3 : move_num;
            this.moveScroll(this.currentOffset() + ((e.wheelDelta >= 0 || e.detail < 0) ? (-1 * move_num) : move_num));
        }.bindAsEventListener(this));

        return true;
    },

    onResize: function()
    {
        if (!this.scrollDiv) {
            return;
        }

        // Update the container div.
        this.scrollsize = this.vp.opts.content.getHeight();
        this.scrollDiv.setStyle({ height: this.scrollsize + 'px' });

        // Update the scrollbar size
        this.updateSize();

        // Update displayed content.
        this.vp.requestContentRefresh(this.currentOffset());
    },

    updateSize: function()
    {
        if (!this._createScrollBar()) {
            this.scrollbar.updateHandleLength(this.vp.getPageSize(), this.vp.getMetaData('total_rows'));
        }
    },

    clear: function()
    {
        if (this.scrollDiv) {
            this.scrollbar.updateHandleLength(0, 0);
        }
    },

    // offset = (integer) Offset to move the scrollbar to
    moveScroll: function(offset)
    {
        this._createScrollBar();
        this.scrollbar.setScrollPosition(offset);
    },

    _onScroll: function()
    {
        if (!this.noupdate) {
            if (this.vp.opts.onScroll) {
                this.vp.opts.onScroll();
            }

            this.vp.requestContentRefresh(this.currentOffset());

            if (this.vp.opts.onScrollIdle) {
                this.vp.opts.onScrollIdle();
            }
        }
    },

    currentOffset: function()
    {
        return this.scrollbar ? this.scrollbar.getValue() : 0;
    }

}),

/**
 * ViewPort_Buffer
 *
 * Note: recognize the difference between offset (current location in the
 * viewport - starts at 0) with start parameters (the row numbers - starts
 * at 1).
 */
ViewPort_Buffer = Class.create({

    initialize: function(vp, b_pages, l_factor)
    {
        this.bufferPages = b_pages;
        this.limitFactor = l_factor;
        this.vp = vp;
        this.clear();
    },

    _limitTolerance: function()
    {
        return Math.round(this.bufferSize() * (this.limitFactor / 100));
    },

    bufferSize: function()
    {
        // Buffer size must be at least the maximum page size.
        return Math.round(Math.max(this.vp.getPageSize('max') + 1, this.bufferPages * this.vp.getPageSize()));
    },

    // d = TODO
    // l = TODO
    // opts = (object) TODO [slice, update]
    update: function(d, l, opts)
    {
        d = $H(d);
        l = $H(l);
        opts = opts || {};

        if (opts.slice) {
            d.each(function(o) {
                if (!this.data.get(o.key)) {
                    this.data.set(o.key, o.value);
                    this.inc.set(o.key, true);
                }
            }, this);
        } else {
            if (this.data.size()) {
                this.data.update(d);
                if (this.inc.size()) {
                    d.keys().each(function(k) {
                        this.inc.unset(k);
                    }, this);
                }
            } else {
                this.data = d;
            }
        }

        this.uidlist = (opts.update) ? l : (this.uidlist.size() ? this.uidlist.merge(l) : l);

        if (opts.update) {
            this.rowlist = $H();
        }
        l.each(function(o) {
            this.rowlist.set(o.value, o.key);
        }, this);
    },

    // offset = (integer) Offset of the beginning of the slice.
    sliceLoaded: function(offset)
    {
        return !this._rangeCheck($A($R(offset + 1, Math.min(offset + this.vp.getPageSize() - 1, this.getMetaData('total_rows')))));
    },

    isNearingLimit: function(offset)
    {
        if (this.uidlist.size() != this.getMetaData('total_rows')) {
            if (offset != 0 &&
                this._rangeCheck($A($R(Math.max(offset + 1 - this._limitTolerance(), 1), offset)))) {
                return 'top';
            } else if (this._rangeCheck($A($R(offset + 1, Math.min(offset + this._limitTolerance() + this.vp.getPageSize() - 1, this.getMetaData('total_rows')))).reverse())) {
                // Search for missing messages in reverse order since in
                // normal usage (sequential scrolling through the message
                // list) messages are more likely to be missing at furthest
                // from the current view.
                return 'bottom';
            }
        }
        return false;
    },

    _rangeCheck: function(range)
    {
        var i = this.inc.size();
        return range.any(function(o) {
            var g = this.rowlist.get(o);
            return (Object.isUndefined(g) || (i && this.inc.get(g)));
        }, this);
    },

    getData: function(uids)
    {
        return uids.collect(function(u) {
            var e = this.data.get(u);
            if (!Object.isUndefined(e)) {
                // We can directly write the rownum to the original object
                // since we will always rewrite when creating rows.
                e.domid = 'vp_row' + u;
                e.rownum = this.uidlist.get(u);
                e.vp_id = u;
                return e;
            }
        }, this).compact();
    },

    getAllUIDs: function()
    {
        return this.uidlist.keys();
    },

    getAllRows: function()
    {
        return this.rowlist.keys();
    },

    rowsToUIDs: function(rows)
    {
        return rows.collect(function(n) {
            return this.rowlist.get(n);
        }, this).compact();
    },

    // vs = (Viewport_Selection) TODO
    select: function(vs)
    {
        this.selected.add('uid', vs.get('uid'));
    },

    // vs = (Viewport_Selection) TODO
    // clearall = (boolean) Clear all entries?
    deselect: function(vs, clearall)
    {
        var size = this.selected.size();

        if (clearall) {
            this.selected.clear();
        } else {
            this.selected.remove('uid', vs.get('uid'));
        }
        return size != this.selected.size();
    },

    getSelected: function()
    {
        return this.selected;
    },

    // rownums = (array) Array of row numbers to remove.
    remove: function(rownums)
    {
        var minrow = rownums.min(),
            newsize,
            rowsize = this.rowlist.size(),
            rowsubtract = 0;
        newsize = rowsize - rownums.size();

        return this.rowlist.keys().each(function(n) {
            if (n >= minrow) {
                var id = this.rowlist.get(n), r;
                if (rownums.include(n)) {
                    this.data.unset(id);
                    this.uidlist.unset(id);
                    rowsubtract++;
                } else if (rowsubtract) {
                    r = n - rowsubtract;
                    this.rowlist.set(r, id);
                    this.uidlist.set(id, r);
                }
                if (n > newsize) {
                    this.rowlist.unset(n);
                }
            }
        }, this);
    },

    clear: function()
    {
        this.data = $H();
        this.inc = $H();
        this.mdata = $H({ total_rows: 0 });
        this.rowlist = $H();
        this.selected = new ViewPort_Selection(this);
        this.uidlist = $H();
    },

    getMetaData: function(id)
    {
        return this.mdata.get(id);
    },

    setMetaData: function(vals)
    {
        this.mdata.update(vals);
    }

}),

/**
 * ViewPort_Filter
 */
ViewPort_Filter = Class.create({

    initialize: function(vp, action, callback)
    {
        this.vp = vp;
        this.action = action;
        this.callback = callback;

        // Initialize other variables
        this.filterid = 0;
        this.filtering = this.last_filter = this.last_folder = this.last_folder_params = null;
    },

    // val = (string) The string to filter on. if null, will use the last
    //                filter string.
    filter: function(val, params)
    {
        params = params || {};

        if (val === null) {
            val = this.last_filter;
        } else {
            val = val.toLowerCase();
            if (val == this.last_filter) {
                return;
            }
        }

        if (!val) {
            this.clear();
            return;
        }

        this.last_filter = val;

        if (this.filtering) {
            this.vp._fetchBuffer({ offset: 0, params: params });
            return;
        }

        this.filtering = ++this.filterid + '%search%';
        this.last_folder = this.vp.view;
        this.last_folder_params = this.vp.getMetaData('additional_params').merge(params);

        // Filter visible rows immediately.
        var c = this.vp.opts.content, delrows;
        delrows = c.childElements().findAll(function(n) {
            return n.getText(true).toLowerCase().indexOf(val) == -1;
        });
        if (this.vp.opts.onClearRows) {
            this.vp.opts.onClearRows(delrows);
        }
        delrows.invoke('remove');
        this.vp.scroller.clear();
        if (this.vp.opts.empty && !c.childElements().size()) {
            c.update(this.vp.opts.empty.innerHTML);
        }

        this.vp.loadView(this.filtering, this.last_folder_params);
    },

    isFiltering: function()
    {
        return this.filtering;
    },

    getAction: function()
    {
        return this.action;
    },

    // params is a Hash object
    addFilterParams: function(params)
    {
        if (!this.filtering) {
            return params;
        }

        params.update({ filter: this.last_filter });

        // Get parameters from a callback function, if defined.
        if (this.callback) {
            params.update(this.callback());
        }

        return params;
    },

    clear: function(reset)
    {
        if (this.filtering) {
            var fname = this.filtering;
            this.filtering = null;
            if (!reset) {
                this.vp.loadView(this.last_folder, this.last_folder_params);
            }
            this.vp.deleteView(fname);
            this.last_filter = this.last_folder = null;
        }
    }

}),

/**
 * ViewPort_Selection
 */
ViewPort_Selection = Class.create({

    // Formats:
    //     'dataob' = Data objects
    //     'div' = DOM DIVs
    //     'domid' = DOM IDs
    //     'rownum' = Row numbers
    //     'uid' = Unique IDs
    initialize: function(buffer, format, data)
    {
        this.buffer = buffer;
        this.clear();
        if (!Object.isUndefined(format)) {
            this.add(format, data);
        }
    },

    add: function(format, d)
    {
        var c = this._convert(format, d);
        this.data = (this.data.size()) ? this.data.concat(c).uniq() : c;
    },

    remove: function(format, d)
    {
        this.data = this.data.diff(this._convert(format, d));
    },

    _convert: function(format, d)
    {
        d = Object.isArray(d) ? d : [ d ];
        switch (format) {
        case 'dataob':
            return d.pluck('vp_id');

        case 'div':
            return d.pluck('id').invoke('substring', 6);

        case 'domid':
            return d.invoke('substring', 6);

        case 'rownum':
            return this.buffer.rowsToUIDs(d);

        case 'uid':
            return d;
        }
    },

    clear: function()
    {
        this.data = [];
    },

    get: function(format)
    {
        format = Object.isUndefined(format) ? 'uid' : format;
        if (format == 'uid') {
            return this.data;
        }
        var d = this.buffer.getData(this.data);

        switch (format) {
        case 'dataob':
            return d;

        case 'div':
            return d.pluck('domid').collect(function(e) { return $(e); }).compact();

        case 'domid':
            return d.pluck('domid');

        case 'rownum':
            return d.pluck('rownum');
        }
    },

    contains: function(format, d)
    {
        return this.data.include(this._convert(format, d).first());
    },

    // params = (Object) Key is search key, value is object -> key of object
    // must be the following:
    //   equal - Matches any value contained in the query array.
    //   not - Matches any value not contained in the query array.
    //   regex - Matches the RegExp contained in the query.
    search: function(params)
    {
        return new ViewPort_Selection(this.buffer, 'uid', this.get('dataob').findAll(function(i) {
            // i = data object
            return $H(params).all(function(k) {
                // k.key = search key; k.value = search criteria
                return $H(k.value).all(function(s) {
                    // s.key = search type; s.value = search query
                    switch (s.key) {
                    case 'equal':
                    case 'not':
                        var r = i[k.key] && s.value.include(i[k.key]);
                        return (s.key == 'equal') ? r : !r;

                    case 'regex':
                        return i[k.key].match(s.value);
                    }
                });
            });
        }).pluck('vp_id'));
    },

    size: function()
    {
        return this.data.size();
    },

    set: function(vals)
    {
        this.get('dataob').each(function(d) {
            $H(vals).each(function(v) {
                d[v.key] = v.value;
            });
        });
    }

});

/** Utility Functions **/
Object.extend(Array.prototype, {
    // Need our own diff() function because prototypejs's without() function
    // does not handle array input.
    diff: function(values) {
        return this.select(function(value) {
            return !values.include(value);
        });
    },
    numericSort: function() {
        return this.sort(function(a,b) { return (a > b) ? 1 : ((a < b) ? -1 : 0); });
    }
});
