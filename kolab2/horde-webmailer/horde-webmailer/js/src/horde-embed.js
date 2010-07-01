var Horde_ToolTips = {
    attachBehavior: function(args)
    {
        var container = args;
        $(container).select('a').each(function(a) {
            Horde_ToolTips.attach(a);
        }.bind(Horde_ToolTips));
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
            d.id = 'horde_toolTip';
            d.addClassName('horde_nicetitle');
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

        } catch (e) {}
    }

};