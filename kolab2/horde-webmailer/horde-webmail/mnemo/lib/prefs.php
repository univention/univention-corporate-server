<?php
/**
 * $Horde: mnemo/lib/prefs.php,v 1.2.10.10 2009-01-13 15:47:33 chuck Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Mnemo 2.0
 * @package Mnemo
 */

function handle_notepadselect($updated)
{
    global $prefs;

    $default_notepad = Util::getFormData('default_notepad');
    if (!is_null($default_notepad)) {
        $notepads = Mnemo::listNotepads();
        if (is_array($notepads) && array_key_exists($default_notepad, $notepads)) {
            $prefs->setValue('default_notepad', $default_notepad);
            $updated = true;
        }
    }
    return $updated;
}
