/**
 * Horde Calendar javascript widget and utility functions.
 */

/**
 * Backwards-compatible function that wraps access to Horde_Calendar
 */
function openCalendar(imgId, target, callback)
{
    var date = new Date();
    var y, m, d;

    if (document.getElementById(target + '[year]')) {
        y = document.getElementById(target + '[year]').value;
        m = document.getElementById(target + '[month]').value;
        d = document.getElementById(target + '[day]').value;
    } else if (document.getElementById(target + '_year')) {
        y = document.getElementById(target + '_year').value;
        m = document.getElementById(target + '_month').value;
        d = document.getElementById(target + '_day').value;
    }

    if (y && m && d) {
        date = new Date(y, m - 1, d);
    }

    Horde_Calendar.openDate = date.getTime();
    Horde_Calendar.draw(Horde_Calendar.openDate, imgId, target, callback);
}

/**
 * Configuration settings for Horde_Calendar.
 */
var Horde_Calendar_Vars = {
    firstDayOfWeek: <?php echo isset($GLOBALS['prefs']) ? (int)$GLOBALS['prefs']->getValue('first_week_day') : '1' ?>
};

/**
 * Translations for strings used in Horde_Calendar.
 */
var Horde_Calendar_Text = {

    /**
     * Days of the week
     */
    weekdays: [
        '<?php echo _("Su") ?>',
        '<?php echo _("Mo") ?>',
        '<?php echo _("Tu") ?>',
        '<?php echo _("We") ?>',
        '<?php echo _("Th") ?>',
        '<?php echo _("Fr") ?>',
        '<?php echo _("Sa") ?>'
    ],

    /**
     * Month names
     */
    months: [
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
    ]

};

/**
 * Main Horde_Calendar object for rendering javascript calendars.
 */
