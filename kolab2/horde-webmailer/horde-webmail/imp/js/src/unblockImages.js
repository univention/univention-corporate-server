/**
 * $Horde: imp/js/src/unblockImages.js,v 1.7.2.2 2008-08-05 17:51:12 slusarz Exp $
 *
 * Use DOM manipulation to un-block images that had been redirected.
 */

var IMP = window.IMP || {};

IMP.unblockImages = function(parent, message)
{
    var tmp;

    if (!parent) {
        return true;
    }

    $(parent).select('[blocked]').each(function(elt) {
        var src = decodeURIComponent(elt.readAttribute('blocked'));
        if (elt.hasAttribute('src')) {
            elt.writeAttribute('src', src);
        } else if (elt.hasAttribute('background')) {
            elt.writeAttribute('background', src);
        } else if (elt.style.backgroundImage) {
            elt.setStyle({ backgroundImage: 'url(' + src + ')' });
        }
    });

    message = $(message);
    if (message) {
        tmp = message.up();
        message.remove();
        if (!tmp.childElements().size()) {
            tmp = tmp.up('TABLE.mimeStatusMessage');
            if (tmp) {
                tmp.remove();
            }
        }
    }

    // On success return false to stop event propagation.
    return false;
};
