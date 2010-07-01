<?php

$block_name = _("EU VAT identification");

/**
 * @package Horde_Block
 */
class Horde_Block_Horde_vatid extends Horde_Block {

    var $_app = 'horde';

    /**
     * The title to go in this block.
     *
     * @return string  The title text.
     */
    function _title()
    {
        return _("VAT id number verification");
    }

    /**
     * The content to go in this block.
     *
     * @return string  The content.
     */
    function _content()
    {
        $vatid = str_replace(' ', '', Util::getFormData('vatid', ''));
        $block_name = 'block_' . $this->_row . '_' . $this->_col;
        $name = 'horde_' . $block_name;

        $html = '<form style="padding:2px" method="post" action="'
            . Horde::selfUrl() . '#' . $name . '" id="' . $name
            . '" onsubmit="$(\'' . $name
            . '_loader\').show();var response=Form.request(\'' . $name
            . '\',{onSuccess:function(){if(response.success()){$(\''
            . $block_name . '\').update(response.transport.responseText);$(\''
            . $block_name . '\').scrollTo();}},parameters:{httpclient:1,row:'
            . $this->_row . ',col:' . $this->_col . '}});return false">'
            . Util::formInput()
            . Horde::label('vatid', _("VAT identification number:"))
            . '<br /><input type="text" length="14" name="vatid" value="'
            . htmlspecialchars($vatid) . '" />'
            . '<br /><input type="submit" id="vatbutton" value="' . _("Check")
            . '" class="button" /> '
            . Horde::img('loading.gif', _("Checking"), array('id' => $name . '_loader', 'style' => 'display:none'))
            . '</form>';

        if (!empty($vatid) &&
            !preg_match('/^([A-Z]{2})([0-9A-Za-z\+\*\.]{2,12})$/', $vatid, $matches)) {
            $html .= '<br />' . $this->_error(_("Invalid VAT identification number format."));
        }

        if (!empty($matches)) {
            $html .= '<br />';
            @include_once 'SOAP/Client.php';
            if (!class_exists('SOAP_Client')) {
                $html .= $this->_error(sprintf(_("%s not found."), '<a href="http://pear.php.net/SOAP" target="_blank">SOAP</a>'));
            } else {
                $client = new SOAP_Client('http://ec.europa.eu/taxation_customs/vies/api/checkVatPort?wsdl', true, false, array(), Horde::getTempDir());
                $params = array('countryCode' => $matches[1], 'vatNumber' => $matches[2]);
                $result = $client->call('checkVat', $params);
                if (is_a($result, 'SOAP_Fault')) {
                    $error = $result->getMessage();
                    switch (true) {
                    case strpos($error, 'INVALID_INPUT'):
                        $error = _("The provided country code is invalid.");
                        break;
                    case strpos($error, 'SERVICE_UNAVAILABLE'):
                        $error = _("The service is currently not available. Try again later.");
                        break;
                    case strpos($error, 'MS_UNAVAILABLE'):
                        $error = _("The member state service is currently not available. Try again later or with a different member state.");
                        break;
                    case strpos($error, 'TIMEOUT'):
                        $error = _("The member state service could not be reached in time. Try again later or with a different member state.");
                        break;
                    case strpos($error, 'SERVER_BUSY'):
                        $error = _("The service is currently too busy. Try again later.");
                        break;
                    }
                    $html .= $this->_error($error);
                } else {
                    if ($result['valid']) {
                        $html .= '<span style="color:green;font-weight:bold">'
                            . _("This VAT identification number is valid.")
                            . '</span><br />';
                    } else {
                        $html .= $this->_error(_("This VAT identification number is invalid.")) . '<br />';
                    }
                    $html .= '<em>' . _("Country") . ':</em> '
                        . $result['countryCode'] . '<br /><em>'
                        . _("VAT number") . ':</em> ' . $result['vatNumber']
                        . '<br /><em>' . _("Date") . ':</em> '
                        . strftime($GLOBALS['prefs']->getValue('date_format'), strtotime($result['requestDate']))
                        . '<br />';
                    if (!empty($result['name'])) {
                        $html .= '<em>' . _("Name") . ':</em> ' . $result['name'] . '<br />';
                    }
                    if (!empty($result['address'])) {
                        $html .= '<em>' . _("Address") . ':</em> ' . $result['address'] . '<br />';
                    }
                }
            }
        }

        return $html;
    }

    function _error($text)
    {
        return '<span style="color:red;font-weight:bold">' . $text . '</span>';
    }

}
