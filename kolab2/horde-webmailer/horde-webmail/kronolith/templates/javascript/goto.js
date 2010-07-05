var currentDate, currentYear;

function weekOfYear(d)
{
    // Adapted from http://www.merlyn.demon.co.uk/js-date7.htm#WkConv.
    var ms1d = 86400000, ms3d = 3 * ms1d, ms7d = 7 * ms1d;

    var year = d.getYear();
    if (year < 1900) {
        year += 1900;
    }
    var D3 = Date.UTC(year, d.getMonth(), d.getDate()) + ms3d;
    var wk = Math.floor(D3 / ms7d);
    with (new Date(wk * ms7d)) {
        var yy = getUTCFullYear();
    }
    return [yy, 1 + wk - Math.floor((Date.UTC(yy, 0, 4) + ms3d) / ms7d)]
}

function openKGoto(timestamp, event)
{
    var row, cell, img, link, days;

    var d = new Date(timestamp * 1000);
    currentDate = d;
    var month = d.getMonth();
    var year = d.getYear();
    if (year < 1900) {
        year += 1900;
    }
    currentYear = year;
    var firstOfMonth = new Date(year, month, 1);
    var diff = firstOfMonth.getDay() - 1;
    if (diff == -1) {
        diff = 6;
    }
    switch (month) {
    case 3:
    case 5:
    case 8:
    case 10:
        days = 30;
        break;

    case 1:
        if (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) {
            days = 29;
        } else {
            days = 28;
        }
        break;

    default:
        days = 31;
        break;
    }

    var wdays = [
        '<?php echo _("Mo") ?>',
        '<?php echo _("Tu") ?>',
        '<?php echo _("We") ?>',
        '<?php echo _("Th") ?>',
        '<?php echo _("Fr") ?>',
        '<?php echo _("Sa") ?>',
        '<?php echo _("Su") ?>'
    ];
    var months = [
        '<?php echo _("January") ?>',
        '<?php echo _("February") ?>',
        '<?php echo _("March") ?>',
        '<?php echo _("April") ?>',
        '<?php echo _("May") ?>',
        '<?php echo _("June") ?>',
        '<?php echo _("July") ?>',
        '<?php echo _("August") ?>',
        '<?php echo _("September") ?>',
        '<?php echo _("October") ?>',
        '<?php echo _("November") ?>',
        '<?php echo _("December") ?>'
    ];

    var table = document.createElement('TABLE');
    var thead = document.createElement('THEAD');
    var tbody = document.createElement('TBODY');
    table.appendChild(thead);
    table.appendChild(tbody);
    table.className = 'calendarPopup';
    table.cellSpacing = 0;

    // Title.
    row = document.createElement('TR');
    cell = document.createElement('TD');
    cell.colSpan = 8;
    cell.className = 'rightAlign';
    link = document.createElement('A');
    link.href = '#';
    link.onclick = function() {
        Element.hide('kgoto');
        if ($('kgoto_iefix')) {
            Element.hide('kgoto_iefix');
        }
        return false;
    }
    link.appendChild(document.createTextNode('x'));
    cell.appendChild(link);
    row.appendChild(cell);
    thead.appendChild(row);

    // Year.
    row = document.createElement('TR');
    cell = document.createElement('TD');
    link = document.createElement('A');
    link.href = '#';
    link.innerHTML = '&laquo;';
    link.onclick = function() {
        newDate = new Date(currentYear - 1, currentDate.getMonth(), 1);
        openKGoto(newDate.getTime() / 1000);
        return false;
    }
    cell.appendChild(link);
    row.appendChild(cell);

    cell = document.createElement('TD');
    cell.colSpan = 6;
    cell.align = 'center';
    link = document.createElement('A');
    link.href = '<?php echo Horde::applicationUrl('year.php') ?>';
    if (link.href.indexOf('?') != -1) {
        link.href += '&';
    } else {
        link.href += '?';
    }
    link.href += 'year=' + year;
    cell.appendChild(link);
    var m = document.createTextNode(year);
    link.appendChild(m);
    row.appendChild(cell);

    cell = document.createElement('TD');
    cell.className = 'rightAlign';
    link = document.createElement('A');
    link.href = '#';
    link.innerHTML = '&raquo;';
    link.onclick = function() {
        newDate = new Date(currentYear + 1, currentDate.getMonth(), 1);
        openKGoto(newDate.getTime() / 1000);
        return false;
    }
    cell.appendChild(link);
    row.appendChild(cell);
    thead.appendChild(row);

    // Month name.
    row = document.createElement('TR');
    cell = document.createElement('TD');
    link = document.createElement('A');
    link.href = '#';
    link.innerHTML = '&laquo;';
    link.onclick = function() {
        var newMonth = currentDate.getMonth() - 1;
        var newYear = currentYear;
        if (newMonth == -1) {
            newMonth = 11;
            newYear -= 1;
        }
        newDate = new Date(newYear, newMonth, currentDate.getDate());
        openKGoto(newDate.getTime() / 1000);
        return false;
    }
    cell.appendChild(link);
    row.appendChild(cell);

    cell = document.createElement('TD');
    cell.colSpan = 6;
    cell.align = 'center';
    link = document.createElement('A');
    link.href = '<?php echo Horde::applicationUrl('month.php') ?>';
    if (link.href.indexOf('?') != -1) {
        link.href += '&';
    } else {
        link.href += '?';
    }
    link.href += 'year=' + year + '&month=' + (month + 1);
    cell.appendChild(link);
    var m = document.createTextNode(months[month]);
    link.appendChild(m);
    row.appendChild(cell);

    cell = document.createElement('TD');
    cell.className = 'rightAlign';
    link = document.createElement('A');
    link.href = '#';
    link.innerHTML = '&raquo;';
    link.onclick = function() {
        newDate = new Date(currentYear, currentDate.getMonth() + 1, 1);
        openKGoto(newDate.getTime() / 1000);
        return false;
    }
    cell.appendChild(link);
    row.appendChild(cell);
    thead.appendChild(row);

    // Weekdays.
    row = document.createElement('TR');
    cell = document.createElement('TH');
    cell.innerHTML = '&nbsp;';
    row.appendChild(cell);
    for (var i = 0; i < 7; i++) {
        cell = document.createElement('TH');
        weekday = document.createTextNode(wdays[i]);
        cell.appendChild(weekday);
        row.appendChild(cell);
    }
    tbody.appendChild(row);

    // Rows.
    var weekInfo;
    var count = 1;
    var today = new Date();
    var thisYear = today.getYear();
    if (thisYear < 1900) {
        thisYear += 1900;
    }
    for (var i = 1; i <= days; i++) {
        if (count == 1) {
            row = document.createElement('TR');
            cell = document.createElement('TD');
            cell.className = 'week';
            weekInfo = weekOfYear(new Date(year, month, i));
            link = document.createElement('A');
            link.href = '<?php echo Horde::applicationUrl('week.php') ?>';
            if (link.href.indexOf('?') != -1) {
                link.href += '&';
            } else {
                link.href += '?';
            }
            link.href += 'year=' + weekInfo[0] + '&week=' + weekInfo[1];
            cell.appendChild(link);
            link.appendChild(document.createTextNode(weekInfo[1]));
            row.appendChild(cell);
        }
        if (i == 1) {
            for (var j = 0; j < diff; j++) {
                cell = document.createElement('TD');
                row.appendChild(cell);
                count++;
            }
        }
        cell = document.createElement('TD');
        if (thisYear == year &&
            today.getMonth() == month &&
            today.getDate() == i) {
            cell.className = 'today';
        }
        link = document.createElement('A');
        link.href = '<?php echo Horde::applicationUrl('day.php') ?>';
        if (link.href.indexOf('?') != -1) {
            link.href += '&';
        } else {
            link.href += '?';
        }
        link.href += 'year=' + year + '&month=' + (month + 1) + '&mday=' + i;
        cell.appendChild(link);
        day = document.createTextNode(i);
        link.appendChild(day);
        row.appendChild(cell);
        if (count == 7) {
            tbody.appendChild(row);
            count = 0;
        }
        count++;
    }
    if (count > 1) {
        for (i = count; i <= 7; i++) {
            cell = document.createElement('TD');
            row.appendChild(cell);
        }
        tbody.appendChild(row);
    }

    // Show popup div.
    var div = $('kgoto');
    if (!div) {
        div = document.createElement('DIV');
        div.id = 'kgoto';
        div.style.position = 'absolute';
        document.body.appendChild(div);
    } else if (div.firstChild) {
        div.removeChild(div.firstChild);
    }
    Element.show(div);
    div.appendChild(table);

    // Position the div if this is the initial click.
    if (event) {
        Position.clone(Event.element(event), div, { setWidth: false, setHeight: false, offsetLeft: 10, offsetTop: 10 });
    }

<?php if ($GLOBALS['browser']->isBrowser('msie') && version_compare($GLOBALS['browser']->getVersion(), '5.5', 'ge')): ?>
    var iefix = $('kgoto_iefix');
    if (!iefix) {
        new Insertion.After(div,
                            '<iframe id="kgoto_iefix" ' +
                            'style="display:none;position:absolute;filter:progid:DXImageTransform.Microsoft.Alpha(opacity=0);" ' +
                            'src="javascript:false;" frameborder="0" scrolling="no"></iframe>');
        iefix = $('kgoto_iefix');
    }

    Position.clone(div, iefix);
    iefix.style.zIndex = 1;
    div.style.zIndex = 2;
    Element.show(iefix);
<?php endif; ?>
}
