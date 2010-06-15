<?php
/**
 * $Horde: turba/lib/prefs.php,v 1.1 2004/02/23 07:20:29 slusarz Exp $
 *
 * Copyright 2001-2004 Jon Parise <jon@horde.org>
 * Copyright 2002-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

function handle_columnselect($updated)
{
    $columns = Util::getFormData('columns');
    if (!empty($columns)) {
        $GLOBALS['prefs']->setValue('columns', $columns);
        return true;
    }

    return false;
}

/* Assign variables for select lists. */
if (!$prefs->isLocked('default_dir')) {
    $default_dir_options = array();
    foreach ($cfgSources as $key => $info) {
        $default_dir_options[$key] = $info['title'];
    }
}
