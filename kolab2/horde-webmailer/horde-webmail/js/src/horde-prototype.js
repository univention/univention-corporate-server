/**
 * General Horde UI effects javascript.
 *
 * $Horde: horde/js/src/horde-prototype.js,v 1.10.2.2 2008-03-25 16:10:56 jan Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

var ToolTips = {
    // Vars used and defaulting to null: current, element, timeout

    attachBehavior: function()
    {
        $$('a').each(function(a) {
            this.attach(a);
        }.bind(this));
    },

    attach: function(e)
    {
        var t = e.getAttribute('title');
        if (!t) {
            return;
        }
        e.setAttribute('nicetitle', t);
        e.removeAttribute('title');
        Event.observe(e, 'mouseover', this.onMouseover.bindAsEventListener(this));
        Event.observe(e, 'mouseout', this.out.bind(this));
        Event.observe(e, 'focus', this.onFocus.bindAsEventListener(this));
        Event.observe(e, 'blur', this.out.bind(this));
    },

    onMouseover: function(e)
    {
        this.onOver(e, [ Event.pointerX(e), Event.pointerY(e) ]);
    },

    onFocus: function(e)
    {
        this.onOver(e, Position.cumulativeOffset(Event.element(e)));
    },

    onOver: function(e, p)
    {
        if (this.timeout) {
            clearTimeout(this.timeout);
        }

        this.element = Event.element(e);
        this.timeout = setTimeout(function() { this.show(p); }.bind(this), 300)
    },

    out: function()
    {
        if (this.timeout) {
            clearTimeout(this.timeout);
        }

        if (this.current) {
            this.current.remove();
            this.current = null;

            var iframe = $('iframe_tt');
            if (iframe) {
                iframe.hide();
            }
        }
    },

    show: function(pos)
    {
        try {
            if (this.current) {
                this.out();
            }

            var link = this.element;
            while (!link.getAttribute('nicetitle') &&
                   link.nodeName.toLowerCase() != 'body') {
                link = link.parentNode;
            }
            var nicetitle = link.getAttribute('nicetitle');
            if (!nicetitle) {
                return;
            }

            var d = $(document.createElement('DIV'));
            d.id = 'toolTip';
            d.addClassName('nicetitle');
            d.update(nicetitle);

            var STD_WIDTH = 100, MAX_WIDTH = 600;
            if (window.innerWidth) {
                MAX_WIDTH = Math.min(MAX_WIDTH, window.innerWidth - 20);
            }
            if (document.body && document.body.scrollWidth) {
                MAX_WIDTH = Math.min(MAX_WIDTH, document.body.scrollWidth - 20);
            }

            var nicetitle_length = 0;
            nicetitle.replace(/<br ?\/>/g, "\n").split("\n").each(function(l) {
                nicetitle_length = Math.max(nicetitle_length, l.stripTags().length);
            });

            var h_pixels = nicetitle_length * 7,
                t_pixels = nicetitle_length * 10,
                w;

            if (h_pixels > STD_WIDTH) {
                w = h_pixels;
            } else if (STD_WIDTH > t_pixels) {
                w = t_pixels;
            } else {
                w = STD_WIDTH;
            }

            // Make sure all of the tooltip is visible
            var left = pos[0] + 20,
                innerWidth = window.innerWidth || document.documentElement.clientWidth || document.body.offsetWidth,
                pageXOffset = window.pageXOffset || document.documentElement.scrollLeft;
            if (innerWidth && ((left + w) > (innerWidth + pageXOffset))) {
                left = innerWidth - w - 40 + pageXOffset;
            }
            if (document.body.scrollWidth && ((left + w) > (document.body.scrollWidth + pageXOffset))) {
                left = document.body.scrollWidth - w - 25 + pageXOffset;
            }

            d.setStyle({ left: Math.max(left, 5) + 'px',
                         width: Math.min(w, MAX_WIDTH) + 'px',
                         top: (pos[1] + 10) + 'px' });
            d.show();
            document.body.appendChild(d);

            this.current = d;

            if (typeof ToolTips_Option_Windowed_Controls != 'undefined') {
                var iframe = $('iframe_tt');
                if (!iframe) {
                    iframe = $(document.createElement('IFRAME'));
                    iframe.src = 'javascript:false;';
                    iframe.name = iframe.id = 'iframe_tt';
                    iframe.setAttribute('scrolling', 'no');
                    iframe.setAttribute('frameborder', 0);
                    iframe.hide();
                    document.body.appendChild(iframe);
                }
                iframe.setStyle({ width: d.offsetWidth,
                                  height: d.offsetHeight,
                                  top: d.style.top,
                                  left: d.style.left,
                                  position: 'absolute',
                                  display: 'block',
                                  zIndex: 99 });
                d.setStyle({ zIndex: 100 });
            }
        } catch (e) {}
    }

};

Event.observe(window, 'load', ToolTips.attachBehavior.bind(ToolTips));
Event.observe(window, 'unload', ToolTips.out.bind(ToolTips));
