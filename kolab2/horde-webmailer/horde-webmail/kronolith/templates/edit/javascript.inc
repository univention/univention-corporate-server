<?php echo $GLOBALS['cManager']->getJavaScript('eventform', 'category') ?>

<script type="text/javascript">

<?php if (!Util::nonInputVar('issearch')): ?>

function setInterval(field)
{
    elt = document.eventform[field];
    if (elt.value == "") {
        elt.value = 1;
    }

    if (field == 'recur_daily_interval') clearFields(1);
    else if (field == 'recur_weekly_interval') clearFields(2);
    else if (field == 'recur_day_of_month_interval') clearFields(3);
    else if (field == 'recur_week_of_month_interval') clearFields(4);
    else if (field == 'recur_yearly_interval') clearFields(5);
}

function setRecur(index)
{
    document.eventform.recur[index].checked = true;
    clearFields(index);
}

function clearFields(index)
{
    var f = document.eventform;
    if (index != 1) f.recur_daily_interval.value = '';
    if (index != 2) {
        f.recur_weekly_interval.value = '';
        for (var i = 0; i < f.elements.length; i++) {
            if (f.elements[i].name == 'weekly[]') {
                f.elements[i].checked = false;
            }
        }
    }
    if (index != 3) f.recur_day_of_month_interval.value = '';
    if (index != 4) f.recur_week_of_month_interval.value = '';
    if (index != 5) f.recur_yearly_interval.value = '';
}

<?php endif; ?>

function setWholeDay(wholeDay)
{
    if (wholeDay == 1) {
<?php if ($GLOBALS['prefs']->getValue('twentyFour')): ?>
        $('start_hour').selectedIndex = 0;
<?php else: ?>
        $('start_hour').selectedIndex = 11;
        $('am').checked = true;
<?php endif; ?>
        $('start_min').selectedIndex = 0;
        $('dur_day').value = 0;
        $('dur_hour').selectedIndex = 23;
        $('dur_min').selectedIndex = 12;
    }
}

function updateWday(span)
{
<?php if ($GLOBALS['browser']->hasFeature('dom')): ?>
    wdays = [
        '<?php echo addslashes(_("Sunday")) ?>',
        '<?php echo addslashes(_("Monday")) ?>',
        '<?php echo addslashes(_("Tuesday")) ?>',
        '<?php echo addslashes(_("Wednesday")) ?>',
        '<?php echo addslashes(_("Thursday")) ?>',
        '<?php echo addslashes(_("Friday")) ?>',
        '<?php echo addslashes(_("Saturday")) ?>'
    ];
    if (span == 'start_wday') {
        spanObj = $('start_wday');
        day = $('start_day').value;
        month = $('start_month').value - 1;
        year = $('start_year').value;
    } else if (span == 'end_wday') {
        spanObj = $('end_wday');
        day = $('end_day').value;
        month = $('end_month').value - 1;
        year = $('end_year').value;
<?php if (!Util::nonInputVar('issearch')): ?>
    } else if (span == 'recur_end_wday') {
        spanObj = $('recur_end_wday');
        day = $('recur_enddate_day').value;
        month = $('recur_enddate_month').value - 1;
        year = $('recur_enddate_year').value;
<?php endif; ?>
    }
    date = new Date(year, month, day)
    spanObj.innerHTML = '(' + wdays[date.getDay()] + ')';
<?php endif; ?>
}
<?php if (!$GLOBALS['prefs']->getValue('twentyFour')): ?>

// Converts a 12 hour based number to its 24 hour format
function convertTo24Hour(in_hour, pm_elementName)
{
    if ($F(pm_elementName)) {
        if (in_hour != 12) {
            in_hour += 12;
        }
    } else if (in_hour == 12) {
        in_hour = 0;
    }

    return in_hour;
}
<?php endif; ?>

