/**
 * dragdrop.js - A minimalist library to handle drag/drop actions.
 * Requires prototype.js 1.6.0.2+
 *
 * Adapted from SkyByte.js/SkyByteDD.js v1.0-beta, May 17 2007
 *   (c) 2007 Aleksandras Ilarionovas (Alex)
 *   http://www.skybyte.net/scripts/
 *
 * Scrolling and ghosting code adapted from script.aculo.us dragdrop.js v1.8.0
 *   (c) 2005-2007 Thomas Fuchs (http://script.aculo.us, http://mir.aculo.us)
 *   (c) 2005-2007 Sammi Williams (http://www.oriontransfer.co.nz, sammi@oriontransfer.co.nz)
 *
 * The original scripts were freely distributable under the terms of an
 * MIT-style license.
 *
 * Usage:
 *   new Drag(element, {
 *       classname: '',           // Class name of the drag element
 *       caption: '',             // Either string or function to set caption
 *                                // on mouse move
 *       ghosting: false,         // Show ghost outline when dragging.
 *       offset: { x:0, y:0 },    // An offset to apply to ghosted elements.
 *       scroll: element,         // Scroll this element when above/below.
 *                                // Only working for vertical elements
 *       snap: null,              // If ghosting, snap allows to specify
 *                                // coords at which the ghosted image will
 *                                // "snap" into place.
 *       threshold: 0,            // Move threshold
 *       // For the following functions, d = drop element, e = event object
 *       onStart: function(d,e),  // A function to run on mousedown
 *       onDrag: function(d,e),   // A function to run on mousemove
 *       onEnd: function(d,e)     // A function to run on mouseup
 *   });
 *
 *   new Drop(element, {
 *       accept: [],           // Accept filter by tag name(s) or leave empty
 *                             // to accept all tags
 *       caption: '',          // Either string or function to set caption on
 *                             // mouse over
 *       hoverclass: '',       // Change the drag element to this class when
 *                             // hovering over an element.
 *       onDrop: function(drop,drag)  // Function fired when mouse button
 *                                    // released (a/k/a a drop event)
 *       onOver: function(drop,drag)  // Function fired when mouse over zone
 *       onOut: function(drop,drag)   // Function fired when mouse leaves the
 *                                    // zone
 *  });
 *
 * $Horde
 *
 * @author Michael Slusarz <slusarz@curecanti.org>
 */

var DragDrop = {
    Drags: {
        drags: $H(),

        register: function(obj)
        {
            if (!this.drags.size()) {
                if (!this.div) {
                    this.div = new Element('DIV', { className: obj.options.classname }).hide();
                }
                $(document.body).insert(this.div);
            }

            this.drags.set(obj.element.readAttribute('id'), obj);
        },

        unregister: function(obj)
        {
            if (this.drag == obj.element) {
                this.drag.deactivate();
            }

            this.drags.unset(obj.element.readAttribute('id'));

            if (!this.drags.size() && this.div) {
                this.div.remove();
            }
        },

        get_drag: function(el)
        {
            return this.drags.get(Object.isElement(el) ? $(el).readAttribute('id') : el);
        },

        activate: function(drag)
        {
            if (this.drag) {
                this.deactivate();
            }
            this.drag = drag;
            this.mousemoveE = drag._mouseMove.bindAsEventListener(drag);
            this.mouseupE = drag._mouseUp.bindAsEventListener(drag);
            document.observe('mousemove', this.mousemoveE);
            document.observe('mouseup', this.mouseupE);
        },

        deactivate: function()
        {
            if (this.drag) {
                this.drag = null;
                document.stopObserving('mousemove', this.mousemoveE);
                document.stopObserving('mouseup', this.mouseupE);
            }
        }
    },

    Drops: {
        drops: $H(),

        register: function(obj)
        {
            this.drops.set(obj.element.readAttribute('id'), obj);
        },

        unregister: function(obj)
        {
            if (this.drop == obj.element) {
                this.drop = null;
            }

            this.drops.unset(obj.element.readAttribute('id'));
        },

        get_drop: function(el)
        {
            return this.drops.get(Object.isElement(el) ? $(el).readAttribute('id') : el);
        }
    },

    validDrop: function(el)
    {
        var d = DragDrop.Drops.drop;
        return (d &&
                el &&
                el != d.element &&
                (!d.options.accept.size() ||
                 d.options.accept.include(el.tagName)));
    }
},

