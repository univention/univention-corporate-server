/**
 * ColorPicker object
 *
 * Original Sphere Plugin v0.1, Design/Programming by Ulyses, (c) 2007
 * ColorJack.com, IE fixes by Hamish.
 *
 * Rewritten to utilize Prototype for Horde by Chuck Hagenbuch,
 * chuck@horde.org.
 */

var ColorPicker = Class.create();
ColorPicker.prototype = {

    initialize: function(options)
    {
        this.options = Object.extend({
            color: 'ffffff',
            update: [],
            draggable: false,
            resizable: false,
            offsetParent: null,
            offset: 10
        }, options || {})

        this.stop = 1;
        this.zIndex = 1000;
        this.hsv = Color.hex2hsv(this.options.color);

        var div = $('color-picker');
        if (!div) {
            div = document.createElement('DIV');
            div.id = 'color-picker';
            div.style.display = 'none';
            div.innerHTML = '<div class="north"><span id="color-picker-hex"></span><div id="color-picker-close">X</div></div>'
                + '<div class="south" id="color-picker-sphere" style="height:128px; width:128px;">'
                + '<div id="color-picker-cursor"></div>'
                + '<img id="color-picker-palette" src="" onmousedown="return false;" ondrag="return false;" onselectstart="return false;" />'
                + '<img id="color-picker-resize" src="" ondrag="return false;" onselectstart="return false;" />'
                + '</div>';
            document.body.appendChild(div);
        }

        div.style.position = 'absolute';
        var xy;
        if (this.options.offsetParent) {
            xy = Position.cumulativeOffset(this.options.offsetParent);
        } else {
            xy = [0, 0];
        }
        div.style.left = xy[0] + this.options.offset + 'px';
        div.style.top = xy[1] + this.options.offset + 'px';
        div.style.display = '';

        if (!this.iefix && Prototype.Browser.IE) {
            new Insertion.After('color-picker',
                                '<iframe id="color-picker-iefix" '+
                                'style="display:none;position:absolute;filter:progid:DXImageTransform.Microsoft.Alpha(opacity=0);" ' +
                                'src="javascript:false;" frameborder="0" scrolling="no"></iframe>');
            this.iefix = $('color-picker-iefix');
        }
        if (this.iefix) {
            setTimeout(this.fixIEOverlapping.bind(this), 50);
        }

        if (this.options.draggable) {
            $('color-picker').style.cursor = 'move';
        }

        // Init based on passed-in color.
        $('color-picker-hex').innerHTML = this.options.color;
        // @TODO set cursor to correct initial pos instead.
        $('color-picker-cursor').style.visibility = 'hidden';

        // Find image path.
        var path = $('color-picker-cursor').getStyle('backgroundImage').replace(/url\("?(.*?)"?\)/, '$1').replace('color-picker-cursor.gif', '');
        $('color-picker-palette').src = path.replace($('color-picker-palette').src, '') + 'color-picker-palette.png';

        if (this.options.resizable) {
            $('color-picker-resize').src = path.replace($('color-picker-palette').src, '') + 'color-picker-resize.gif';
        } else {
            $('color-picker-resize').hide();
        }

        this.addEvents();
        $('color-picker').show();
    },

    fixIEOverlapping: function()
    {
        Position.clone('color-picker', this.iefix, { setTop : (!$('color-picker').style.height) });
        this.iefix.style.zIndex = $('color-picker').getStyle('zIndex') - 1;
        this.iefix.show();
    },

    hide: function()
    {
        this.removeEvents();
        $('color-picker').hide();
        if (this.iefix) {
            this.iefix.hide();
        }
    },

    addEvents: function()
    {
        if (this.listeners) {
            return;
        }

        this.listeners = [
            ['color-picker-close', 'click', this.hide.bindAsEventListener(this)],
            ['color-picker-sphere', 'mousedown', this.coreXY.bindAsEventListener(this, 'color-picker-cursor')]
        ];

        if (this.options.draggable) {
            this.listeners.push(['color-picker', 'mousedown', this.coreXY.bindAsEventListener(this, 'color-picker')]);
        }

        if (this.options.resizable) {
            this.listeners.push(['color-picker-resize', 'mousedown', this.coreXY.bindAsEventListener(this, 'color-picker-resize')]);
        }

        for (var i = 0, i_max = this.listeners.length; i < i_max; ++i) {
            var l = this.listeners[i];
            Event.observe(l[0], l[1], l[2]);
        }
    },

    removeEvents: function()
    {
        if (this.listeners) {
            for (var i = 0, i_max = this.listeners.length; i < i_max; ++i) {
                var l = this.listeners[i];
                Event.stopObserving(l[0], l[1], l[2]);
            }
        }

        this.listeners = null;
    },

    coords: function(W)
    {
        var W2 = W / 2,
            rad = (this.hsv[0] / 360) * (Math.PI * 2),
            hyp = (this.hsv[1] + (100 - this.hsv[2])) / 100 * (W2 / 2);
        $('color-picker-cursor').setStyle({
            left: Math.round(Math.abs(Math.round(Math.sin(rad) * hyp) + W2 + 3)) + 'px',
            top: Math.round(Math.abs(Math.round(Math.cos(rad) * hyp) - W2 - 21)) + 'px'
        });
    },

    point: function(o, a, b, e, oH)
    {
        this.commit(o, [Event.pointerX(e) + a, Event.pointerY(e) + b], oH);
    },

    commit: function(o, v, oH)
    {
        if (o == 'color-picker-cursor') {
            var W = parseInt($('color-picker-sphere').getStyle('width')),
                W2 = W / 2,
                W3 = W2 / 2,
                x = v[0] - W2 - 3,
                y = W - v[1] - W2 + 21,
                SV = Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2)),
                hue = Math.atan2(x, y) / (Math.PI * 2);

            this.hsv = [
                hue > 0 ? (hue * 360) : ((hue * 360) + 360),
                SV < W3 ? (SV / W3) * 100 : 100,
                SV >= W3 ? Math.max(0, 1 - ((SV - W3) / (W2 - W3))) * 100 : 100
            ];

            var c = Color.hsv2hex(this.hsv);
            var brightness = Color.brightness(Color.hsv2rgb(this.hsv));

            $('color-picker-hex').innerHTML = c;

            for (var i = 0, i_max = this.options.update.length; i < i_max; ++i) {
                var u = this.options.update[i];
                switch (u[1]) {
                case 'background':
                    $(u[0]).setStyle({ backgroundColor: '#' + c }, true);
                    $(u[0]).setStyle({ color: brightness < 125 ? '#fff' : '#000' }, true);
                    break;

                case 'value':
                    $(u[0]).value = '#' + c;
                    break;
                }
            }

            this.coords(W);
        } else if (o == 'color-picker-resize') {
            var b = Math.max(Math.max(v[0], v[1]) + oH, 75);
            this.coords(b);

            $('color-picker').setStyle({ height: (b + 28) + 'px', width: (b + 20) + 'px' });
            $('color-picker-sphere').setStyle({ height: b + 'px', width: b + 'px' });
        } else {
            $(o).setStyle({ left: v[0] + 'px', top: v[1] + 'px' });
        }
    },

    coreXY: function(e, o)
    {
        if (!this.stop) {
            return;
        }

        // @TODO remove when we can set the initial cursor pos.
        $('color-picker-cursor').style.visibility = 'visible';

        this.stop = '';
        $(o).setStyle({zIndex: this.zIndex++}, true);

        if (o == 'color-picker-cursor') {
            var ab = Position.cumulativeOffset($(o).parentNode);
            this.point(o, -(ab[0] - 5), -(ab[1] - 28), e);
        }

        var oX, oY, oH;
        if (o == 'color-picker-resize') {
            oX = -(Event.pointerX(e)),
            oY = -(Event.pointerY(e)),
            oH = parseInt($('color-picker-sphere').getStyle('height'));
        } else {
            oX = parseInt($(o).getStyle('left')) - Event.pointerX(e),
            oY = parseInt($(o).getStyle('top')) - Event.pointerY(e),
            oH = null;
        }

        document.onmousemove = function(e, o, oX, oY, oH) {
            if (!this.stop) {
                this.point(o, oX, oY, e, oH);
            }
        }.bindAsEventListener(this, o, oX, oY, oH);
        document.onmouseup = function() {
            this.stop = 1;
            document.onmousemove = '';
            document.onmouseup = '';
        }.bind(this);
    }

}