function updateDuration()
{
    var startHour = parseInt($F('start_hour'));
    var endHour = parseInt($F('end_hour'));
<?php if (!$GLOBALS['prefs']->getValue('twentyFour')): ?>
    startHour = convertTo24Hour(startHour, 'pm');
    endHour = convertTo24Hour(endHour, 'epm');
<?php endif; ?>
    var startDate = Date.UTC($F('start_year'),
                             $F('start_month') - 1,
                             $F('start_day'),
                             startHour,
                             $F('start_min'));
    var endDate = Date.UTC($F('end_year'),
                           $F('end_month') - 1,
                           $F('end_day'),
                           endHour,
                           $F('end_min'));
    var failed = false;
    if (endDate < startDate) {
<?php if (!$GLOBALS['prefs']->getValue('twentyFour')): ?>
        // If the end hour is marked as the (default) AM, and the
        // start hour is also AM, automatically default the end hour
        // to PM if the date is otherwise the same - assume that the
        // user wants a 9am-2pm event (for example), instead of
        // throwing an error.
        if ($F('start_year') == $F('end_year') &&
            $F('start_month') == $F('end_month') &&
            $F('start_day') == $F('end_day') &&
            !$F('pm') && !$F('epm')) {
            // Toggle the end date to PM.
            $('epm').checked = true;

            // Recalculate end time.
            var endHour = parseInt($F('end_hour'));
            endHour = convertTo24Hour(endHour, 'epm');
            endDate = Date.UTC($F('end_year'),
                               $F('end_month') - 1,
                               $F('end_day'),
                               endHour,
                               $F('end_min'));
        } else {
<?php endif; ?>
        alert('<?php echo addslashes(_("The end date must be later than the start date.")) ?>');
        endDate = startDate;
        failed = true;
<?php if (!$GLOBALS['prefs']->getValue('twentyFour')): ?>
        }
<?php endif; ?>
    }
    var duration = (endDate - startDate) / 1000;
    $('dur_day').value = Math.floor(duration / 86400);
    duration %= 86400;
    var durHour = Math.floor(duration / 3600);
    duration %= 3600;
    var durMin = Math.floor(duration / 60 / 5);
    $('dur_hour').selectedIndex = durHour;
    $('dur_min').selectedIndex = durMin;
    $('allday').checked = false;
    if (failed) {
        updateEndDate();
    }
}

function updateEndDate()
{
    var yearDiff = <?php echo date('Y') - 1 ?>;
    var startHour = parseInt($F('start_hour'));
<?php if (!$GLOBALS['prefs']->getValue('twentyFour')): ?>
    startHour = convertTo24Hour(startHour, 'pm');
<?php endif; ?>
    var startDate = new Date($F('start_year'),
                             $F('start_month') - 1,
                             $F('start_day'),
                             startHour,
                             $F('start_min'));
    var endDate = new Date();
    var minutes = $F('dur_day') * 1440;
    minutes += $F('dur_hour') * 60;
    minutes += parseInt($F('dur_min'));
    var msecs = minutes * 60000;
    endDate.setTime(startDate.getTime() + msecs);
    var endYear = endDate.getYear();
    if (endYear < 1900) {
        endYear += 1900;
    }
    $('end_year').value = endYear;
    $('end_month').selectedIndex = endDate.getMonth();
    $('end_day').selectedIndex = endDate.getDate() - 1;
    var endHour = endDate.getHours()
<?php if (!$GLOBALS['prefs']->getValue('twentyFour')): ?>
    if (endHour < 12) {
        if (endHour == 0) {
            endHour = 12;
        }
        $('eam').checked = true;
    } else {
        if (endHour > 12) {
            endHour -= 12;
        }
        $('epm').checked = true;
    }
    endHour -= 1;
<?php endif; ?>
    $('end_hour').selectedIndex = endHour;
    $('end_min').selectedIndex = endDate.getMinutes() / 5;
    updateWday('end_wday');
}

function setStartDate(date)
{
    var startDate = new Date();
    startDate.setTime(date * 1000);
    var startYear = startDate.getYear();
    if (startYear < 1900) {
        startYear += 1900;
    }
    $('start_year').value = startYear;
    $('start_month').selectedIndex = startDate.getMonth();
    $('start_day').selectedIndex = startDate.getDate() - 1;
    updateEndDate();
    // Uncheck recurring weekdays.
    $('mo').checked = false;
    $('tu').checked = false;
    $('we').checked = false;
    $('th').checked = false;
    $('fr').checked = false;
    $('sa').checked = false;
    $('su').checked = false;
}

<?php if (Util::getFormData('allday') == 1): ?>
Event.observe(window, 'load', function() {
    $('allday').click;
});
<?php endif; ?>

function toggleSection(section)
{
    var dir = '<?php echo $GLOBALS['registry']->getImageDir() ?>';
    if (!$('section_' + section)) {
        return;
    }
    $('section_' + section).toggle();
    if ($('section_' + section).visible()) {
        $('toggle_' + section).src = dir + '/minus.png';
        $('toggle_' + section).alt = '<?php addslashes(_("Hide")) ?>';
        if ($('extra_' + section)) {
            $('extra_' + section).hide();
        }
    } else {
        $('toggle_' + section).src = dir + '/plus.png';
        $('toggle_' + section).alt = '<?php addslashes(_("Show")) ?>';
        if ($('extra_' + section)) {
            $('extra_' + section).show();
        }
    }
}
Event.observe(window, 'load', function() {
    toggleSection('description');
    toggleSection('attendees');
    toggleSection('recurrence');
<?php if ($GLOBALS['conf']['metadata']['keywords']): ?>
    toggleSection('keywords');
<?php endif; ?>
});

</script>