Drag = Class.create({

    initialize: function(el) {
        this.element = $(el);
        this.options = Object.extend({
            caption: '',
            classname: 'drag',
            constraint: null,
            ghosting: false,
            scroll: null,
            snap: null,
            threshold: 0,
            onDrag: null,
            onEnd: null,
            onStart: null
        }, arguments[1] || {});
        this.mousedownE = this._mouseDown.bindAsEventListener(this);
        this.element.observe('mousedown', this.mousedownE);
        if (this.options.scroll) {
            this.options.scroll = $(this.options.scroll);
        }
        DragDrop.Drags.register(this);

        // Disable text selection.
        // See: http://ajaxcookbook.org/disable-text-selection/
        // Stopping the event on mousedown works on all browsers, but avoid
        // that if possible because it will prevent any event handlers further
        // up the DOM tree from firing.
        if (Prototype.Browser.IE) {
            this.element.observe('selectstart', Event.stop);
        } else if (Prototype.Browser.Gecko) {
            this.element.setStyle({ MozUserSelect: 'none' });
        }
    },

    destroy: function()
    {
        this.element.stopObserving('mousedown', this.mousedownE);
        DragDrop.Drags.unregister(this);
    },

    _mouseDown: function(e)
    {
        $(document.body).setStyle({ cursor: 'default' });
        DragDrop.Drags.activate(this);
        this.move = 0;
        this.wasDragged = false;
        this.lastcaption = null;

        if (Object.isFunction(this.options.onStart)) {
            this.options.onStart(this, e);
        }

        if (!Prototype.Browser.IE && !Prototype.Browser.Gecko) {
            e.stop();
        }
    },

    _mouseMove: function(e)
    {
        var oleft, otop, vo, xy;

        if (++this.move <= this.options.threshold) {
            return;
        }

        this.lastCoord = xy = [ e.pointerX(), e.pointerY() ];

        if (this.options.ghosting) {
            if (!this.ghost) {
                oleft = this.element.offsetLeft;
                otop = this.element.offsetTop;
                this.ghost = $(this.element.cloneNode(true)).writeAttribute('id', null).setOpacity(0.7).clonePosition(this.element, { setLeft: false, setTop: false }).setStyle({ left: oleft + 'px', position: 'absolute', top: otop + 'px', zIndex: parseInt(this.element.getStyle('zIndex')) + 1 });
                this.element.insert({ before: this.ghost });
                vo = this.ghost.viewportOffset();
                this.ghostOffset = [ vo[0] - oleft, vo[1] - otop ];
            }

            xy[0] -= this.ghostOffset[0];
            xy[1] -= this.ghostOffset[1];

            switch (this.options.constraint) {
            case 'horizontal':
                xy[1] = this.ghost.offsetTop;
                break;

            case 'vertical':
                xy[0] = this.ghost.offsetLeft;
                break;
            }

            if (this.options.snap) {
                xy = this.options.snap(xy[0], xy[1], this.element);
            }

            if (this.options.offset) {
                xy[0] += this.options.offset.x;
                xy[1] += this.options.offset.y;
            }

            this._setContents(this.ghost, xy[0], xy[1]);
        }

        this._onMoveDrag(xy, e);

        if (Object.isFunction(this.options.onDrag)) {
            this.options.onDrag(this, e);
        }

        this.wasDragged = true;

        if (this.options.scroll) {
            this._onMoveScroll();
        }
    },

    _mouseUp: function(e)
    {
        var d = DragDrop.Drops.drop;

        this._stopScrolling();

        if (this.ghost) {
            this.ghost.remove();
            this.ghost = null;
        }
        DragDrop.Drags.div.hide();

        if (DragDrop.validDrop(this.element) &&
            Object.isFunction(d.options.onDrop)) {
            d.options.onDrop(d.element, this.element, e);
        }

        DragDrop.Drags.deactivate();

        if (Object.isFunction(this.options.onEnd)) {
            this.options.onEnd(this, e);
        }
    },

    _onMoveDrag: function(xy, e)
    {
        var c_opt, caption, cname, d_cap,
            d = DragDrop.Drops.drop,
            div = DragDrop.Drags.div,
            d_update = true;

        if (d && DragDrop.validDrop(this.element)) {
            d_cap = d.options.caption;
            if (d_cap) {
                caption = Object.isFunction(d_cap) ? d_cap(d.element, this.element, e) : d_cap;
                if (caption && d.options.hoverclass) {
                    cname = d.options.hoverclass;
                }
            } else {
                d_update = false;
            }
        }

        if (d_update) {
            if (!caption) {
                c_opt = this.options.caption;
                caption = Object.isFunction(c_opt) ? c_opt(this.element) : c_opt;
            }
            if (caption != this.lastcaption) {
                this.lastcaption = caption;
                div.update(caption).writeAttribute({ className: cname || this.options.classname });
                if (caption.empty()) {
                    div.hide();
                }
            }
        }

        if (!this.lastcaption.empty()) {
            this._setContents(div, xy[0] + 15, xy[1] + (this.ghost ? (this.ghost.getHeight() + 5) : 5));
        }
    },

    _onMoveScroll: function()
    {
        this._stopScrolling();

        var delta, p, speed,
            s = this.options.scroll,
            dim = s.getDimensions();

        // No need to scroll if element is not current scrolling.
        if (s.scrollHeight == dim.height) {
            return;
        }

        delta = document.viewport.getScrollOffsets();
        p = s.viewportOffset(),
        speed = [ 0, 0 ];

        p[0] += s.scrollLeft + delta.left;
        p[2] = p[0] + dim.width;

        // Only scroll if directly above/below element
        if (this.lastCoord[0] > p[2] ||
            this.lastCoord[0] < p[0]) {
            return;
        }

        p[1] += s.scrollTop + delta.top;
        p[3] = p[1] + dim.height;

        // Left scroll
        //if (this.lastCoord[0] < p[0]) {
        //    speed[0] = this.lastCoord[0] - p[0];
        //}
        // Top scroll
        if (this.lastCoord[1] < p[1]) {
            speed[1] = this.lastCoord[1] - p[1];
        }
        // Scroll right
        //if (this.lastCoord[0] > p[2]) {
        //    speed[0] = this.lastCoord[0] - p[2];
        //}
        // Scroll left
        if (this.lastCoord[1] > p[3]) {
            speed[1] = this.lastCoord[1] - p[3];
        }

        if (speed[0] || speed[1]) {
            this.lastScrolled = new Date();
            this.scrollInterval = setInterval(this._scroll.bind(this, speed[0] * 15, speed[1] * 15), 10);
        }
    },

    _stopScrolling: function()
    {
        if (this.scrollInterval) {
            clearInterval(this.scrollInterval);
            this.scrollInterval = null;
        }
    },

    _scroll: function(x, y)
    {
        var current = new Date(),
            delta = current - this.lastScrolled,
            s = this.options.scroll;
        this.lastScrolled = current;

        //s.scrollLeft += x * delta / 1000;
        s.scrollTop += y * delta / 1000;
    },

    _setContents: function(elt, x, y)
    {
        var d_pos = document.viewport.getDimensions(),
            e_pos = elt.getDimensions();

        if ((x + e_pos.width > d_pos.width) ||
            (y + e_pos.height > d_pos.height)) {
            elt.hide();
        } else {
            elt.setStyle({ left: x + 'px', top: y + 'px' }).show();
        }
    }

}),

