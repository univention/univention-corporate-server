<?php
/**
 * $Horde: kronolith/config/prefs.php.dist,v 1.66.2.14 2009-06-19 17:06:22 jan Exp $
 *
 * See horde/config/prefs.php for documentation on the structure of this file.
 */

$prefGroups['view'] = array(
    'column' => _("Display Options"),
    'label' => _("User Interface"),
    'desc' => _("Select confirmation options, how to display the different views and choose default view."),
    'members' => array('confirm_delete', 'defaultview',
                       'time_between_days', 'week_start_monday',
                       'day_hour_start', 'day_hour_end', 'day_hour_force',
                       'slots_per_hour', 'show_icons', 'show_time', 'show_location',
                       'show_legend', 'show_fb_legend', 'show_shared_side_by_side', 'show_external_colors'),
);

$prefGroups['summary'] = array(
    'column' => _("Display Options"),
    'label' => _("Portal Options"),
    'desc' => _("Select which events to show in the portal."),
    'members' => array('summary_days', 'summary_alarms'),
);

$prefGroups['share'] = array(
    'column' => _("Calendars"),
    'label' => _("Default Calendar"),
    'desc' => _("Choose your default calendar."),
    'members' => array('shareselect'),
);

if (!empty($GLOBALS['conf']['holidays']['enable'])) {
    $prefGroups['holidays'] = array(
        'column' => _("Calendars"),
        'label' => _("Holidays"),
        'desc' => _("Choose which holidays to display"),
        'members' => array('holiday_drivers'),
    );
}

$prefGroups['event_options'] = array(
    'column' => _("Events"),
    'label' => _("Event Defaults"),
    'desc' => _("Set default values for new events."),
    'members' => array('default_alarm_management'),
);
$prefGroups['maintenance'] = array(
    'column' => _("Events"),
    'label' => _("Maintenance"),
    'desc' => _("Set options for deleting old events."),
    'members' => array('purge_events', 'purge_events_interval', 'purge_events_keep')
);

$prefGroups['notification'] = array(
    'column' => _("Events"),
    'label' => _("Notifications"),
    'desc' => _("Choose how you want to be notified about event changes, event alarms and upcoming events."),
    'members' => array('event_notification', 'event_notification_exclude_self', 'daily_agenda', 'event_reminder'),
);
if (!empty($GLOBALS['conf']['alarms']['driver'])) {
    $prefGroups['notification']['members'][] = 'event_alarms';
}

$prefGroups['freebusy'] = array(
    'column' => _("Calendars"),
    'label' => _("Free/Busy Information"),
    'desc' => _("Set your Free/Busy calendars and your own and other users' Free/Busy options."),
    'members' => array('fb_cals_select', 'freebusy_days'),
);

if ($GLOBALS['registry']->hasMethod('contacts/sources')) {
    $prefGroups['addressbooks'] = array(
        'column' => _("Other Options"),
        'label' => _("Address Books"),
        'desc' => _("Select address book sources for adding and searching for addresses."),
        'members' => array('display_contact', 'sourceselect'),
    );
}

// confirm deletion of events which don't recur?
$_prefs['confirm_delete'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Confirm deletion of events?")
);

// default view
$_prefs['defaultview'] = array(
    'value' => 'month',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('day' => _("Day"),
                    'week' => _("Week"),
                    'workweek' => _("Work Week"),
                    'month' => _("Month")),
    'desc' => _("Select the view to display on startup:")
);

// Display the timeslots between each day column, in week view.
$_prefs['time_between_days'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show time of day between each day in week views?")
);

// what day does the week start with
$_prefs['week_start_monday'] = array(
    'value' => '0',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'desc' => _("Select the first weekday:"),
    'enum' => array('0' => _("Sunday"),
                    '1' => _("Monday"))
);

// start of the time range in day/week views:
$_prefs['day_hour_start'] = array(
    'value' => 16,
    'locked' => false,
    'shared' => false,
    'type' => 'select',
    'desc' => _("What time should day and week views start, when there are no earlier events?")
);

// end of the time range in day/week views:
$_prefs['day_hour_end'] = array(
    'value' => 48,
    'locked' => false,
    'shared' => false,
    'type' => 'select',
    'desc' => _("What time should day and week views end, when there are no later events?")
);

// enforce hour slots?
$_prefs['day_hour_force'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Restrict day and week views to these time slots, even if there <strong>are</strong> earlier or later events?"),
);

// number of slots in each hour:
$_prefs['slots_per_hour'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'desc' => _("How long should the time slots on the day and week views be?"),
    'enum' => array(4 => _("15 minutes"),
                    3 => _("20 minutes"),
                    2 => _("30 minutes"),
                    1 => _("1 hour"),
    ),
);

// show delete/alarm icons in the calendar view?
$_prefs['show_icons'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show delete, alarm, and recurrence icons in calendar views?"),
);

// show event start/end times in the calendar and/or print views?
$_prefs['show_time'] = array(
    'value' => 'a:1:{i:0;s:5:"print";}',
    'locked' => false,
    'shared' => false,
    'type' => 'multienum',
    'enum' => array('screen' => _("Month, Week, and Day Views"),
                    'print' => _("Print Views"),
     ),
    'desc' => _("Choose the views to show event start and end times in:"),
);

// show event location in the calendar and/or print views?
$_prefs['show_location'] = array(
    'value' => 'a:1:{i:0;s:5:"print";}',
    'locked' => false,
    'shared' => false,
    'type' => 'multienum',
    'enum' => array('screen' => _("Month, Week, and Day Views"),
                    'print' => _("Print Views"),
     ),
    'desc' => _("Choose the views to show event locations in:"),
);

