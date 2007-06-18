<?php
/**
 * The MIME_Viewer_vcard class renders out vCards in HTML format.
 *
 * $Horde: framework/MIME/MIME/Viewer/vcard.php,v 1.26 2004/04/07 14:43:10 chuck Exp $
 *
 * Copyright 2002-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_vcard extends MIME_Viewer {

    /**
     * Render out the vcard contents.
     *
     * @access public
     *
     * @param optional array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = null)
    {
        global $registry, $prefs;

        require_once 'Horde/Data.php';

        $app = false;
        $data = $this->mime_part->getContents();
        $html = '';
        $import_msg = null;
        $title = _("vCard");
        $vc = &Horde_Data::singleton('vcard');

        $vc->importData($data);

        if (Util::getFormData('import') &&
            Util::getFormData('source') &&
            $registry->hasMethod('contacts/import_vcard')) {
            $source = Util::getFormData('source');
            $contacts = $registry->call('contacts/import_vcard', array($source, $data));
            if (is_a($contacts, 'PEAR_Error')) {
                $import_msg = _("There was an error importing the contact data.");
            } else {
                $import_msg = _("This contact data has been successfully added to your address book. Click below to view:");
                $import_msg .= '</td></tr>';
                foreach ($contacts as $contactID => $name) {
                    $url = Horde::url($registry->link('contacts/show', array('source' => $source, 'key' => $contactID)));
                    $import_msg .= '<tr><td class="item" colspan="2">';
                    $import_msg .= Horde::link($url, $name, null, '_blank') . Horde::img('mime/vcard.gif', $name, null, $registry->getParam('graphics', 'horde')) . '&nbsp;' . $name . '</a><br />';
                    $import_msg .= '</td></tr>';
                }
            }
        }

        $html  = Util::bufferOutput('include', $registry->getParam('templates', 'horde') . '/common-header.inc');
        $html .= '<table cellspacing="1" border="0" cellpadding="1">';
        if (!is_null($import_msg)) {
            $html .= '<tr><td colspan="2" class="header">' . $import_msg . '</td></tr><tr><td>&nbsp;</td></tr>';
        } elseif ($registry->hasMethod('contacts/import_vcard') &&
                  $registry->hasMethod('contacts/sources')) {
            $html .= '<tr><td colspan="2" class="header"><form action="' . $_SERVER['PHP_SELF'] . '" method="get" name="import_vcard">' . Util::formInput();
            foreach ($_GET as $key => $val) {
                $html .= '<input type="hidden" name="' . htmlspecialchars($key) . '" value="' . htmlspecialchars($val) . '" />';
            }
            $html .= '<input type="submit" class="button" name="import" value="' . _("Add to my address book:") . '" />';
            $html .= '<select name="source">';
            foreach ($registry->call('contacts/sources', array(true)) as $key => $label) {
                $selected = ($key == $prefs->getValue('add_source')) ? ' selected="selected"' : '';
                $html .= '<option value="' . htmlspecialchars($key) . '"' . $selected . '>' . htmlspecialchars($label) . '</option>';
            }
            $html .= '</form></td></tr><tr><td>&nbsp;</td></tr>';
        }

        for ($i = 0; $i < count($vc->count()); $i++) {
            if ($i > 0) {
                $html .= '<tr><td>&nbsp;</td></tr>';
            }

            $html .= '<tr><td colspan="2" class="header">';
            $fullname = $vc->getValues('FN', $i);
            if (array_key_exists(0, $fullname)) {
                $html .= $fullname[0]['value'];
            }
            $html .= '</td></tr>';

            $name = $vc->getValues('N', $i);
            $name_arr = array();
            if (array_key_exists(0, $name)) {
                $name_parts = explode(';', $name[0]['value']);
                if (isset($name_parts[3])) {
                    $name_arr[] = $name_parts[3];
                }
                if (isset($name_parts[1])) {
                    $name_arr[] = $name_parts[1];
                }
                if (isset($name_parts[2])) {
                    $name_arr[] = $name_parts[2];
                }
                if (isset($name_parts[0])) {
                    $name_arr[] = $name_parts[0];
                }
                if (isset($name_parts[4])) {
                    $name_arr[] = $name_parts[4];
                }
            }

            $html .= $this->_row(_("Name"), implode(' ', $name_arr));

            $aliases = $vc->getValues('ALIAS', $i);
            if (count($aliases)) {
                $alias_arr = array();
                foreach ($aliases as $alias) {
                    $alias_arr[] = $alias['value'];
                }
                $html .= $this->_row(_("Alias"), implode('<br />', $alias_arr));
            }

            $birthdays = $vc->getValues('BDAY', $i);
            if (count($birthdays)) {
                include_once 'Date/Calc.php';
                $birthday = $vc->mapDate($birthdays[0]['value']);
                $html .= $this->_row(_("Birthday"), Date_Calc::dateFormat($birthday['mday'], $birthday['month'], $birthday['year'], '%Y-%m-%d'));
            }

            $labels = $vc->getValues('LABEL', $i);
            foreach ($labels as $label) {
                if (isset($label['params']['TYPE'])) {
                    foreach ($label['params']['TYPE'] as $type) {
                        $label['params'][String::upper($type)] = true;
                    }
                }
                if (isset($label['params']['HOME'])) {
                    $html .= $this->_row(_("Home Address"), nl2br($label['value']));
                } elseif (isset($label['params']['WORK'])) {
                    $html .= $this->_row(_("Work Address"), nl2br($label['value']));
                } else {
                    $html .= $this->_row(_("Address"), nl2br($label['value']));
                }
            }

            $numbers = $vc->getValues('TEL', $i);
            foreach ($numbers as $number) {
                if (isset($number['params']['TYPE'])) {
                    foreach ($number['params']['TYPE'] as $type) {
                        $number['params'][String::upper($type)] = true;
                    }
                }
                if (isset($number['params']['VOICE'])) {
                    if (isset($number['params']['HOME'])) {
                        $html .= $this->_row(_("Home Phone"), $number['value']);
                    } elseif (isset($number['params']['WORK'])) {
                        $html .= $this->_row(_("Work Phone"), $number['value']);
                    } elseif (isset($number['params']['CELL'])) {
                        $html .= $this->_row(_("Cell Phone"), $number['value']);
                    } else {
                        $html .= $this->_row(_("Phone"), $number['value']);
                    }
                } elseif (isset($number['params']['FAX'])) {
                    $html .= $this->_row(_("Fax"), $number['value']);
                }
            }

            $addresses = $vc->getValues('EMAIL', $i);
            $emails = array();
            foreach ($addresses as $address) {
                if (isset($address['params']['TYPE'])) {
                    foreach ($address['params']['TYPE'] as $type) {
                        $address['params'][String::upper($type)] = true;
                    }
                }
                $email = '<a href="';
                if ($registry->hasMethod('mail/compose')) {
                    $email .= $registry->call('mail/compose', array(array('to' => $address['value'])));
                } else {
                    $email .= 'mailto:' . $address['value'];
                }
                $email .= '">' . $address['value'] . '</a>';
                if (isset($address['params']['PREF'])) {
                    array_unshift($emails, $email);
                } else {
                    array_push($emails, $email);
                }
            }
            if (count($emails)) {
                $html .= $this->_row(_("Email"), implode('<br />', $emails));
            }

            $title = $vc->getValues('TITLE', $i);
            if (count($title)) {
                $html .= $this->_row(_("Title"), $title[0]['value']);
            }

            $role = $vc->getValues('ROLE', $i);
            if (count($role)) {
                $html .= $this->_row(_("Role"), $role[0]['value']);
            }

            $org = $vc->getValues('ORG', $i);
            if (count($org)) {
                $html .= $this->_row(_("Company"), $org[0]['value']);
            }

            $notes = $vc->getValues('NOTE', $i);
            if (count($notes)) {
                $html .= $this->_row(_("Notes"), nl2br($notes[0]['value']));
            }

            $url = $vc->getValues('URL', $i);
            if (count($url)) {
                $html .= $this->_row(_("URL"), '<a href="' . $url[0]['value'] . '" target="_blank">' . $url[0]['value'] . '</a>');
            }

            $html .= '</table>';
        }

        $html .= Util::bufferOutput('include', $registry->getParam('templates', 'horde') . '/common-footer.inc');

        return $html;
    }

    function _row($label, $value)
    {
        return '<tr><td class="item" valign="top">' . $label . '</td><td class="item" valign="top">' . $value . "</td></tr>\n";
    }

    /**
     * Return the MIME content type of the rendered content.
     *
     * @access public
     *
     * @return string  The content type of the output.
     */
    function getType()
    {
        return 'text/html';
    }

}
