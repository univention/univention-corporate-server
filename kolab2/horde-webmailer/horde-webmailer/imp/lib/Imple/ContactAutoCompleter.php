<?php
/**
 * $Horde: imp/lib/Imple/ContactAutoCompleter.php,v 1.24.2.8 2009-01-06 15:24:08 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class Imple_ContactAutoCompleter extends Imple {

    /**
     * Constructor.
     *
     * @param array $params  Configuration parameters.
     * <pre>
     * 'triggerId' => TODO (optional)
     * 'resultsId' => TODO (optional)
     * </pre>
     */
    function Imple_ContactAutoCompleter($params)
    {
        if (empty($params['triggerId'])) {
            $params['triggerId'] = $this->_randomid();
        }
        if (empty($params['resultsId'])) {
            $params['resultsId'] = $params['triggerId'] . '_results';
        }

        parent::Imple($params);
    }

    /**
     * Attach the Imple object to a javascript event.
     */
    function attach()
    {
        parent::attach();
        Horde::addScriptFile('autocomplete.js', 'imp', true);
        $url = Horde::url($GLOBALS['registry']->get('webroot', 'imp') . '/imple.php?imple=ContactAutoCompleter/input=' . rawurlencode($this->_params['triggerId']), true);
        IMP::addInlineScript('new Ajax.Autocompleter("' . $this->_params['triggerId'] . '", "' . $this->_params['resultsId'] . '", "' . $url . '", { tokens: [",", ";"], indicator: "' . $this->_params['triggerId'] . '_loading_img", afterUpdateElement: function(f, t) { if (!f.value.endsWith(";")) { f.value += ","; } f.value += " "; } });', 'dom');
    }

    /**
     * TODO
     *
     * @param array $args  TODO
     *
     * @return string  TODO
     */
    function handle($args)
    {
        // Avoid errors if 'input' isn't set and short-circuit empty searches.
        if (empty($args['input']) ||
            !($input = Util::getPost($args['input']))) {
            return '<ul></ul>';
        }

        require_once IMP_BASE . '/lib/Compose.php';
        $results = IMP_Compose::expandAddresses($input, true, false);
        if (empty($results) || is_a($results, 'PEAR_Error')) {
            /* @TODO: error handling */
            return '<ul></ul>';
        }

        if (is_array($results)) {
            $results = $results[0];
            array_shift($results);
        } else {
            $results = array($results);
        }

        $html = '<ul>';
        $input = htmlspecialchars($input);
        $input_regex = '/(' . preg_quote($input, '/')  . ')/i';
        foreach ($results as $result) {
            $html .= '<li>' . str_replace(array('&lt;strong&gt;', '&lt;/strong&gt;'),
                                          array('<strong>', '</strong>'),
                                          htmlspecialchars(preg_replace($input_regex, '<strong>$1</strong>', $result))) . '</li>';
        }
        return $html . '</ul>';
    }

}
