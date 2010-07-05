<?php

if (!function_exists('_imp_hook_display_folder')) {
    function _imp_hook_display_folder($mailbox)
    {
        $type = Kolab::getMailboxType($mailbox);
        return empty($type) || $type == 'mail';
    }
}
