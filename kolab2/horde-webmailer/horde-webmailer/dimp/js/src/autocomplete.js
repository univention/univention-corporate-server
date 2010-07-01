/**
 * autocomplete.js - A javascript library which implements autocomplete.
 * Requires prototype.js v1.6.0.2+ and scriptaculous v1.8.0+ (effects.js)
 *
 * Adapted from script.aculo.us controls.js v1.8.0
 *   (c) 2005-2007 Thomas Fuchs, Ivan Krstic, and Jon Tirsen
 *   Contributors: Richard Livsey, Rahul Bhargava, Rob Wills
 *   http://script.aculo.us/
 *
 * The original script was freely distributable under the terms of an
 * MIT-style license.
 *
 * $Horde: dimp/js/src/autocomplete.js,v 1.1.2.3 2009-02-20 05:20:22 slusarz Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var Autocompleter = {};
Autocompleter.Base = Class.create({
    baseInitialize: function(element, update, options)
    {
        this.element = $(element);
        this.update = $(update).hide();
        this.active = this.changed = this.hasFocus = false;
        this.entryCount = this.index = 0;
        this.observer = null;
        this.oldElementValue = this.element.value;

        this.options = Object.extend({
            paramName: this.element.name,
            tokens: [],
            frequency: 0.4,
            minChars: 1,
            onHide: this._onHide.bind(this),
            onShow: this._onShow.bind(this)
        }, (this._setOptions) ? this._setOptions(options) : (options || {}));

        // Force carriage returns as token delimiters anyway
        if (!this.options.tokens.include('\n')) {
            this.options.tokens.push('\n');
        }

        this.element.writeAttribute('autocomplete', 'off').observe("blur", this._onBlur.bindAsEventListener(this)).observe(Prototype.Browser.Gecko ? "keypress" : "keydown", this._onKeyPress.bindAsEventListener(this));
    },

    _onShow: function(elt, update)
    {
        var p = update.getStyle('position');
        if (!p || p == 'absolute') {
            update.setStyle({ position: 'absolute' }).clonePosition(elt, {
                setHeight: false,
                offsetTop: elt.offsetHeight
            });
        }
        new Effect.Appear(update, { duration: 0.15 });
    },

    _onHide: function(elt, update)
    {
        new Effect.Fade(update, { duration: 0.15 });
    },

    show: function()
    {
        if (!this.update.visible()) {
            this.options.onShow(this.element, this.update);
        }

        if (Prototype.Browser.IE &&
            !this.iefix &&
            this.update.getStyle('position') == 'absolute') {
            this.iefix = new Element('IFRAME', { src: 'javascript:false;', frameborder: 0, scrolling: 'no' }).setStyle({ position: 'absolute', filter: 'progid:DXImageTransform.Microsoft.Alpha(opactiy=0)', zIndex: 1 }).hide();
            this.update.setStyle({ zIndex: 2 }).insert({ after: this.iefix });
        }

        if (this.iefix) {
            this._fixIEOverlapping.bind(this).delay(0.05);
        }
    },

    _fixIEOverlapping: function()
    {
        this.iefix.clonePosition(this.update).show();
    },

    hide: function()
    {
        this.stopIndicator();
        if (this.update.visible()) {
            this.options.onHide(this.element, this.update);
            if (this.iefix) {
                this.iefix.hide();
            }
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

    _onKeyPress: function(e)
    {
        if (this.active) {
            switch (e.keyCode) {
            case Event.KEY_TAB:
            case Event.KEY_RETURN:
                this.selectEntry();
                e.stop();
                return;

            case Event.KEY_ESC:
                this.hide();
                this.active = false;
                e.stop();
                return;

            case Event.KEY_LEFT:
            case Event.KEY_RIGHT:
                return;

            case Event.KEY_UP:
            case Event.KEY_DOWN:
                if (e.keyCode == Event.KEY_UP) {
                    this.markPrevious();
                } else {
                    this.markNext();
                }
                this.render();
                e.stop();
                return;
            }
        } else {
            switch (e.keyCode) {
            case 0:
                if (!Prototype.Browser.WebKit) {
                    break;
                }
                // Fall through to below case
                //
            case Event.KEY_TAB:
            case Event.KEY_RETURN:
                return;
            }
        }

        this.changed = this.hasFocus = true;

        if (this.observer) {
            clearTimeout(this.observer);
        }
        this.observer = this.onObserverEvent.bind(this).delay(this.options.frequency);
    },

    _onHover: function(e)
    {
        var elt = e.findElement('LI');
        if (this.index != elt.autocompleteIndex) {
            this.index = elt.autocompleteIndex;
            this.render();
        }
        e.stop();
    },

    _onClick: function(e)
    {
        this.index = e.findElement('LI').autocompleteIndex;
        this.selectEntry();
    },

    _onBlur: function(e)
    {
        // Needed to make click events work
        this.hide.bind(this).delay(0.25);
        this.active = this.hasFocus = false;
    },

    render: function()
    {
        if (this.entryCount > 0) {
            for (var i = 0; i < this.entryCount; ++i) {
                [ this.getEntry(i) ].invoke(this.index == i ? 'addClassName' : 'removeClassName', 'selected');
            }
            if (this.hasFocus) {
                this.show();
                this.active = true;
            }
        } else {
            this.active = false;
            this.hide();
        }
    },

    markPrevious: function()
    {
        if (this.index) {
            --this.index;
        } else {
            this.index = this.entryCount - 1;
        }
        this.getEntry(this.index).scrollIntoView(true);
    },

    markNext: function()
    {
        if (this.index < this.entryCount - 1) {
            ++this.index;
        } else {
            this.index = 0;
        }
        this.getEntry(this.index).scrollIntoView(false);
    },

    getEntry: function(index)
    {
        return this.update.down().childElements()[index];
    },

    selectEntry: function()
    {
        this.active = false;
        this.updateElement(this.getEntry(this.index));
        this.hide();
    },

    updateElement: function(elt)
    {
        var bounds, newValue, nodes, whitespace, v,
            value = '';

        if (this.options.updateElement) {
            this.options.updateElement(elt);
            return;
        }

        if (this.options.select) {
            nodes = $(elt).select('.' + this.options.select) || [];
            if (nodes.size()) {
                value = nodes[0].collectTextNodes(this.options.select);
            }
        } else {
            value = elt.collectTextNodesIgnoreClass('informal');
        }

        bounds = this.getTokenBounds();
        if (bounds[0] != -1) {
            v = this.element.value;
            newValue = v.substr(0, bounds[0]);
            whitespace = v.substr(bounds[0]).match(/^\s+/);
            if (whitespace) {
                newValue += whitespace[0];
            }
            this.element.value = newValue + value + v.substr(bounds[1]);
        } else {
            this.element.value = value;
        }
        this.element.focus();

        if (this.options.afterUpdateElement) {
            this.options.afterUpdateElement(this.element, elt);
        }

        this.oldElementValue = this.element.value;
    },

    updateChoices: function(choices)
    {
        var c, i = 0;

        if (!this.changed && this.hasFocus) {
            this.update.update(choices);
            c = this.update.down().childElements();
            this.entryCount = c.size();
            c.each(function(n) {
                n.autocompleteIndex = i++;
                this.addObservers(n);
            }.bind(this));

            this.stopIndicator();
            this.index = 0;

            if (this.entryCount == 1 && this.options.autoSelect) {
                this.selectEntry();
            } else {
                this.render();
            }
        }
    },

    addObservers: function(elt)
    {
        $(elt).observe("mouseover", this._onHover.bindAsEventListener(this)).observe("click", this._onClick.bindAsEventListener(this));
    },

    onObserverEvent: function()
    {
        this.changed = false;
        if (this.getToken().length >= this.options.minChars) {
            this.getUpdatedChoices();
        } else {
            this.active = false;
            this.hide();
        }
        this.oldElementValue = this.element.value;
    },

    getToken: function()
    {
        var bounds = this.getTokenBounds();
        return this.element.value.substring(bounds[0], bounds[1]).strip();
    },

    getTokenBounds: function()
    {
        var diff, i, l, offset, tp,
            index = 0,
            value = this.element.value,
            nextTokenPos = value.length,
            prevTokenPos = -1,
            boundary = Math.min(value.length, this.oldElementValue.length);

        if (value.strip().empty()) {
            return [ -1, 0 ];
        }

        diff = boundary;
        for (i = 0; i < boundary; ++i) {
            if (value[i] != this.oldElementValue[i]) {
                diff = index;
                break;
            }
        }

        offset = (diff == this.oldElementValue.length ? 1 : 0);

        for (l = this.options.tokens.length; index < l; ++index) {
            tp = value.lastIndexOf(this.options.tokens[index], diff + offset - 1);
            if (tp > prevTokenPos) {
                prevTokenPos = tp;
            }
            tp = value.indexOf(this.options.tokens[index], diff + offset);
            if (tp != -1 && tp < nextTokenPos) {
                nextTokenPos = tp;
            }
        }
        return [ prevTokenPos + 1, nextTokenPos ];
    }
});

Ajax.Autocompleter = Class.create(Autocompleter.Base, {
    initialize: function(element, update, url, options)
    {
        this.baseInitialize(element, update, options);
        this.options = Object.extend(this.options, {
            asynchronous: true,
            onComplete: this._onComplete.bind(this),
            defaultParams: $H(this.options.parameters)
        });
        this.url = url;
    },

    getUpdatedChoices: function()
    {
        var p = Object.clone(this.options.defaultParams);
        this.startIndicator();
        p.set(this.options.paramName, this.getToken());
        this.options.parameters = p.toQueryString();
        new Ajax.Request(this.url, this.options);
    },

    _onComplete: function(request)
    {
        this.updateChoices(request.responseText);
    }
});

Autocompleter.Local = Class.create(Autocompleter.Base, {
    initialize: function(element, update, arr, options)
    {
        this.baseInitialize(element, update, options);
        this.options.arr = arr;
    },

    getUpdatedChoices: function()
    {
        this.updateChoices(this.options.selector(this));
    },

    _setOptions: function(options)
    {
        this.options = Object.extend({
            choices: 10,
            partialSearch: true,
            partialChars: 2,
            ignoreCase: true,
            fullSearch: false,
            selector: this._selector.bind(this)
        }, options || {});
    },

    _selector: function(instance)
    {
        var elem, foundPos,
            entry = instance.getToken(),
            i = 0,
            partial = [],
            ret = [];

        for (; i < instance.options.arr.length && ret.length < instance.options.choices ; ++i) {
            elem = instance.options.arr[i];
            foundPos = instance.options.ignoreCase ?
                elem.toLowerCase().indexOf(entry.toLowerCase()) :
                elem.indexOf(entry);

            while (foundPos != -1) {
                if (foundPos == 0 && elem.length != entry.length) {
                    ret.push("<li><strong>" + elem.substr(0, entry.length) + "</strong>" + elem.substr(entry.length) + "</li>");
                  break;
                } else if (entry.length >= instance.options.partialChars &&
                           instance.options.partialSearch &&
                           foundPos != -1 &&
                           (instance.options.fullSearch || /\s/.test(elem.substr(foundPos-1,1)))) {
                    partial.push("<li>" + elem.substr(0, foundPos) + "<strong>" + elem.substr(foundPos, entry.length) + "</strong>" + elem.substr(foundPos + entry.length) + "</li>");
                    break;
                }

                foundPos = instance.options.ignoreCase ?
                    elem.toLowerCase().indexOf(entry.toLowerCase(), foundPos + 1) :
                    elem.indexOf(entry, foundPos + 1);
            }
        }

        if (partial.length) {
            ret = ret.concat(partial.slice(0, instance.options.choices - ret.length));
        }

        return "<ul>" + ret.join('') + "</ul>";
    }
});