// show category legend?
// a value of 0 = no, 1 = yes
$_prefs['show_legend'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show category legend?"),
);

// show the calendar options panel?
// a value of 0 = no, 1 = yes
$_prefs['show_panel'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// show Free/Busy legend?
// a value of 0 = no, 1 = yes
$_prefs['show_fb_legend'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show Free/Busy legend?"),
);

// collapsed or side by side view
$_prefs['show_shared_side_by_side'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show shared calendars side-by-side?"),
);

// days to show in summary
$_prefs['summary_days'] = array(
    'value' => 7,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'desc' => _("Select the time span to show:"),
    'enum' => array(1 => '1 ' . _("day"),
                    2 => '2 ' . _("days"),
                    3 => '3 ' . _("days"),
                    4 => '4 ' . _("days"),
                    5 => '5 ' . _("days"),
                    6 => '6 ' . _("days"),
                    7 => '1 ' . _("week"),
                    14 => '2 ' . _("weeks"),
                    21 => '3 ' . _("weeks"),
                    28 => '4 ' . _("weeks"),
    ),
);

// show alarms in summary?
$_prefs['summary_alarms'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show only events that have an alarm set?"),
);

// show external event colors?
$_prefs['show_external_colors'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show external events using category colors?"),
);

// default calendar selection widget
$_prefs['shareselect'] = array('type' => 'special');

// default calendar
// Set locked to true if you don't want users to have multiple calendars.
$_prefs['default_share'] = array(
    'value' => Auth::getAuth() ? Auth::getAuth() : 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// Which drivers are we supposed to use to examine holidays?
$_prefs['holiday_drivers'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'multienum',
    'desc' => _("Which kind of holidays do you want to get displayed?"),
);

// store the calendars to diplay
$_prefs['display_cals'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// default alarm
$_prefs['default_alarm'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);
$_prefs['default_alarm_management'] = array('type' => 'special');

// remote calendars
$_prefs['remote_cals'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// store the remote calendars to display
$_prefs['display_remote_cals'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// store the external calendars to display
$_prefs['display_external_cals'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// new event notifications
$_prefs['event_notification'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('' => _("No"),
                    'owner' => _("On my calendars only"),
                    'show' => _("On all shown calendars"),
                    'read' => _("On all calendars I have read access to")),
    'desc' => _("Choose if you want to be notified of new, edited, and deleted events by email:")
);

// daily agenda
$_prefs['daily_agenda'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('' => _("No"),
                    'owner' => _("On my calendars only"),
                    'show' => _("On all shown calendars"),
                    'read' => _("On all calendars I have read access to")),
    'desc' => _("Choose if you want to receive daily agenda email reminders:")
);

$_prefs['event_notification_exclude_self'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Don't send me a notification if I've added, changed or deleted the event?")
);

// reminder notifications
$_prefs['event_reminder'] = array(
    'value' => 'owner',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('' => _("No"),
                    'owner' => _("On my calendars only"),
                    'show' => _("On all shown calendars"),
                    'read' => _("On all calendars I have read access to")),
    'desc' => _("Choose if you want to receive reminders for events with alarms:")
);

// alarm methods
$_prefs['event_alarms'] = array(
    'value' => 'a:1:{s:6:"notify";a:0:{}}',
    'locked' => false,
    'shared' => false,
    'type' => 'alarm',
    'desc' => _("Choose how you want to receive reminders for events with alarms:")
);

// number of days to generate Free/Busy information for:
$_prefs['freebusy_days'] = array(
    'value' => 30,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("How many days of Free/Busy information should be generated?")
);

// By default, display all contacts in the address book when loading
// the contacts screen.  If your default address book is large and
// slow to display, you may want to disable and lock this option.
$_prefs['display_contact'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("List all contacts when loading the contacts screen? (if disabled, you will only see contacts that you search for explicitly)"),
);

// address book selection widget
$_prefs['sourceselect'] = array('type' => 'special');

// address book(s) to use when expanding addresses
// You can provide default values this way (note the \t and the double quotes):
// 'value' => "source_one\tsource_two"
// refer to turba/config/sources.php for possible source values
$_prefs['search_sources'] = array(
    'value' => "",
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// field(s) to use when expanding addresses
// This depends on the search_sources preference if you want to provide
// default values:
// 'value' => "source_one\tfield_one\tfield_two\nsource_two\tfield_three"
// will search the fields 'field_one' and 'field_two' in source_one and
// 'field_three' in source_two.
// refer to turba/config/sources.php for possible source and field values
$_prefs['search_fields'] = array(
    'value' => "",
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// Calendars to include in generating Free/Busy URLs.
$_prefs['fb_cals'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
    'desc' => _("Choose the calendars to include when generating Free/Busy URLs:")
);

// Free/Busy calendars selector.
$_prefs['fb_cals_select'] = array('type' => 'special');

// The following two preferences are no longer used and only necessary for the
// upgrade script.
$_prefs['event_categories'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);
$_prefs['event_colors'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

$_prefs['purge_events'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Purge old events from your calender?"),
);

// 'value': yearly = 1, monthly = 2, weekly = 3, daily = 4, every login = 5
$_prefs['purge_events_interval'] = array(
    'value' => '2',
    'locked' => false,
    'shared' => false,
    'type' => 'select',
    'desc' => _("Purge old events how often:"),
);

$_prefs['purge_events_keep'] = array(
    'value' => 365,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("Purge old events older than this amount of days."),
);

// last time maintenance was run.
// value is a UNIX timestamp of the last time maintenance ran for the user.
$_prefs['last_kronolith_maintenance'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

$_prefs['saved_attendee_list'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
    'desc' => _("A saved list of attendees")
);
