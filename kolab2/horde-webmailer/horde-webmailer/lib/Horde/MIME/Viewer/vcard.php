<?php
/**
 * The MIME_Viewer_vcard class renders out vCards in HTML format.
 *
 * $Horde: framework/MIME/MIME/Viewer/vcard.php,v 1.34.10.27 2009-10-09 15:55:19 mrubinsk Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_vcard extends MIME_Viewer {

    /**
     * Render out the vcard contents.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = null)
    {
        global $registry, $prefs, $notification;

        require_once 'Horde/iCalendar.php';

        $app = false;
        $data = $this->mime_part->getContents();
        $html = '';
        $import_msg = null;
        $title = _("vCard");

        $iCal = new Horde_iCalendar();
        if (!$iCal->parsevCalendar($data, 'VCALENDAR',
                                   $this->mime_part->getCharset())) {
            $notification->push(
                _("There was an error reading the contact data."),
                'horde.error');
        }

        if (Util::getFormData('import') &&
            Util::getFormData('source') &&
            $registry->hasMethod('contacts/import')) {
            $source = Util::getFormData('source');
            $count = 0;
            foreach ($iCal->getComponents() as $c) {
                if (is_a($c, 'Horde_iCalendar_vcard')) {
                    $contacts = $registry->call('contacts/import',
                                                array($c, null, $source));
                    if (is_a($contacts, 'PEAR_Error')) {
                        $notification->push(
                            _("There was an error importing the contact data:") . ' '
                            . $contacts->getMessage(),
                            'horde.error');
                        continue;
                    }
                    $count++;
                }
            }
            $notification->push(sprintf(ngettext(
                "%d contact was successfully added to your address book.",
                "%d contacts were successfully added to your address book.",
                $count),
                                        $count),
                                'horde.success');
        }

        $html .= '<table cellspacing="1" border="0" cellpadding="1">';

        $i = 0;
        foreach ($iCal->getComponents() as $vc) {
            if ($i > 0) {
                $html .= '<tr><td colspan="2">&nbsp;</td></tr>';
            }
            ++$i;

            $html .= '<tr><td colspan="2" class="header">';
            $fullname = $vc->getAttributeDefault('FN', false);
            if ($fullname !== false) {
                $html .= $fullname;
            }
            $html .= '</td></tr>';

            $n = $vc->printableName();
            if (!empty($n)) {
                $html .= $this->_row(_("Name"), $n);
            }

            $aliases = $vc->getAttributeValues('ALIAS');
            if (!is_a($aliases, 'PEAR_Error')) {
                $html .= $this->_row(_("Alias"), implode("\n", $aliases));
            }
            $birthdays = $vc->getAttributeValues('BDAY');
            if (!is_a($birthdays, 'PEAR_Error')) {
                require_once 'Horde/Date.php';
                $birthday = new Horde_Date($birthdays[0]);
                $html .= $this->_row(
                    _("Birthday"),
                    $birthday->strftime($prefs->getValue('date_format')));
            }

            $photos = $vc->getAllAttributes('PHOTO');
            foreach ($photos as $photo) {
                if (isset($photo['params']['VALUE']) &&
                    String::upper($photo['params']['VALUE']) == 'URI') {
                    $html .= $this->_row(_("Photo"),
                                         '<img src="' . htmlspecialchars($photo['value']) . '" />',
                                         false);
                } elseif (isset($photo['params']['ENCODING']) &&
                          String::upper($photo['params']['ENCODING']) == 'B' &&
                          isset($photo['params']['TYPE']) &&
                          ($GLOBALS['browser']->hasFeature('dataurl') === true ||
                           $GLOBALS['browser']->hasFeature('dataurl') >= strlen($photo['value']))) {
                    $html .= $this->_row(_("Photo"),
                                         '<img src="data:' . htmlspecialchars($photo['params']['TYPE'] . ';base64,' . $photo['value']) . '" />',
                                         false);
                }
            }

            $labels = $vc->getAllAttributes('LABEL');
            foreach ($labels as $label) {
                if (isset($label['params']['TYPE'])) {
                    if (!is_array($label['params']['TYPE'])) {
                        $label['params']['TYPE'] = array($label['params']['TYPE']);
                    }
                } else {
                    $label['params']['TYPE'] = array_keys($label['params']);
                }
                $types = array();
                foreach ($label['params']['TYPE'] as $type) {
                    switch(String::upper($type)) {
                    case 'HOME':
                        $types[] = _("Home Address");
                        break;
                    case 'WORK':
                        $types[] = _("Work Address");
                        break;
                    case 'DOM':
                        $types[] = _("Domestic Address");
                        break;
                    case 'INTL':
                        $types[] = _("International Address");
                        break;
                    case 'POSTAL':
                        $types[] = _("Postal Address");
                        break;
                    case 'PARCEL':
                        $types[] = _("Parcel Address");
                        break;
                    case 'PREF':
                        $types[] = _("Preferred Address");
                        break;
                    }
                }
                if (!count($types)) {
                    $types = array(_("Address"));
                }
                $html .= $this->_row(implode('/', $types), $label['value']);
            }

            $adrs = $vc->getAllAttributes('ADR');
            foreach ($adrs as $item) {
                if (isset($item['params']['TYPE'])) {
                    if (!is_array($item['params']['TYPE'])) {
                        $item['params']['TYPE'] = array($item['params']['TYPE']);
                    }
                } else {
                    $item['params']['TYPE'] = array_keys($item['params']);
                }
                $address = $item['values'];
                $a = array();
                if (isset($address[VCARD_ADR_STREET])) {
                    $a[] = $address[VCARD_ADR_STREET];
                }
                if (isset($address[VCARD_ADR_LOCALITY])) {
                    $a[] = $address[VCARD_ADR_LOCALITY];
                }
                if (isset($address[VCARD_ADR_REGION])) {
                    $a[] = $address[VCARD_ADR_REGION];
                }
                if (isset($address[VCARD_ADR_POSTCODE])) {
                    $a[] = $address[VCARD_ADR_POSTCODE];
                }
                if (isset($address[VCARD_ADR_COUNTRY])) {
                    $a[] = $address[VCARD_ADR_COUNTRY];
                }
                $types = array();
                foreach ($item['params']['TYPE'] as $type) {
                    switch(String::upper($type)) {
                    case 'HOME':
                        $types[] = _("Home Address");
                        break;
                    case 'WORK':
                        $types[] = _("Work Address");
                        break;
                    case 'DOM':
                        $types[] = _("Domestic Address");
                        break;
                    case 'INTL':
                        $types[] = _("International Address");
                        break;
                    case 'POSTAL':
                        $types[] = _("Postal Address");
                        break;
                    case 'PARCEL':
                        $types[] = _("Parcel Address");
                        break;
                    case 'PREF':
                        $types[] = _("Preferred Address");
                        break;
                    }
                }
                if (!count($types)) {
                    $types = array(_("Address"));
                }
                $html .= $this->_row(implode('/', $types), implode("\n", $a));
            }

            $numbers = $vc->getAllAttributes('TEL');

            foreach ($numbers as $number) {
                if (isset($number['params']['TYPE'])) {
                    if (!is_array($number['params']['TYPE'])) {
                        $number['params']['TYPE'] = array($number['params']['TYPE']);
                    }
                    foreach ($number['params']['TYPE'] as $type) {
                        $number['params'][String::upper($type)] = true;
                    }
                }
                if (isset($number['params']['FAX'])) {
                    $html .= $this->_row(_("Fax"), $number['value']);
                } else {
                    if (isset($number['params']['HOME'])) {
                        $html .= $this->_row(_("Home Phone"),
                                             $number['value']);
                    } elseif (isset($number['params']['WORK'])) {
                        $html .= $this->_row(_("Work Phone"),
                                             $number['value']);
                    } elseif (isset($number['params']['CELL'])) {
                        $html .= $this->_row(_("Cell Phone"),
                                             $number['value']);
                    } else {
                        $html .= $this->_row(_("Phone"),
                                             $number['value']);
                    }
                }
            }

            $addresses = $vc->getAllAttributes('EMAIL');
            $emails = array();
            foreach ($addresses as $address) {
                if (isset($address['params']['TYPE'])) {
                    if (!is_array($address['params']['TYPE'])) {
                        $address['params']['TYPE'] = array($address['params']['TYPE']);
                    }
                    foreach ($address['params']['TYPE'] as $type) {
                        $address['params'][String::upper($type)] = true;
                    }
                }
                $email = '<a href="';
                if ($registry->hasMethod('mail/compose')) {
                    $email .= $registry->call(
                        'mail/compose',
                        array(array('to' => $address['value'])));
                } else {
                    $email .= 'mailto:' . htmlspecialchars($address['value']);
                }
                $email .= '">' . htmlspecialchars($address['value']) . '</a>';
                if (isset($address['params']['PREF'])) {
                    array_unshift($emails, $email);
                } else {
                    $emails[] = $email;
                }
            }

            if (count($emails)) {
                $html .= $this->_row(_("Email"), implode("\n", $emails), false);
            }

            $title = $vc->getAttributeValues('TITLE');
            if (!is_a($title, 'PEAR_Error')) {
                $html .= $this->_row(_("Title"), $title[0]);
            }

            $role = $vc->getAttributeValues('ROLE');
            if (!is_a($role, 'PEAR_Error')) {
                $html .= $this->_row(_("Role"), $role[0]);
            }

            $org = $vc->getAttributeValues('ORG');
            if (!is_a($org, 'PEAR_Error')) {
                $html .= $this->_row(_("Company"), $org[0]);
                if (isset($org[1])) {
                    $html .= $this->_row(_("Department"), $org[1]);
                }
            }

            $notes = $vc->getAttributeValues('NOTE');
            if (!is_a($notes, 'PEAR_Error')) {
                $html .= $this->_row(_("Notes"), $notes[0]);
            }

            $url = $vc->getAttributeValues('URL');
            if (!is_a($url, 'PEAR_Error')) {
                $html .= $this->_row(
                    _("URL"),
                    '<a href="' . htmlspecialchars($url[0])
                        . '" target="_blank">' . htmlspecialchars($url[0])
                        . '</a>',
                    false);
            }
        }

        if ($registry->hasMethod('contacts/import') &&
            $registry->hasMethod('contacts/sources')) {
            $html .= '<tr><td colspan="2" class="smallheader"><form action="'
                . Horde::selfUrl() . '" method="get" name="vcard_import">'
                . Util::formInput();
            foreach ($_GET as $key => $val) {
                $html .= '<input type="hidden" name="' . htmlspecialchars($key)
                    . '" value="' . htmlspecialchars($val) . '" />';
            }

            $sources = $registry->call('contacts/sources', array(true));
            if (count($sources) > 1) {
                $html .=
                    '<input type="submit" class="button" name="import" value="'
                    . _("Add to address book:") . '" />'
                    . '<label for="add_source" class="hidden">'
                    . _("Address Book") . '</label>'
                    . '<select id="add_source" name="source">';
                foreach ($sources as $key => $label) {
                    $selected = ($key == $prefs->getValue('add_source'))
                        ? ' selected="selected"' : '';
                    $html .= '<option value="' . htmlspecialchars($key) . '"'
                        . $selected . '>' . htmlspecialchars($label)
                        . '</option>';
                }
            } else {
                reset($sources);
                $html .=
                    '<input type="submit" class="button" name="import" value="'
                    . _("Add to my address book") . '" />'
                    . '<input type="hidden" name="source" value="'
                    . htmlspecialchars(key($sources)) . '" />';
            }

            $html .= '</form></td></tr><tr><td>&nbsp;</td></tr>';
        }

        $html .=  '</table>';

        return
            Util::bufferOutput(
                'include',
                $registry->get('templates', 'horde') . '/common-header.inc')
            . Util::bufferOutput(array($notification, 'notify'),
                                 array('listeners' => 'status'))
            . $html
            . Util::bufferOutput(
                'include',
                $registry->get('templates', 'horde') . '/common-footer.inc');
    }

    function _row($label, $value, $encode = true)
    {
        if ($encode) {
            $label = htmlspecialchars($label);
            $value = htmlspecialchars($value);
        }
        return '<tr><td class="item" valign="top">' . $label
            . '</td><td class="item" valign="top">' . nl2br($value)
            . "</td></tr>\n";
    }

    /**
     * Return the MIME content type of the rendered content.
     *
     * @return string  The content type of the output.
     */
    function getType()
    {
        return 'text/html; charset=' . NLS::getCharset();
    }

}
