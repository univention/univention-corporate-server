/**
 * Javascript code for finding all tables with classname "striped" and
 * dynamically striping their row colors.
 *
 * $Horde: horde/js/src/stripe.js,v 1.3.2.1 2007-12-20 15:01:31 jan Exp $
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Matt Warden <mwarden@gmail.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/* We do everything onload so that the entire document is present
 * before we start searching it for tables. */
if (window.addEventListener) {
    window.addEventListener('load', findStripedElements, false);
} else if (window.attachEvent) {
    window.attachEvent('onload', findStripedElements);
} else if (window.onload != null) {
    var oldOnLoad = window.onload;
    window.onload = function(e)
    {
        oldOnLoad(e);
        findStripedElements();
    };
} else {
    window.onload = findStripedElements;
}

function findStripedElements()
{
    if (!document.getElementsByTagName) {
        return;
    }
    var elts = document.getElementsByTagName('*');
    for (var i = 0; i < elts.length; ++i) {
        var e = elts[i];
        if (e.className.indexOf('striped') != -1) {
            if (e.tagName == 'TABLE') {
                stripeTable(e);
            } else {
                stripeElement(e);
            }
        }
    }
}

function stripeTable(table)
{
    // The flag we'll use to keep track of whether the current row is
    // odd or even.
    var even = false;

    // Tables can have more than one tbody element; get all child
    // tbody tags and interate through them.
    var tbodies = table.childNodes;
    for (var c = 0; c < tbodies.length; c++) {
        if (tbodies[c].tagName == 'TBODY') {
            var trs = tbodies[c].childNodes;
            for (var i = 0; i < trs.length; i++) {
                if (trs[i].tagName == 'TR') {
                    trs[i].className = trs[i].className.replace(/ ?rowEven ?/, '').replace(/ ?rowOdd ?/, '');
                    if (trs[i].className) {
                        trs[i].className += ' ';
                    }
                    trs[i].className += even ? 'rowEven' : 'rowOdd';

                    // Flip from odd to even, or vice-versa.
                    even = !even;
                }
            }
        }
    }
}

function stripeElement(parent)
{
    // The flag we'll use to keep track of whether the current elt is
    // odd or even.
    var even = false;

    // Toggle the classname of any child node that is an element.
    var children = parent.childNodes;
    for (var i = 0; i < children.length; i++) {
        var tag = children[i];
        if (tag.nodeType && tag.nodeType == 1) {
            tag.className = tag.className.replace(/ ?rowEven ?/, '').replace(/ ?rowOdd ?/, '');
            tag.className = tag.className.split(' ').concat([even ? 'rowEven' : 'rowOdd']).join(' ');

            // Flip from odd to even, or vice-versa.
            even = !even;
        }
    }
}
