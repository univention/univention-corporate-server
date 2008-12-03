<?php

@%@BCWARNING=#@%@

/**
 * $Horde: gollem/config/prefs.php.dist,v 1.33 2006/05/01 20:15:01 karsten Exp $
 *
 * See horde/config/prefs.php for documentation on the structure of this file.
 */

// Make sure that constants are defined.
require_once '/usr/share/horde3/gollem/lib/Gollem.php';

$prefGroups['display'] = array(
    'column' => _("User Interface"),
    'label' => _("File Display"),
    'desc' => _("Change your file sorting options."),
    'members' => array('show_dotfiles', 'sortdirsfirst', 'columnselect',
                       'sortby', 'sortdir'));

$prefGroups['settings'] = array(
    'column' => _("User Interface"),
    'label' => _("Settings"),
    'desc' => _("Change file and folder handling settings."),
    'members' => array('recursive_deletes'));

// show dotfiles?
$_prefs['show_dotfiles'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show dotfiles?")
);

// columns selection widget
$_prefs['columnselect'] = array(
    'locked' => false,
    'type' => 'special'
);

// columns to be displayed
$_prefs['columns'] = array(
    'value' => "ftp\ttype\tname\tdownload\tmodified\tsize\tpermission\towner\tgroup",
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// user preferred sorting column
$_prefs['sortby'] = array(
    'value' => GOLLEM_SORT_TYPE,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(
        GOLLEM_SORT_TYPE => _("File Type"),
        GOLLEM_SORT_NAME => _("File Name"),
        GOLLEM_SORT_DATE => _("File Modification Time"),
        GOLLEM_SORT_SIZE => _("File Size")
    ),
    'desc' => _("Default sorting criteria:")
);

// user preferred sorting direction
$_prefs['sortdir'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(
        GOLLEM_SORT_ASCEND => _("Ascending"),
        GOLLEM_SORT_DESCEND => _("Descending")
    ),
    'desc' => _("Default sorting direction:")
);

// always sort directories before files
$_prefs['sortdirsfirst'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("List folders first?")
);

//user preferred recursive deletes
$_prefs['recursive_deletes'] = array(
    'value' => 'disabled',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(
        'disabled' => _("No"),
        'enabled' => _("Yes"),
        'warn' => _("Ask")
    ),
    'desc' => _("Delete folders recursively?")
);
