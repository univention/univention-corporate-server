<?php
/**
 * Support functions for importing SquirreMail preferences.
 *
 * @author Ben Chavet <ben@horde.org>
 */

function savePrefs($user, $basename, $prefs_cache)
{
    global $prefs;

    // Load default SquirrelMail signature
    $prefs_cache['signature'] = getSignature($basename);

    // Loop through the SquirrelMail prefs and translate them to Horde prefs
    foreach ($prefs_cache as $key => $val) {
        $horde_pref = convert($key, $val);
        if (!$horde_pref) {
            continue;
        }
        foreach ($horde_pref as $pref) {
            $prefs->retrieve($pref['scope']);
            $prefs->setValue($pref['name'], $pref['value']);
        }
    }

    // Import identities
    if (isset($prefs_cache['identities']) && $prefs_cache['identities'] > 1) {
        $identity = &Identity::singleton(array('imp', 'imp'), $user);
        // Intentionally off-by-one
        for ($i = 1; $i < $prefs_cache['identities']; $i++) {
            $new_identity = array('id' => 'Identity #' . ($i + 1),
                                  'fullname' => $prefs_cache['full_name' . $i],
                                  'replyto_addr' => $prefs_cache['reply_to' . $i],
                                  'from_addr' => $prefs_cache['email_address' . $i],
                                  'signature' => getSignature($basename, $i));
            if (isset($prefs_cache['prefix_sig'])) {
                $new_identity['sig_dashes'] = $prefs_cache['prefix_sig'];
            }
            if (isset($prefs_cache['sig_first'])) {
                $new_identity['sig_first'] = $prefs_cache['sig_first'];
            }
            if (isset($prefs_cache['sent_folder'])) {
                if ($prefs_cache['sent_folder'] == '[ ' . _("Do not use Sent") . ' ]') {
                    $new_identity['save_sent_mail'] = 0;
                } else {
                    $new_identity['save_sent_mail'] = 1;
                }
            }
            $identity->add($new_identity);
        }
        $identity->save();
    }

    // Store prefs
    $prefs->store();
}

/**
 * Returns the horde pref value(s) that correspond with the given squirrelmail
 * pref.
 *
 * @return array of pref arrays ('name', 'scope', 'value').
 *         false if there is no horde pref equivalent, or the horde default
 *           should be used.
 */
function convert($sm_pref_name, $sm_pref_value)
{

    switch ($sm_pref_name) {

    case 'compose_new_win':
        return array(array('name' => 'compose_popup', 'scope' => 'imp', 'value' => $sm_pref_value));
        break;

    case 'draft_folder':
        if ($sm_pref_value != '[ ' . _("Do not use Drafts") . ' ]') {
            return array(array('name' => 'drafts_folder', 'scope' => 'imp', 'value' => $sm_pref_value));
        }
        break;

    case 'email_address':
        return array(array('name' => 'from_addr', 'scope' => 'horde', 'value' => $sm_pref_value));
        break;

    case 'full_name':
        return array(array('name' => 'fullname', 'scope' => 'horde', 'value' => $sm_pref_value));
        break;

    case 'hour_format':
        return array(array('name' => 'twentyFour', 'scope' => 'horde', 'value' => ($sm_pref_value == 1)));
        break;
                     
    case 'internal_date_sort':
        if ($sm_pref_value == 1) {
            return array(array('name' => 'sortby', 'scope' => 'imp', 'value' => '1'));
        }
        break;

    case 'language':
        return array(array('name' => 'language', 'scope' => 'horde', 'value' => $sm_pref_value));
        break;

    case 'left_refresh':
        return array(array('name' => 'menu_refresh_time', 'scope' => 'horde', 'value' => $sm_pref_value));
        break;

    case 'left_size':
        return array(array('name' => 'sidebar_width', 'scope' => 'horde', 'value' => $sm_pref_value));
        break;

    case 'mdn_user_support':
        $value = 'ask';
        if ($sm_pref_value == 0) {
            $value = 'never';
        }
        return array(array('name' => 'disposition_request_read',
                           'scope' => 'imp',
                           'value' => $value));
        break;

    case 'prefix_sig':
        return array(array('name' => 'sig_dashes', 'scope' => 'imp', 'value' => $sm_pref_value));
        break;

    case 'reply_citation_style':
        switch ($sm_pref_value) {
        case 'none':
            return array(array('name' => 'attrib_text', 'scope' => 'imp', 'value' => ''));
            break;
        case 'author_said':
            return array(array('name' => 'attrib_text', 'scope' => 'imp', 'value' => '%p wrote'));
            break;
        case 'date_time_author':
            return array(array('name' => 'attrib_text', 'scope' => 'imp', 'value' => 'On %c, %p wrote'));
            break;
        }
        break;

    case 'reply_to':
        return array(array('name' => 'replyto_addr', 'scope' => 'imp', 'value' => $sm_pref_value));
        break;

    case 'sent_folder':
        if ($sm_pref_value == '[ ' . _("Do not use Sent") . ' ]') {
            return array(array('name' => 'save_sent_mail', 'scope' => 'imp', 'value' => '0'));
        }
        return array(array('name' => 'save_sent_mail', 'scope' => 'imp', 'value' => '1'),
                     array('name' => 'sent_mail_folder', 'scope' => 'imp', 'value' => $sm_pref_value));
        break;

    case 'show_num':
        return array(array('name' => 'max_msgs', 'scope' => 'imp', 'value' => $sm_pref_value));
        break;

    case 'show_xmailer_default':
        if ($sm_pref_value == 1) {
            $GLOBALS['prefs']->retrieve('imp');
            $value = "X-Mailer\n" . $GLOBALS['prefs']->getValue('mail_hdr');
            return array(array('name' => 'mail_hdr', 'scope' => 'imp', 'value' => trim($value)));
        }
        break;

    case 'sig_first':
        return array(array('name' => 'sig_first', 'scope' => 'imp', 'value' => $sm_pref_value));
        break;

    case 'signature':
        return array(array('name' => 'signature', 'scope' => 'imp', 'value' => $sm_pref_value));
        break;

    case 'sort_by_ref':
        if ($sm_pref_value == 1) {
            return array(array('name' => 'sortby', 'scope' => 'imp', 'value' => '161'));
        }
        break;

    case 'timezone':
        return array(array('name' => 'timezone', 'scope' => 'horde', 'value' => $sm_pref_value));
        break;

    case 'trash_folder':
        if ($sm_pref_value == '[ ' . _("Do not use Trash") . ' ]') {
            return array(array('name' => 'use_trash', 'scope' => 'imp', 'value' => '0'));
        }
        return array(array('name' => 'use_trash', 'scope' => 'imp', 'value' => '1'),
                     array('name' => 'trash_folder', 'scope' => 'imp', 'value' => $sm_pref_value));
        break;

    case 'unseen_notify':
        if ($sm_pref_value == 2) {
            return array(array('name' => 'nav_poll_all', 'scope' => 'imp', 'value' => false));
        } else if ($sm_pref_value == 3) {
            return array(array('name' => 'nav_poll_all', 'scope' => 'imp', 'value' => true));
        }
        break;

    case 'use_signature':
        if ($sm_pref_value == 0) {
            return array(array('name' => 'signature', 'scope' => 'imp', 'value' => ''));
        }
        break;

    // The rest of the SquirrelMail options do not translate
    default:
        return false;
    }

    // Default to no conversion.
    return false;
}
