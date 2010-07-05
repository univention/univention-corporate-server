<?php
/**
 * $Horde: turba/lib/prefs.php,v 1.2.10.11 2009-01-06 15:27:47 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
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

function handle_addressbookselect($updated)
{
    $addressbooks = Util::getFormData('addressbooks');
    $GLOBALS['prefs']->setValue('addressbooks', str_replace("\r", '', $addressbooks));
    return true;
}

/* Assign variables for select lists. */
if (!$prefs->isLocked('default_dir')) {
    $default_dir_options = array();
    foreach ($cfgSources as $key => $info) {
        $default_dir_options[$key] = $info['title'];
    }
}

foreach (Turba::getAddressBooks() as $key => $curSource) {
    if (empty($curSource['map']['__uid'])) {
        continue;
    }
    if (!empty($curSource['browse'])) {
        $_prefs['sync_books']['enum'][$key] = $curSource['title'];
    }
    $sync_books = @unserialize($prefs->getValue('sync_books'));
    if (empty($sync_books)) {
        $prefs->setValue('sync_books',
                         serialize(array(Turba::getDefaultAddressbook())));
    }
}
