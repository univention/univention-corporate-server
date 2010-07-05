/**
 * DimpSlider.js - A minimalist library to create a slider that acts like a
 * browser's native scrollbar.
 * Requires prototype.js 1.6.0.2+
 *
 * Adapted from script.aculo.us slider.js v1.8.0
 *   (c) 2005-2007 Marty Haught, Thomas Fuchs
 *   http://script.aculo.us/
 *
 * The original script was freely distributable under the terms of an
 * MIT-style license.
 *
 * $Horde: dimp/js/src/DimpSlider.js,v 1.6.2.11 2009-01-06 15:22:37 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var DimpSlider = Class.create({
    value: 0,

    initialize: function(track, options)
    {
        this.track = $(track);
        this.options = Object.extend({
            buttonclass: null,
            cursorclass: null,
            pagesize: 0,
            totalsize: 0
        }, options || {});

        this.handle = new Element('DIV', { className: this.options.cursorclass }).makePositioned();
        this.track.insert(this.handle);

        if (this.options.buttonclass) {
            this.sbup = new Element('DIV', { className: this.options.buttonclass.up });
            this.sbdown = new Element('DIV', { className: this.options.buttonclass.down }).makePositioned();
            this.handle.insert({ before: this.sbup, after: this.sbdown });
            [ this.sbup, this.sbdown ].invoke('observe', 'mousedown', this._arrowClick.bindAsEventListener(this));
        }

        this.sbdownsize = this.sbupsize = this.value = 0;
        this.active = this.dragging = false;

        if (this._showScroll()) {
            this._initScroll();
        }

        this.eventMU = this._endDrag.bindAsEventListener(this);
        this.eventMM = this._update.bindAsEventListener(this);

        [ this.handle, this.track ].invoke('observe', 'mousedown', this._startDrag.bindAsEventListener(this));
    },

    _initScroll: function()
    {
        if (this.init) {
            return false;
        }
        this.init = true;
        this.track.show();
        if (this.sbup) {
            this.sbupsize = this.sbup.offsetHeight;
            this.sbdownsize = this.sbdown.offsetHeight;
        }
        this._updateHandleLength();
        return true;
    },

    _startDrag: function(e)
    {
        if (!e.isLeftClick()) {
            return;
        }

        var dir,
            hoffsets = this.handle.cumulativeOffset();

        if (e.element() == this.track) {
            dir = (e.pointerY() < hoffsets[1]) ? -1 : 1;
            this.setScrollPosition(this.getValue() - dir + (this.options.pagesize * dir));
        } else {
            this.curroffsets = this.track.cumulativeOffset();
            this.offsetY = e.pointerY() - hoffsets[1] + this.sbupsize;
            this.active = true;

            document.observe('mouseup', this.eventMU);
            document.observe('mousemove', this.eventMM);
        }

        e.stop();
    },

    _update: function(e)
    {
        if (this.active) {
            this.dragging = true;
            this._setScrollPosition('px', Math.min(Math.max(0, e.pointerY() - this.offsetY - this.curroffsets[1]), this.handletop));
            if (this.options.onSlide) {
                this.options.onSlide();
            }
            if (Prototype.Browser.WebKit) {
                window.scrollBy(0,0);
            }
            e.stop();
        }
    },

    _endDrag: function(e)
    {
        if (this.active && this.dragging) {
            this._updateFinished();
            e.stop();

            document.stopObserving('mouseup', this.eventMU);
            document.stopObserving('mousemove', this.eventMM);
        }
        this.active = this.dragging = false;
    },

    _arrowClick: function(e)
    {
        this.setScrollPosition(this.getValue() + ((e.element() == this.sbup) ? -1 : 1));
    },

    _updateFinished: function()
    {
        if (this.options.onChange) {
            this.options.onChange();
        }
    },

    updateHandleLength: function(pagesize, totalsize)
    {
        this.options.pagesize = pagesize;
        this.options.totalsize = totalsize;
        if (!this._showScroll()) {
            this.value = 0;
            this.track.hide();
            return;
        }
        if (!this._initScroll()) {
            this.track.show();
            this._updateHandleLength();
        }
    },

    _updateHandleLength: function()
    {
        var t = this.track.offsetHeight - this.sbupsize - this.sbdownsize;

        // Minimum handle size = 10px
        this.handle.setStyle({ height: Math.max(10, Math.round((this.options.pagesize / this.options.totalsize) * t)) + 'px' });
        this.handletop = t - this.handle.offsetHeight;
        if (this.sbdown) {
            this.sbdown.setStyle({ top: this.handletop + 'px' });
        }
        this._setScrollPosition('val', this.getValue());
    },

    getValue: function()
    {
        return this.value;
    },

    setScrollPosition: function(val)
    {
        if (this._showScroll()) {
            var oldval = this.getValue();
            this._setScrollPosition('val', val);
            if (oldval != this.getValue()) {
                this._updateFinished();
            }
        }
    },

    _setScrollPosition: function(type, data)
    {
        this.value = (type == 'val')
            ? Math.min(Math.max(0, data), this.options.totalsize - this.options.pagesize)
            : Math.max(0, Math.round(Math.min(data, this.handletop) / this.handletop * (this.options.totalsize - this.options.pagesize)));
        this.handlevalue = (type == 'px')
            ? data
            : Math.round(this.getValue() / (this.options.totalsize - this.options.pagesize) * this.handletop);
        this.handle.setStyle({ top: this.handlevalue + 'px' });
    },

    _showScroll: function()
    {
        return (this.options.pagesize < this.options.totalsize);
    }
});
