/**
 * Horde sidebar javascript.
 *
 * $Horde: horde/js/src/sidebar.js,v 1.1.2.2 2008-05-19 19:37:24 slusarz Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

var HordeSidebar = {

    getCookie: function(name, deflt)
    {
        var dc = document.cookie,
            prefix = name + '=',
            begin = dc.indexOf('; ' + prefix),
            end;

        if (begin == -1) {
            begin = dc.indexOf(prefix);
            if (begin != 0) {
                return deflt;
            }
        } else {
            begin += 2;
        }

        end = dc.indexOf(';', begin);
        if (end == -1) {
            end = dc.length;
        }
        return unescape(dc.substring(begin + prefix.length, end));
    },

    toggleMenuFrame: function()
    {
        if (!parent || !parent.document.getElementById('hf')) {
            return;
        }

        var cols,
            expires = new Date(),
            rtl = horde_sidebar_rtl;
        if ($('expandedSidebar').visible()) {
            cols = rtl ? '*,20' : '20,*';
        } else {
            cols = (rtl ? '*,' : '') + horde_sidebar_cols + (rtl ? '' : ',*');
        }
        parent.document.getElementById('hf').setAttribute('cols', cols);
        $('expandedSidebar', 'hiddenSidebar').invoke('toggle');
        if ($('themelogo')) {
            $('themelogo').toggle();
        }

        // Expire in one year.
        expires.setTime(expires.getTime() + 31536000000);
        document.cookie = 'horde_sidebar_expanded=' + $('expandedSidebar').visible() + ';DOMAIN=' + horde_sidebar_domain + ';PATH=' + horde_sidebar_path + ';expires=' + expires.toGMTString();
    },

    updateSidebar: function()
    {
        new Ajax.PeriodicalUpdater(
            'horde_menu',
            horde_sidebar_url,
            { parameters: { httpclient: 1 },
              method: 'get',
              evalScripts: true,
              frequency: horde_sidebar_refresh }
        );
    }

};

Event.observe(window, 'load', function() {
    $('hiddenSidebar').hide();
    if (HordeSidebar.getCookie('horde_sidebar_expanded', true).toString() != $('expandedSidebar').visible().toString()) {
        HordeSidebar.toggleMenuFrame();
    }
    if (horde_sidebar_refresh) {
        HordeSidebar.updateSidebar.delay(horde_sidebar_refresh);
    }
});
