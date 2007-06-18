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

function openGoto(timestamp)
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

    var lay = document.getElementById('kgoto');
    if (lay.firstChild) {
        lay.removeChild(lay.firstChild);
    }

    var table = document.createElement('TABLE');
    var tbody = document.createElement('TBODY');
    table.appendChild(tbody);
    table.className = 'item';
    table.cellSpacing = 0;
    table.cellPadding = 2;
    table.border = 0;

    // Title.
    row = document.createElement('TR');
    cell = document.createElement('TD');
    cell.colSpan = 8;
    cell.align = 'right';
    cell.className = 'header';
    link = document.createElement('A');
    link.href = '';
    link.onclick = function() {
        document.getElementById('kgoto').style.visibility = 'hidden';
        return false;
    }
    img = document.createElement('IMG');
    img.src = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') ?>/close.gif';
    img.border = 0;
    link.appendChild(img);
    cell.appendChild(link);
    row.appendChild(cell);
    tbody.appendChild(row);

    // Year.
    row = document.createElement('TR');
    cell = document.createElement('TD');
    cell.align = 'left';
    link = document.createElement('A');
    link.href = '';
    link.onclick = function() {
        newDate = new Date(currentYear - 1, currentDate.getMonth(), currentDate.getDate());
        openGoto(newDate.getTime() / 1000);
        return false;
    }
    cell.appendChild(link);
    img = document.createElement('IMG')
    img.src = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') ?>/nav/left.gif';
    img.align = 'middle';
    img.border = 0;
    link.appendChild(img);
    row.appendChild(cell);

    cell = document.createElement('TD');
    cell.colSpan = 6;
    cell.align = 'center';
    var y = document.createTextNode(year);
    cell.appendChild(y);
    row.appendChild(cell);

    cell = document.createElement('TD');
    cell.align = 'right';
    link = document.createElement('A');
    link.href = '';
    link.onclick = function() {
        newDate = new Date(currentYear + 1, currentDate.getMonth(), currentDate.getDate());
        openGoto(newDate.getTime() / 1000);
        return false;
    }
    cell.appendChild(link);
    img = document.createElement('IMG')
    img.src = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') ?>/nav/right.gif';
    img.align = 'middle';
    img.border = 0;
    link.appendChild(img);
    row.appendChild(cell);
    tbody.appendChild(row);

    // Month name.
    row = document.createElement('TR');
    cell = document.createElement('TD');
    cell.align = 'left';
    link = document.createElement('A');
    link.href = '';
    link.onclick = function() {
        newDate = new Date(currentYear, currentDate.getMonth() - 1, currentDate.getDate());
        openGoto(newDate.getTime() / 1000);
        return false;
    }
    cell.appendChild(link);
    img = document.createElement('IMG')
    img.src = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') ?>/nav/left.gif';
    img.align = 'middle';
    img.border = 0;
    link.appendChild(img);
    row.appendChild(cell);

    cell = document.createElement('TD');
    cell.colSpan = 6;
    cell.align = 'center';
    link = document.createElement('A');
    link.href = '<?php echo Horde::applicationUrl('month.php') ?>';
    if (link.href.indexOf('?') != -1) {
        link.href += '<?php echo ini_get('arg_separator.output') ?>year=' + year + '<?php echo ini_get('arg_separator.output') ?>month=' + (month + 1);
    } else {
        link.href += '?year=' + year + '<?php echo ini_get('arg_separator.output') ?>month=' + (month + 1);
    }
    cell.appendChild(link);
    var m = document.createTextNode(months[month]);
    link.appendChild(m);
    row.appendChild(cell);

    cell = document.createElement('TD');
    cell.align = 'right';
    link = document.createElement('A');
    link.href = '';
    link.onclick = function() {
        newDate = new Date(currentYear, currentDate.getMonth() + 1, currentDate.getDate());
        openGoto(newDate.getTime() / 1000);
        return false;
    }
    cell.appendChild(link);
    img = document.createElement('IMG')
    img.src = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') ?>/nav/right.gif';
    img.align = 'middle';
    img.border = 0;
    link.appendChild(img);
    row.appendChild(cell);
    tbody.appendChild(row);

    // weekdays
    row = document.createElement('TR');
    cell = document.createElement('TD');
    row.appendChild(cell);
    for (var i = 0; i < 7; i++) {
        cell = document.createElement('TD');
        weekday = document.createTextNode(wdays[i]);
        cell.appendChild(weekday);
        row.appendChild(cell);
    }
    tbody.appendChild(row);

    // rows
    var weekInfo, italic;
    var count = 1;
    var today = new Date();
    var thisYear = today.getYear();
    if (thisYear < 1900) {
        thisYear += 1900;
    }
    var odd = true;
    for (var i = 1; i <= days; i++) {
        if (count == 1) {
            row = document.createElement('TR');
            row.align = 'right';
            if (odd) {
                row.className = 'item0';
            } else {
                row.className = 'item1';
            }
            odd = !odd;
            cell = document.createElement('TD');
            weekInfo = weekOfYear(new Date(year, month, i));
            italic = document.createElement('I');
            cell.appendChild(italic);
            link = document.createElement('A');
            link.href = '<?php echo Horde::applicationUrl('week.php') ?>';
            if (link.href.indexOf('?') != -1) {
                link.href += '<?php echo ini_get('arg_separator.output') ?>year=' + weekInfo[0] + '<?php echo ini_get('arg_separator.output') ?>week=' + weekInfo[1];
            } else {
                link.href += '?year=' + weekInfo[0] + '<?php echo ini_get('arg_separator.output') ?>week=' + weekInfo[1];
            }
            italic.appendChild(link);
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
            cell.style.border = '1px solid red';
        }
        link = document.createElement('A');
        link.href = '<?php echo Horde::applicationUrl('day.php') ?>';
        if (link.href.indexOf('?') != -1) {
            link.href += '<?php echo ini_get('arg_separator.output') ?>year=';
        } else {
            link.href += '?year=';
        }
        link.href += year + '<?php echo ini_get('arg_separator.output') ?>month=' + (month + 1) + '<?php echo ini_get('arg_separator.output') ?>mday=' + i;
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

    // show Layer
    lay.appendChild(table);
    lay.style.visibility = 'visible';
}