var Horde_Calendar = {

    date: null,
    target: null,
    openDate: null,

    /**
     * Days in the month (month is a zero-indexed javascript month)
     */
    daysInMonth: function(month, year)
    {
        switch (month) {
        case 3:
        case 5:
        case 8:
        case 10:
            return 30;
        break;

        case 1:
            if (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) {
                return 29;
            } else {
                return 28;
            }
            break;

        default:
            return 31;
            break;
        }
    },

    weeksInMonth: function(month, year)
    {
        var firstOfMonth = (new Date(year, month, 1)).getDay();
        var firstWeekDays, weeks;
        if (Horde_Calendar_Vars.firstDayOfWeek == 1 && firstOfMonth == 0) {
            firstWeekDays = 7 - firstOfMonth + Horde_Calendar_Vars.firstDayOfWeek;
            weeks = 1;
        } else if (Horde_Calendar_Vars.firstDayOfWeek == 0 && firstOfMonth == 6) {
            firstWeekDays = 7 - firstOfMonth + Horde_Calendar_Vars.firstDayOfWeek;
            weeks = 1;
        } else {
            firstWeekDays = Horde_Calendar_Vars.firstDayOfWeek - firstOfMonth;
            weeks = 0;
        }
        firstWeekDays %= 7;
        return Math.ceil((Horde_Calendar.daysInMonth(month, year) - firstWeekDays) / 7) + weeks;
    },

    draw: function(timestamp, imgId, target, callback)
    {
        var row, cell, img, link;

        Horde_Calendar.target = target;
        if (typeof callback != 'function') {
            callback = new Function(callback);
        }
        Horde_Calendar.callback = callback;

        Horde_Calendar.date = new Date(timestamp);
        var month = Horde_Calendar.date.getMonth();
        var year = Horde_Calendar.date.getFullYear();

        var startOfView;
        var firstOfMonth = (new Date(year, month, 1)).getDay();
        var daysInView = Horde_Calendar.weeksInMonth(month, year) * 7;
        var daysInMonth = Horde_Calendar.daysInMonth(month, year);

        if (Horde_Calendar_Vars.firstDayOfWeek == 0) {
            startOfView = 1 - firstOfMonth;

            // We may need to adjust the number of days in the view if
            // we're starting weeks on Sunday.
            if (firstOfMonth == 0) {
                //daysInView -= 7;
            }
            var lastOfMonth = new Date(year, month, daysInMonth);
            lastOfMonth = lastOfMonth.getDay();
            if (lastOfMonth == 0) {
                daysInView += 7;
            }
        } else {
            // @TODO Adjust this for days other than Monday.
            if (firstOfMonth == 0) {
                startOfView = -5;
            } else {
                startOfView = 2 - firstOfMonth;
            }
        }

        var div = document.getElementById('goto');
        if (div.firstChild) {
            div.removeChild(div.firstChild);
        }

        var table = document.createElement('TABLE');
        var thead = document.createElement('THEAD');
        var tbody = document.createElement('TBODY');
        table.appendChild(thead);
        table.appendChild(tbody);
        table.className = 'calendarPopup';
        table.cellSpacing = 0;

        // Title bar.
        row = document.createElement('TR');
        cell = document.createElement('TD');
        cell.colSpan = 7;
        cell.className = 'rightAlign';
        link = document.createElement('A');
        link.href = '#';
        link.onclick = function()
        {
            var div = document.getElementById('goto');
            div.style.display = 'none';
            if (div.firstChild) {
                div.removeChild(div.firstChild);
            }
            var iefix = document.getElementById('goto_iefix');
            if (iefix) {
                iefix.style.display = 'none';
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
        link.onclick = function()
        {
            newDate = new Date(Horde_Calendar.date.getFullYear() - 1, Horde_Calendar.date.getMonth(), 1);
            Horde_Calendar.draw(newDate.getTime(), imgId, Horde_Calendar.target, Horde_Calendar.callback);
            return false;
        }
        cell.appendChild(link);
        row.appendChild(cell);

        cell = document.createElement('TD');
        cell.colSpan = 5;
        cell.align = 'center';
        var y = document.createTextNode(year);
        cell.appendChild(y);
        row.appendChild(cell);

        cell = document.createElement('TD');
        link = document.createElement('A');
        link.href = '#';
        link.innerHTML = '&raquo;';
        link.onclick = function()
        {
            newDate = new Date(Horde_Calendar.date.getFullYear() + 1, Horde_Calendar.date.getMonth(), 1);
            Horde_Calendar.draw(newDate.getTime(), imgId, Horde_Calendar.target, Horde_Calendar.callback);
            return false;
        }
        cell.appendChild(link);
        cell.className = 'rightAlign';
        row.appendChild(cell);
        thead.appendChild(row);

        // Month name.
        row = document.createElement('TR');
        cell = document.createElement('TD');
        link = document.createElement('A');
        link.href = '#';
        link.innerHTML = '&laquo;';
        link.onclick = function()
        {
            var newMonth = Horde_Calendar.date.getMonth() - 1;
            var newYear = Horde_Calendar.date.getFullYear();
            if (newMonth == -1) {
                newMonth = 11;
                newYear -= 1;
            }
            newDate = new Date(newYear, newMonth, 1);
            Horde_Calendar.draw(newDate.getTime(), imgId, Horde_Calendar.target, Horde_Calendar.callback);
            return false;
        }
        cell.appendChild(link);
        row.appendChild(cell);

        cell = document.createElement('TD');
        cell.colSpan = 5;
        cell.align = 'center';
        var m = document.createTextNode(Horde_Calendar_Text.months[month]);
        cell.appendChild(m);
        row.appendChild(cell);

        cell = document.createElement('TD');
        cell.className = 'rightAlign';
        link = document.createElement('A');
        link.href = '#';
        link.innerHTML = '&raquo;';
        link.onclick = function()
        {
            newDate = new Date(Horde_Calendar.date.getFullYear(), Horde_Calendar.date.getMonth() + 1, 1);
            Horde_Calendar.draw(newDate.getTime(), imgId, Horde_Calendar.target, Horde_Calendar.callback);
            return false;
        }
        cell.appendChild(link);
        row.appendChild(cell);
        thead.appendChild(row);

        // Weekdays.
        row = document.createElement('TR');
        for (var i = 0; i < 7; ++i) {
            cell = document.createElement('TH');
            weekday = document.createTextNode(Horde_Calendar_Text.weekdays[(i + Horde_Calendar_Vars.firstDayOfWeek) % 7]);
            cell.appendChild(weekday);
            row.appendChild(cell);
        }
        thead.appendChild(row);

        // Cache today and open date.
        var today = new Date();
        var today_year = today.getFullYear();
        var today_month = today.getMonth();
        var today_day = today.getDate();
        var open = new Date(Horde_Calendar.openDate);
        var open_year = open.getFullYear();
        var open_month = open.getMonth();
        var open_day = open.getDate();

        // Rows.
        var count = 1;
        for (var i = startOfView, i_max = startOfView + daysInView; i < i_max; ++i) {
            if (count == 1) {
                row = document.createElement('TR');
            }

            cell = document.createElement('TD');

            if (i < 1 || i > daysInMonth) {
                row.appendChild(cell);

                if (count == 7) {
                    tbody.appendChild(row);
                    count = 0;
                }

                ++count;
                continue;
            }

            if (today_year == year &&
                today_month == month &&
                today_day == i) {
                cell.className = 'today';
            }
            if (open_year == year &&
                open_month == month &&
                open_day == i) {
                if (cell.className.length) {
                    cell.className += ' current';
                } else {
                    cell.className = 'current';
                }
            }

            link = document.createElement('A');
            cell.appendChild(link);

            link.href = i;
            link.onclick = Horde_Calendar.day_onclick;

            day = document.createTextNode(i);
            link.appendChild(day);

            row.appendChild(cell);
            if (count == 7) {
                tbody.appendChild(row);
                count = 0;
            }
            ++count;
        }
        if (count > 1) {
            tbody.appendChild(row);
        }

        div.appendChild(table);
        div.style.display = '';
        div.style.position = 'absolute';
        div.style.visibility = 'visible';

        // Position the popup every time in case of a different input,
        // window sizing changes, etc.
        var el = document.getElementById(imgId);
        var p = Horde_Calendar.getAbsolutePosition(el);

        if (p.x + div.offsetWidth > document.body.offsetWidth) {
            div.style.left = (document.body.offsetWidth - 10 - div.offsetWidth) + 'px';
        } else {
            div.style.left = p.x + 'px';
        }
        if (p.y + div.offsetHeight > document.body.offsetHeight) {
            div.style.top = (document.body.offsetHeight - 10 - div.offsetHeight) + 'px';
        } else {
            div.style.top = p.y + 'px';
        }

        // Browser sniff for IE taken from Prototype.
        if (!!(window.attachEvent && !window.opera)) {
            // Fix for IE and select elements.
            iefix = document.getElementById('goto_iefix');
            if (!iefix) {
                iefix = document.createElement('IFRAME');
                iefix.id = 'goto_iefix';
                iefix.src = 'javascript:false;';
                iefix.scrolling = 'no';
                iefix.frameborder = 0;
                iefix.style.display = 'none';
                iefix.style.position = 'absolute';
                document.body.appendChild(iefix);
            }
            iefix.style.width = div.offsetWidth;
            iefix.style.height = div.offsetHeight;
            iefix.style.top = div.style.top;
            iefix.style.left = div.style.left;

            if (div.style.zIndex == '') {
                div.style.zIndex = 2;
                iefix.style.zIndex = 1;
            } else {
                iefix.style.zIndex = div.style.zIndex - 1;
            }
            iefix.style.display = '';
        }
    },

    day_onclick: function()
    {
        var day = this.href;
        while (day.indexOf('/') != -1) {
            day = day.substring(day.indexOf('/') + 1);
        }

        // BC
        if (document.getElementById(Horde_Calendar.target + '[year]')) {
            Horde_Calendar.setSelectValue(document.getElementById(Horde_Calendar.target + '[year]'), Horde_Calendar.date.getFullYear());
            Horde_Calendar.setSelectValue(document.getElementById(Horde_Calendar.target + '[month]'), Horde_Calendar.date.getMonth() + 1);
            Horde_Calendar.setSelectValue(document.getElementById(Horde_Calendar.target + '[day]'), day);
        } else {
            Horde_Calendar.setSelectValue(document.getElementById(Horde_Calendar.target + '_year'), Horde_Calendar.date.getFullYear());
            Horde_Calendar.setSelectValue(document.getElementById(Horde_Calendar.target + '_month'), Horde_Calendar.date.getMonth() + 1);
            Horde_Calendar.setSelectValue(document.getElementById(Horde_Calendar.target + '_day'), day);
        }

        var div = document.getElementById('goto');
        div.style.display = 'none';
        if (div.firstChild) {
            div.removeChild(div.firstChild);
        }
        var iefix = document.getElementById('goto_iefix');
        if (iefix) {
            iefix.style.display = 'none';
        }

        if (Horde_Calendar.callback) {
            Horde_Calendar.callback();
        }

        return false;
    },

    getAbsolutePosition: function(el)
    {
        var r = { x: el.offsetLeft, y: el.offsetTop };
        if (el.offsetParent) {
            var tmp = Horde_Calendar.getAbsolutePosition(el.offsetParent);
            r.x += tmp.x;
            r.y += tmp.y;
        }
        return r;
    },

    setSelectValue: function(select, value)
    {
        select.value = value;
        if (select.value != value) {
            for (var i = 0; i < select.options.length; ++i) {
                if (select.options[i].value == value) {
                    select.selectedIndex = i;
                    return true;
                }
            }
        }

        return false;
    }

};
