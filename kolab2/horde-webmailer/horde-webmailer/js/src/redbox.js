/**
 * Redbox.js
 *
 * $Horde: horde/js/src/redbox.js,v 1.7.2.4 2008-02-06 10:08:37 slusarz Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var RedBox = {

    overlay: true,
    onDisplay: null,

    showInline: function(id)
    {
        this.appearWindow();
        this.cloneWindowContents(id);
    },

    showHtml: function(html)
    {
        this.appearWindow();
        this.htmlWindowContents(html);
    },

    appearWindow: function()
    {
        var loading = $('RB_loading');
        if (loading && loading.visible()) {
            loading.hide();
        } else {
            this.showOverlay();
        }
        var opts = { duration: 0.4, queue: 'end' },
            w = $('RB_window');
        if (this.onDisplay) {
            opts.afterFinish = this.onDisplay;
        }
        new Effect.Appear(w, opts);
        w.scrollTo();
    },

    loading: function()
    {
        this.showOverlay();
        var rl = $('RB_loading');
        if (rl) {
            rl.show();
        }
        this.setWindowPosition();
    },

    close: function()
    {
        new Effect.Fade('RB_window', { duration: 0.4 });
        if (this.overlay) {
            new Effect.Fade('RB_overlay', { duration: 0.4 });
        }
    },

    showOverlay: function()
    {
        var rb = $('RB_redbox');
        if (!rb) {
            rb = new Element('DIV', { id: 'RB_redbox', align: 'center' });
            $(document.body).insert(rb);

            var ov = new Element('DIV', { id: 'RB_overlay' }).hide();
            rb.insert({ top: new Element('DIV', { id: 'RB_window' }).hide() }).insert({ top: ov });

            if (this.overlay) {
                ov.insert({ top: new Element('DIV', { id: 'RB_loading' }).hide() });
            }
        }

        if (this.overlay) {
            this.setOverlaySize();
            new Effect.Appear('RB_overlay', { duration: 0.4, to: 0.6, queue: 'end' });
        }
    },

    setOverlaySize: function()
    {
        if (window.innerHeight && window.scrollMaxY) {
            yScroll = window.innerHeight + window.scrollMaxY;
        } else if (document.body.scrollHeight > document.body.offsetHeight) {
            // all but Explorer Mac
            yScroll = document.body.scrollHeight;
        } else {
            // Explorer Mac...would also work in Explorer 6 Strict, Mozilla
            // and Safari
            yScroll = document.body.offsetHeight;
        }
        Element.setStyle('RB_overlay', { height: yScroll + 'px' });
    },

    setWindowPosition: function()
    {
        var win = $('RB_window');
        var d = win.getDimensions(),
            v = document.viewport.getDimensions();
        win.setStyle({ width: 'auto', height: 'auto', left: ((v.width - d.width) / 2) + 'px', top: ((v.height - d.height) / 2) + 'px' });
    },

    cloneWindowContents: function(id)
    {
        $('RB_window').appendChild($($(id).cloneNode(true)).setStyle({ display: 'block' }));
        this.setWindowPosition();
    },

    htmlWindowContents: function(html)
    {
        $('RB_window').update(html);
        this.setWindowPosition();
    },

    getWindowContents: function()
    {
        var w = $('RB_window');
        return w.visible() ? w.down() : null;
    },

    overlayVisible: function()
    {
        var ov = $('RB_overlay');
        return ov && ov.visible();
    }

}
