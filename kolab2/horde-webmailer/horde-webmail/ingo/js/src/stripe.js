/**
 * Javascript code for finding all tables with classname "striped" and
 * dynamically striping their row colors.
 *
 * $Horde: ingo/js/src/stripe.js,v 1.2.2.2 2008-03-06 20:50:17 chuck Exp $
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Matt Warden <mwarden@gmail.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

function stripeAllElements()
{
    $$('.striped').each(stripeElement);
}

function stripeElement(elt)
{
    var classes = [ 'rowEven', 'rowOdd' ],
        e = [];

    if (elt.tagName == 'TABLE') {
        // Tables can have more than one tbody element; get all child
        // tbody tags and interate through them.
        elt.immediateDescendants().each(stripeElement);
        return;
    } else {
        // Toggle the classname of any child node that is an element.
        e = elt.immediateDescendants();
    }

    e.each(function(c) {
        c.removeClassName(classes[1]);
        c.addClassName(classes[0]);
        classes.reverse(true);
    });
}

/* We have to wait for the full DOM to be loaded to ensure we don't
 * miss anything. */
document.observe('dom:loaded', stripeAllElements);
