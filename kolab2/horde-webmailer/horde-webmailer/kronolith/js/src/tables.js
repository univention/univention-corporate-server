/**
 * Javascript code for finding all tables with classname "striped" and
 * dynamically striping their row colors, and finding all tables with
 * classname "sortable" and making them dynamically sortable.
 *
 * TODO: incorporate missing features (if wanted) and improvements from:
 * http://tetlaw.id.au/view/blog/table-sorting-with-prototype/
 * http://www.millstream.com.au/view/code/tablekit/
 * http://tablesorter.com/docs/
 *
 * $Horde: kronolith/js/src/tables.js,v 1.1.2.3 2007-12-21 00:10:33 chuck Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

var SORT_COLUMN_INDEX;

function table_stripe(table)
{
    var classes = [ 'rowEven', 'rowOdd' ];

    // Tables can have more than one tbody element; get all child
    // tbody tags and interate through them.
    table.select('tbody tr').each(function(c) {
        c.removeClassName(classes[1]);
        c.addClassName(classes[0]);
        classes.reverse(true);
    });
}

function table_makeSortable(table)
{
    var i = 0;

    // We have a first row: assume it's the header, and make its
    // contents clickable links.
    table.down('tr').immediateDescendants().each(function(cell) {
        if (cell.hasClassName('nosort')) {
            ++i;
            return;
        }

        cell.setAttribute('columnIndex', i++);
        cell.setStyle({ cursor: 'pointer' });
        cell.observe('click', function(e) {
            var c = e.findElement('th');
            e.stop();
            var a = c.down('a');
            if (a && !a.hasClassName('sortlink')) {
                return true;
            }
            table_resortTable(c);
            return false;
        });
    });
}

function table_getSortValue(el)
{
    var str = '';

    if (Object.isString(el) || Object.isUndefined(el)) {
        return el;
    }

    // Use "sortval" if defined.
    el = $(el);
    if (el.readAttribute('sortval')) {
        return el.readAttribute('sortval');
    }

    if (el.innerText) {
        // Not needed but it is faster.
        return el.innerText;
    }

    $A(el.childNodes).each(function(e) {
        switch (e.nodeType) {
        case 1:
            // ELEMENT_NODE
            str += table_getSortValue(e);
            break;

        case 3:
            // TEXT_NODE
            str += e.nodeValue;
            break;
        }
    });

    return str;
}

function table_resortTable(th)
{
    var table = th.up('table'),
        th_siblings = th.up().immediateDescendants(),
        sortfn,
        sortDown = 0;

    th_siblings.each(function(e) {
        if (th == e) {
            if (e.hasClassName('sortup')) {
                e.removeClassName('sortup');
                e.addClassName('sortdown');
            } else if (e.hasClassName('sortdown')) {
                e.removeClassName('sortdown');
                e.addClassName('sortup');
                sortDown = 1;
            } else {
                e.addClassName('sortdown');
            }
        } else {
            e.removeClassName('sortup');
            e.removeClassName('sortdown');
        }
    });

    // Work out a type for the column
    if (th_siblings.size() <= 1) {
        return;
    }

    SORT_COLUMN_INDEX = th.readAttribute('columnIndex');
    var itm = table_getSortValue(table.down('tbody > tr').cells[SORT_COLUMN_INDEX]);

    if (itm.match(/^\d\d[\/-]\d\d[\/-]\d\d\d\d$/) ||
        itm.match(/^\d\d[\/-]\d\d[\/-]\d\d$/)) {
        sortfn = table_sort_date;
    } else if (itm.match(/^[£$]/)) {
        sortfn = table_sort_currency;
    } else if (itm.match(/^[\d\.]+$/)) {
        sortfn = table_sort_numeric;
    } else {
        sortfn = table_sort_caseinsensitive;
    }

    // Don't mix up seperate tbodies; sort each in turn.
    $A(table.getElementsByTagName('tbody')).each(function(tbody) {
        var bottomRows = [ ],
            newRows = $A(tbody.getElementsByTagName('tr'));

        newRows.sort(sortfn);
        if (sortDown) {
            newRows.reverse();
        }

        // We appendChild rows that already exist to the tbody, so it
        // moves them rather than creating new ones. Don't do
        // sortbottom rows.
        newRows.each(function(r) {
            if (r.hasClassName('sortbottom')) {
                bottomRows.push(r);
            } else {
                tbody.appendChild(r);
            }
        });

        // Do sortbottom rows only.
        bottomRows.each(function(r) {
            tbody.appendChild(r);
        });
    });

    // If we just resorted a striped table, re-stripe it.
    if (table.hasClassName('striped')) {
        table_stripe(table);
    }

    // Finally, see if we have a callback function to trigger.
    if (typeof table_sortCallback != 'undefined' && Object.isFunction(table_sortCallback)) {
        table_sortCallback(table.id, th.id, sortDown);
    }
}

function table_sort_date(a, b)
{
    // Two digit years less than 50 are treated as 20XX, greater than
    // 50 are treated as 19XX.
    var aa = table_getSortValue(a.cells[SORT_COLUMN_INDEX]),
        bb = table_getSortValue(b.cells[SORT_COLUMN_INDEX]),
        dt1, dt2, yr;

    if (aa.length == 10) {
        dt1 = aa.substr(6, 4) + aa.substr(3, 2) + aa.substr(0, 2);
    } else {
        yr = aa.substr(6, 2);
        if (parseInt(yr) < 50) {
            yr = '20' + yr;
        } else {
            yr = '19' + yr;
        }
        dt1 = yr + aa.substr(3, 2) + aa.substr(0, 2);
    }
    if (bb.length == 10) {
        dt2 = bb.substr(6, 4) + bb.substr(3, 2) + bb.substr(0, 2);
    } else {
        yr = bb.substr(6, 2);
        if (parseInt(yr) < 50) {
            yr = '20' + yr;
        } else {
            yr = '19' + yr;
        }
        dt2 = yr + bb.substr(3, 2) + bb.substr(0, 2);
    }
    if (dt1 == dt2) {
        return 0;
    } else if (dt1 < dt2) {
        return -1;
    }
    return 1;
}

function table_sort_currency(a, b)
{
    var aa = table_getSortValue(a.cells[SORT_COLUMN_INDEX]).replace(/[^0-9.]/g, ''),
        bb = table_getSortValue(b.cells[SORT_COLUMN_INDEX]).replace(/[^0-9.]/g, '');
    return parseFloat(aa) - parseFloat(bb);
}

function table_sort_numeric(a, b)
{
    var aa = parseFloat(table_getSortValue(a.cells[SORT_COLUMN_INDEX]));
    if (isNaN(aa)) {
        aa = 0;
    }
    var bb = parseFloat(table_getSortValue(b.cells[SORT_COLUMN_INDEX]));
    if (isNaN(bb)) {
        bb = 0;
    }
    return aa - bb;
}

function table_sort_caseinsensitive(a, b)
{
    var aa = table_getSortValue(a.cells[SORT_COLUMN_INDEX]).toLowerCase(),
        bb = table_getSortValue(b.cells[SORT_COLUMN_INDEX]).toLowerCase();
    if (aa == bb) {
        return 0;
    } else if (aa < bb) {
        return -1;
    }
    return 1;
}

function table_sort_default(a, b)
{
    var aa = table_getSortValue(a.cells[SORT_COLUMN_INDEX]),
        bb = table_getSortValue(b.cells[SORT_COLUMN_INDEX]);
    if (aa == bb) {
        return 0;
    } else if (aa < bb) {
        return -1;
    }
    return 1;
}

/* We do everything onload so that the entire document is present
 * before we start searching it for tables. */
document.observe('dom:loaded', function() {
    $$('table.striped').each(table_stripe);
    $$('table.sortable').each(table_makeSortable);
});
