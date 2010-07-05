/**
 * General Horde UI effects javascript.
 *
 * $Horde: horde/js/src/horde.js,v 1.10.2.1 2007-12-20 15:01:30 jan Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

var ToolTips = {
    current: null,
    timeout: null,
    element: null,

    attachBehavior: function()
    {
        links = document.getElementsByTagName('a');
        for (var i = 0; i < links.length; i++) {
            if (links[i].title) {
                links[i].setAttribute('nicetitle', links[i].title);
                links[i].removeAttribute('title');

                addEvent(links[i], 'mouseover', ToolTips.onMouseover);
                addEvent(links[i], 'mouseout', ToolTips.out);
                addEvent(links[i], 'focus', ToolTips.onFocus);
                addEvent(links[i], 'blur', ToolTips.out);
            }
        }
    },

    onMouseover: function(event)
    {
        if (typeof ToolTips == 'undefined') {
            return;
        }

        if (ToolTips.timeout) {
            clearTimeout(ToolTips.timeout);
        }

        if (event.srcElement) {
            ToolTips.element = event.srcElement;
        } else if (event.target) {
            ToolTips.element = event.target;
        }

        var pos = mousePos(event);
        ToolTips.timeout = setTimeout(function() { ToolTips.show(pos); }, 300)
    },

    onFocus: function(event)
    {
        if (typeof ToolTips == 'undefined') {
            return;
        }

        if (ToolTips.timeout) {
            clearTimeout(ToolTips.timeout);
        }

        if (event.srcElement) {
            ToolTips.element = event.srcElement;
        } else if (event.target) {
            ToolTips.element = event.target;
        }

        var pos = eltPos(ToolTips.element);
        ToolTips.timeout = setTimeout(function() { ToolTips.show(pos); }, 300)
    },

    out: function()
    {
        if (typeof ToolTips == 'undefined') {
            return;
        }

        if (ToolTips.timeout) {
            clearTimeout(ToolTips.timeout);
        }

        if (ToolTips.current) {
            document.getElementsByTagName('body')[0].removeChild(ToolTips.current);
            ToolTips.current = null;

            var iframe = document.getElementById('iframe_tt');
            if (iframe != null) {
                iframe.style.display = 'none';
            }
        }
    },

    show: function(pos)
    {
        try {
            if (ToolTips.current) {
                ToolTips.out();
            }

            var link = ToolTips.element;
            while (!link.getAttribute('nicetitle') && link.nodeName.toLowerCase() != 'body') {
                link = link.parentNode;
            }
            var nicetitle = link.getAttribute('nicetitle');
            if (!nicetitle) {
                return;
            }

            var d = document.createElement('div');
            d.className = 'nicetitle';
            d.innerHTML = nicetitle;

            var STD_WIDTH = 100;
            var MAX_WIDTH = 600;
            if (window.innerWidth) {
                MAX_WIDTH = Math.min(MAX_WIDTH, window.innerWidth - 20);
            }
            if (document.body && document.body.scrollWidth) {
                MAX_WIDTH = Math.min(MAX_WIDTH, document.body.scrollWidth - 20);
            }

            var nicetitle_length = 0;
            var lines = nicetitle.replace(/<br ?\/>/g, "\n").split("\n");
            for (var i = 0; i < lines.length; ++i) {
                nicetitle_length = Math.max(nicetitle_length, lines[i].length);
            }

            var h_pixels = nicetitle_length * 7;
            var t_pixels = nicetitle_length * 10;

            var w;
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

            d.id = 'toolTip';
            d.style.left = left + 'px';
            d.style.width = Math.min(w, MAX_WIDTH) + 'px';
            d.style.top = (pos[1] + 10) + 'px';
            d.style.display = '';

            document.getElementsByTagName('body')[0].appendChild(d);
            ToolTips.current = d;

            if (typeof ToolTips_Option_Windowed_Controls != 'undefined') {
                var iframe = document.getElementById('iframe_tt');
                if (iframe == null) {
                    iframe = document.createElement('<iframe src="javascript:false;" name="iframe_tt" id="iframe_tt" scrolling="no" frameborder="0" style="position:absolute;top:0;left:0;display:none"></iframe>');
                    document.getElementsByTagName('body')[0].appendChild(iframe);
                }
                iframe.style.width = d.offsetWidth;
                iframe.style.height = d.offsetHeight;
                iframe.style.top = d.style.top;
                iframe.style.left = d.style.left;
                iframe.style.position = 'absolute';
                iframe.style.display = 'block';
                d.style.zIndex = 100;
                iframe.style.zIndex = 99;
            }
        } catch (e) {}
    }

};

/**
 * Return the [x,y] position of the mouse.
 */
function mousePos(event)
{
    return [event.pageX || (event.clientX + (document.documentElement.scrollLeft || document.body.scrollLeft)),
            event.pageY || (event.clientY + (document.documentElement.scrollTop || document.body.scrollTop))];
}
/**
 * Return the [x,y] position of an element.
 */
function eltPos(elt)
{
    if (elt.offsetParent) {
        for (posX = 0, posY = 0; elt.offsetParent; elt = elt.offsetParent) {
            posX += elt.offsetLeft;
            posY += elt.offsetTop;
        }
        return [posX, posY];
    } else {
        return [elt.x, elt.y];
    }
}

/**
 * Add an event listener as long as the browser supports it. Different
 * browsers still handle these events slightly differently; in
 * particular avoid using "this" in event functions.
 *
 * @author Scott Andrew
 * @author Chuck Hagenbuch <chuck@horde.org>
 */
function addEvent(obj, evType, fn)
{
    if (obj.addEventListener) {
        obj.addEventListener(evType, fn, true);
        return true;
    } else if (obj.attachEvent) {
        var r = obj.attachEvent('on' + evType, fn);
        EventCache.add(obj, evType, fn);
        return r;
    } else {
        return false;
    }
}

var EventCache = function()
{
    var listEvents = [];

    return {
        listEvents: listEvents,

        add: function(node, sEventName, fHandler, bCapture)
        {
            listEvents.push(arguments);
        },

        flush: function()
        {
            var i, item;
            for (i = listEvents.length - 1; i >= 0; i = i - 1) {
                item = listEvents[i];

                if (item[0].removeEventListener) {
                    item[0].removeEventListener(item[1], item[2], item[3]);
                };

                /* From this point on we need the event names to be
                 * prefixed with 'on'. */
                if (item[1].substring(0, 2) != 'on') {
                    item[1] = 'on' + item[1];
                }

                if (item[0].detachEvent) {
                    item[0].detachEvent(item[1], item[2]);
                }

                item[0][item[1]] = null;
            }
        }
    };
}();

if (document.createElement && document.getElementsByTagName) {
    addEvent(window, 'load', ToolTips.attachBehavior);
    addEvent(window, 'unload', ToolTips.out);
    addEvent(window, 'unload', EventCache.flush);
}
