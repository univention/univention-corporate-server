/**
 * Reuseable keyboard or mouse driven list component. Based on
 * Scriptaculous' AutoCompleter.
 *
 * $Horde: imp/js/src/KeyNavList.js,v 1.8.2.5 2009-01-06 15:24:03 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var KeyNavList = Class.create({
    // Vars used and defaulting to empty:
    //     active, entryCount

    initialize: function(element, options)
    {
        var clickfunc = this.onClick.bindAsEventListener(this),
            entry,
            i = 0,
            overfunc = this.onHover.bindAsEventListener(this);

        this.element = $(element);
        this.options = options || {};
        this.index = -1;

        this.entryCount = this.element.firstDescendant().childElements().size();
        for (; i < this.entryCount; i++) {
            entry = this.getEntry(i);
            entry.writeAttribute('autocompleteIndex', i);
            entry.observe('click', clickfunc);
            entry.observe('mouseover', overfunc);
        }

        this.options.onShow = this.options.onShow ||
            function(elt) { new Effect.Appear(elt, { duration: 0.15 }); };
        this.options.onHide = this.options.onHide ||
            function(elt) { new Effect.Fade(elt, { duration: 0.15 }); };

        this.element.observe('blur', this.onBlur.bind(this));
        document.observe('keypress', this.onKeyPress.bindAsEventListener(this));
    },

    show: function()
    {
        this.active = true;
        if (!this.element.visible()) {
            this.options.onShow(this.element);
        }
        if (!this.iefix &&
            (navigator.appVersion.indexOf('MSIE') > 0) &&
            (this.element.getStyle('position') == 'absolute')) {
            this.element.insert({ after:
                '<iframe id="' + this.element.id + '_iefix" '
                + 'style="display:none;position:absolute;filter:progid:DXImageTransform.Microsoft.Alpha(opacity=0);" '
                + 'src="javascript:false;" frameborder="0" scrolling="no"></iframe>'});
            this.iefix = $(this.element.id + '_iefix');
        }
        if (this.iefix) {
            setTimeout(this.fixIEOverlapping.bind(this), 50);
        }
    },

    fixIEOverlapping: function()
    {
        this.iefix.clonePosition(this.element).setStyle({ zIndex: 1 }).show();
        this.element.setStyle({ zIndex: 2 });
    },

    hide: function()
    {
        this.active = false;
        this.stopIndicator();
        if (this.element.visible()) {
            this.options.onHide(this.element);
        }
        if (this.iefix) {
            this.iefix.hide();
        }
    },

    startIndicator: function()
    {
        if (this.options.indicator) {
            $(this.options.indicator).show();
        }
    },

    stopIndicator: function()
    {
        if (this.options.indicator) {
            $(this.options.indicator).hide();
        }
    },

    onKeyPress: function(e)
    {
        if (!this.active) {
            return;
        }

        switch (e.keyCode) {
        case Event.KEY_TAB:
        case Event.KEY_RETURN:
            this.selectEntry();
            e.stop();

        case Event.KEY_ESC:
            this.hide();
            this.active = false;
            e.stop();
            return;

        case Event.KEY_LEFT:
        case Event.KEY_RIGHT:
            return;

        case Event.KEY_UP:
            this.markPrevious();
            this.render();
            e.stop();
            return;

        case Event.KEY_DOWN:
            this.markNext();
            this.render();
            e.stop();
            return;
        }
    },

    onHover: function(e)
    {
        var element = e.findElement('LI'),
            index = parseInt(element.readAttribute('autocompleteIndex'));
        if (this.index != index) {
            this.index = index;
            this.render();
        }
        e.stop();
    },

    onClick: function(e)
    {
        var element = e.findElement('LI');
        this.index = parseInt(element.readAttribute('autocompleteIndex'));
        this.selectEntry();
        this.hide();
        e.stop();
    },

    onBlur: function()
    {
        setTimeout(this.hide.bind(this), 250);
        this.active = false;
    },

    render: function()
    {
        if (this.entryCount > 0) {
            for (var i = 0; i < this.entryCount; i++) {
                [ this.getEntry(i) ].invoke(this.index == i ? 'addClassName' : 'removeClassName', 'selected');
            }
            this.show();
            this.active = true;
        } else {
            this.hide();
            this.active = false;
        }
    },

    markPrevious: function()
    {
        if (this.index > 0) {
            this.index--;
        } else {
            this.index = this.entryCount - 1;
        }
    },

    markNext: function()
    {
        if (this.index < this.entryCount - 1) {
            this.index++;
        } else {
            this.index = 0;
        }
    },

    getEntry: function(index)
    {
        return this.element.down().down(index);
    },

    getCurrentEntry: function()
    {
        return this.getEntry(this.index);
    },

    selectEntry: function()
    {
        this.active = false;
        if (typeof this.options.onChoose == 'function') {
            this.options.onChoose(this.getCurrentEntry());
        }
    }

});
