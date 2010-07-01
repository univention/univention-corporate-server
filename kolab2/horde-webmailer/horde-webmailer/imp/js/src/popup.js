/**
 * IMP Popup JavaScript.
 *
 * Provides the javascript to open popup windows.
 * This file should be included via Horde::addScriptFile().
 * Requires prototypejs 1.6.0.2+
 *
 * $Horde: imp/js/src/popup.js,v 1.2.2.7 2008-06-27 21:07:37 slusarz Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

/**
 * Open a popup window.
 *
 * @param string $url      The URL to open in the popup window.
 * @param integer $width   The width of the popup window. (Default: 600 px)
 * @param integer $height  The height of the popup window. (Default: 500 px)
 * @param string $args     Any additional args to pass to the script.
 *                         (Default: no args)
 */
function popup_imp(url, width, height, args)
{
    var q, win,
        params = $H(),
        name = new Date().getTime();

    height = Math.min(screen.height - 75, height || 500);
    width = Math.min(screen.width - 75, width || 600);

    q = url.indexOf('?');
    if (q != -1) {
        params = $H(url.toQueryParams());
        url = url.substring(0, q);
    }

    if (args) {
        $H(args.toQueryParams()).each(function(a) {
            params.set(a.key, unescape(a.value));
        });
    }
    params.set('uniq', name);

    win = window.open(url + '?' + params.toQueryString(), name, 'toolbar=no,location=no,status=yes,scrollbars=yes,resizable=yes,width=' + width + ',height=' + height + ',left=0,top=0');
    if (!win) {
        alert(IMP.text.popup_block);
    } else {
        if (Object.isUndefined(win.name)) {
            win.name = name;
        }
        if (Object.isUndefined(win.opener)) {
            win.opener = self;
        }
        win.focus();
    }
}
