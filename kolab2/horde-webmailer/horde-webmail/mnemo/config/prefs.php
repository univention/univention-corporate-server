<?php
/**
 * $Horde: mnemo/config/prefs.php.dist,v 1.24.2.5 2009-06-19 17:06:22 jan Exp $
 *
 * See horde/config/prefs.php for documentation on the structure of this file.
 */

// Make sure that constants are defined.
require_once dirname(__FILE__) . '/../lib/Mnemo.php';

$prefGroups['display'] = array(
    'column' => _("General Options"),
    'label' => _("Display Options"),
    'desc' => _("Change your note sorting and display options."),
    'members' => array('show_notepad', 'sortby', 'sortdir')
);

$prefGroups['share'] = array(
    'column' => _("General Options"),
    'label' => _("Default Notepad"),
    'desc' => _("Choose your default Notepad."),
    'members' => array('notepadselect')
);

$prefGroups['deletion'] = array(
    'column' => _("General Options"),
    'label' => _("Delete Confirmation"),
    'desc' => _("Delete button behaviour"),
    'members' => array('delete_opt')
);


// show a notepad column in the list view?
$_prefs['show_notepad'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Should the Notepad be shown in its own column in the List view?")
);

// show the notepad options panel?
// a value of 0 = no, 1 = yes
$_prefs['show_panel'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// user preferred sorting column
$_prefs['sortby'] = array(
    'value' => MNEMO_SORT_DESC,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(MNEMO_SORT_DESC => _("Note Text"),
                    MNEMO_SORT_CATEGORY => _("Note Category"),
                    MNEMO_SORT_NOTEPAD => _("Notepad")),
    'desc' => _("Default sorting criteria:")
);

// user preferred sorting direction
$_prefs['sortdir'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(MNEMO_SORT_ASCEND => _("Ascending"),
                    MNEMO_SORT_DESCEND => _("Descending")),
    'desc' => _("Default sorting direction:")
);

// user note categories
$_prefs['memo_categories'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// category highlight colors
$_prefs['memo_colors'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// default notepad selection widget
$_prefs['notepadselect'] = array('type' => 'special');

// default notepad
// Set locked to true if you don't want users to have multiple notepads.
$_prefs['default_notepad'] = array(
    'value' => Auth::getAuth() ? Auth::getAuth() : 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// store the notepads to diplay
$_prefs['display_notepads'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// preference for delete confirmation dialog.
$_prefs['delete_opt'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Do you want to confirm deleting entries?")
);