Drop = Class.create({

    initialize: function(el)
    {
        this.element = $(el);
        this.options = Object.extend({
            accept: [],
            caption: '',
            hoverclass: '',
            onDrop: null,
            onOut: null,
            onOver: null
        }, arguments[1] || {});
        this.mouseoverE = this._mouseOver.bindAsEventListener(this);
        this.mouseoutE = this._mouseOut.bindAsEventListener(this);
        this.element.observe('mouseover', this.mouseoverE);
        this.element.observe('mouseout', this.mouseoutE);
        DragDrop.Drops.register(this);
    },

    destroy: function()
    {
        this.element.stopObserving('mouseover', this.mouseoverE);
        this.element.stopObserving('mouseout', this.mouseoutE);
        DragDrop.Drops.unregister(this);
    },

    _mouseOver: function(e)
    {
        if (DragDrop.Drags.drag) {
            DragDrop.Drops.drop = this;
            if (Object.isFunction(this.options.onOver)) {
                this.options.onOver(this.element, DragDrop.Drags.drag);
            }
        }
    },

    _mouseOut: function(e)
    {
        if (Object.isFunction(this.options.onOut)) {
            this.options.onOut(this.element, DragDrop.Drags.drag);
        }
        DragDrop.Drops.drop = null;
    }
});