/**
 * Color utility class
 */
var Color = {

    hsv2hex: function(h)
    {
        return Color.rgb2hex(Color.hsv2rgb(h));
    },

    hex2hsv: function(h)
    {
        return Color.rgb2hsv(Color.hex2rgb(h));
    },

    hex2rgb: function(hex)
    {
        if (hex.substring(0, 1) == '#') {
            hex = hex.substring(1);
        }
        return [
            parseInt(hex.substring(0, 2), 16),
            parseInt(hex.substring(2, 4), 16),
            parseInt(hex.substring(4, 6), 16)
        ];
    },

    rgb2hex: function(rgb) {
        var r = rgb[0].toString(16), g = rgb[1].toString(16), b = rgb[2].toString(16);
        return (r.length == 2 ? r : '0' + r) + (g.length == 2 ? g : '0' + g) + (b.length == 2 ? b : '0' + b);
    },

    /**
     * http://easyrgb.com/math.php?MATH=M21#text21
     */
    hsv2rgb: function(r)
    {
        var F, A, C, R, B, G, S = r[1] / 100, V = r[2] / 100, H = r[0] / 360;

        if (S > 0) {
            if (H >= 1) {
                H = 0;
            }

            H = 6 * H;
            F = H - Math.floor(H);
            A = Math.round(255 * V * (1.0 - S));
            B = Math.round(255 * V * (1.0 - (S * F)));
            C = Math.round(255 * V * (1.0 - (S * (1.0 - F))));
            V = Math.round(255 * V);

            switch (Math.floor(H)) {
            case 0: R = V; G = C; B = A; break;
            case 1: R = B; G = V; B = A; break;
            case 2: R = A; G = V; B = C; break;
            case 3: R = A; G = B; B = V; break;
            case 4: R = C; G = A; B = V; break;
            case 5: R = V; G = A; B = B; break;
            }

            return [R ? R : 0, G ? G : 0, B ? B : 0];
        } else {
            return [(V = Math.round(V * 255)), V, V];
        }
    },

    /**
     * http://easyrgb.com/math.php?MATH=M20#text20
     */
    rgb2hsv: function(r)
    {
        var R = r[0] / 255;
        var G = r[1] / 255;
        var B = r[2] / 255;

        var var_Min = Math.min(R, G, B);
        var var_Max = Math.max(R, G, B);
        var del_Max = var_Max - var_Min;

        var V = var_Max;

        var H, S;
        if (del_Max == 0) {
            H = 0;
            S = 0;
        } else {
            S = del_Max / var_Max;

            var del_R = (((var_Max - R) / 6 ) + (del_Max / 2)) / del_Max;
            var del_G = (((var_Max - G) / 6 ) + (del_Max / 2)) / del_Max;
            var del_B = (((var_Max - B) / 6 ) + (del_Max / 2)) / del_Max;

            if (R == var_Max) {
                H = del_B - del_G;
            } else if (G == var_Max) {
                H = (1 / 3) + del_R - del_B;
            } else if (B == var_Max) {
                H = (2 / 3) + del_G - del_R;
            }

            if (H < 0) {
                H += 1;
            } else if (H > 1) {
                H -= 1;
            }
        }

        return [H * 100, S * 100, V * 100];
    },

    brightness: function(rgb)
    {
        return Math.round((rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000);
    }

}
