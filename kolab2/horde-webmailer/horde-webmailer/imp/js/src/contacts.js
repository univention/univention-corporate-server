/**
 * Provides the javascript for the contacts.php script
 *
 * $Horde: imp/js/src/contacts.js,v 1.6.2.6 2008-08-22 15:54:25 jan Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

// The following variables are defined in contacts.php:
//   formname, to_only

function passAddresses()
{
    var sa = '';

    $('selected_addresses').childElements().each(function(s) {
        if (!s.value) {
            return;
        }
        sa += s.value + '|';
    });

    $('sa').setValue(sa);
}

function sameOption(f, item, itemj)
{
    var t = f + ": " + item.value,
        tj = itemj.value;

    return Try.these(
        function() {
            return (t == tj) || (decodeURIComponent(t) == decodeURIComponent(tj));
        },
        // Catch exception with NS 7.1
        function() {
            return (t == tj);
        }
    );
}

function addAddress(f)
{
    var s = $('search_results');

    if (!$F(s).size()) {
        alert(IMP.text.contacts_select);
        return false;
    } else {
        var d = $('selected_addresses'), l = $A(d).length, option;
        s.childElements().each(function(i) {
            if (i.value && i.selected) {
                if (!$A(d).any(function(j) {
                    return sameOption(f, i, j);
                })) {
                    option = f + ': ' + i.value;
                    d[l++] = new Option(option, option);
                }
            }
        });
    }

    return true;
}

function updateMessage()
{
    if (parent.opener.closed) {
        alert(IMP.text.contacts_closed);
        this.close();
        return;
    }

    if (!parent.opener.document[formname]) {
        alert(IMP.text.contacts_called);
        this.close();
        return;
    }

    $('selected_addresses').childElements().each(function(s) {
        var address = s.value, f, field = null, pos, v;
        pos = address.indexOf(':');
        f = address.substring(0, pos);
        address = address.substring(pos + 2, address.length)

        if (f == 'to') {
            field = parent.opener.document[formname].to;
        } else if (!to_only && f == 'cc') {
            field = parent.opener.document[formname].cc;
        } else if (!to_only && f == 'bcc') {
            field = parent.opener.document[formname].bcc;
        } else {
            return;
        }

        // Always delimit with commas.
        if (field.value.length) {
            v = field.value.replace(/, +/g, ',').split(',').findAll(function(s) { return s; });
            field.value = v.join(', ');
            if (field.value.lastIndexOf(';') != field.value.length - 1) {
                field.value += ',';
            }
            field.value += ' ' + address;
        } else {
            field.value = address;
        }
        if (address.lastIndexOf(';') != address.length - 1) {
            field.value += ', ';
        }
    });

    this.close();
}

function removeAddress()
{
    $('selected_addresses').childElements().each(function(o) {
        if (o.selected) {
            o.remove();
        }
    });
}
