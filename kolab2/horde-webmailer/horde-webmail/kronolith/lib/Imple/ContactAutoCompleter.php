<?php
/**
 * $Horde: kronolith/lib/Imple/ContactAutoCompleter.php,v 1.3.2.4 2009-03-30 17:24:03 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Kronolith
 */

/** Horde_MIME */
require_once 'Horde/MIME.php';

/**
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Kronolith
 */
class Imple_ContactAutoCompleter extends Imple {

    /**
     * onShow javascript code.
     *
     * @var string
     */
    var $_onshow = ', onShow: function(e, u){ if(!u.style.position || u.style.position==\'absolute\') { u.style.position = \'absolute\'; Position.clone(e, u, { setHeight: false, offsetTop: e.offsetHeight }); } u.style.zIndex = 2; Effect.Appear(u,{duration:0.15, beforeSetup:function(effect) { effect.element.setOpacity(effect.options.from); effect.element.show(); u.style.height = Math.min(u.offsetHeight, ((window.innerHeight ? window.innerHeight : document.body.clientHeight) - Position.page(e)[1] - e.offsetHeight - 10)) + \'px\'; u.style.overflow = \'auto\'; } }); }';

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
        $url = Horde::url($GLOBALS['registry']->get('webroot', 'kronolith') . '/imple.php?imple=ContactAutoCompleter/input=' . rawurlencode($this->_params['triggerId']), true);
        Kronolith::addInlineScript('Event.observe(window, "load", function() { new Ajax.Autocompleter("' . $this->_params['triggerId'] . '", "' . $this->_params['resultsId'] . '", "' . $url . '", { tokens: ",", indicator: "' . $this->_params['triggerId'] . '_loading_img"' . $this->_onshow . ', afterUpdateElement: function(f, t) { if (f.value.lastIndexOf(";") != (f.value.length - 1)) { f.value += ", "; } } }); });');
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
            !($input = Util::getFormData($args['input']))) {
            return '<ul></ul>';
        }

        $results = $this->expandAddresses($input, true);
        if (is_a($results, 'PEAR_Error')) {
            // TODO: error handling
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

    /**
     * Uses the Registry to expand names and returning error information for
     * any address that is either not valid or fails to expand.
     *
     * @param string $addrString  The name(s) or address(es) to expand.
     * @param boolean $full       If true generate a full, rfc822-valid address
     *                            list.
     *
     * @return mixed   Either a string containing all expanded addresses or an
     *                 array containing all matching address or an error
     *                 object.
     */
    function expandAddresses($addrString, $full = false)
    {
        if (!preg_match('|[^\s]|', $addrString)) {
            return '';
        }

        $search_fields = array();

        $src = explode("\t", $GLOBALS['prefs']->getValue('search_sources'));
        if ((count($src) == 1) && empty($src[0])) {
            $src = array();
        }

        if (($val = $GLOBALS['prefs']->getValue('search_fields'))) {
            $field_arr = explode("\n", $val);
            foreach ($field_arr as $field) {
                $field = trim($field);
                if (!empty($field)) {
                    $tmp = explode("\t", $field);
                    if (count($tmp) > 1) {
                        $source = array_splice($tmp, 0, 1);
                        $search_fields[$source[0]] = $tmp;
                    }
                }
            }
        }

        $arr = array_filter(array_map('trim', MIME::rfc822Explode($addrString, ',')));

        $results = $GLOBALS['registry']->call('contacts/search', array($arr, $src, $search_fields, true));
        if (is_a($results, 'PEAR_Error')) {
            return $results;
        }

        /* Remove any results with empty email addresses. */
        foreach (array_keys($results) as $key) {
            for ($i = 0, $subTotal = count($results[$key]); $i < $subTotal; ++$i) {
                if (empty($results[$key][$i]['email'])) {
                    unset($results[$key][$i]);
                }
            }
        }

        $ambiguous = $error = false;
        $missing = array();
        $vars = null;

        require_once 'Mail/RFC822.php';
        $parser = new Mail_RFC822(null, '@INVALID');

        foreach ($arr as $i => $tmp) {
            $address = MIME::encodeAddress($tmp, null, '');
            if (!is_a($address, 'PEAR_Error') &&
                ($parser->validateMailbox($address) ||
                 $parser->_isGroup($address))) {
                // noop
            } elseif (!isset($results[$tmp]) || !count($results[$tmp])) {
                /* Handle the missing/invalid case - we should return error
                 * info on each address that couldn't be
                 * expanded/validated. */
                $error = true;
                if (!$ambiguous) {
                    $arr[$i] = PEAR::raiseError(null, null, null, null, $arr[$i]);
                    $missing[$i] = $arr[$i];
                }
            } else {
                $res = $results[$tmp];
                if (count($res) == 1) {
                    if ($full) {
                        if (strpos($res[0]['email'], ',') !== false) {
                            if ($vars === null) {
                                $vars = get_class_vars('MIME');
                            }
                            $arr[$i] = MIME::_rfc822Encode($res[0]['name'], $vars['rfc822_filter'] . '.') . ': ' . $res[0]['email'] . ';';
                        } else {
                            list($mbox, $host) = explode('@', $res[0]['email']);
                            $arr[$i] = MIME::rfc822WriteAddress($mbox, $host, $res[0]['name']);
                        }
                    } else {
                        $arr[$i] = $res[0]['email'];
                    }
                } else {
                    /* Handle the multiple case - we return an array
                     * with all found addresses. */
                    $arr[$i] = array($arr[$i]);
                    foreach ($res as $one_res) {
                        if (empty($one_res['email'])) {
                            continue;
                        }
                        if ($full) {
                            if (strpos($one_res['email'], ',') !== false) {
                                if ($vars === null) {
                                    $vars = get_class_vars('MIME');
                                }
                                $arr[$i][] = MIME::_rfc822Encode($one_res['name'], $vars['rfc822_filter'] . '.') . ': ' . $one_res['email'] . ';';
                            } else {
                                $mbox_host = explode('@', $one_res['email']);
                                if (isset($mbox_host[1])) {
                                    $arr[$i][] = MIME::rfc822WriteAddress($mbox_host[0], $mbox_host[1], $one_res['name']);
                                }
                            }
                        } else {
                            $arr[$i][] = $one_res['email'];
                        }
                    }
                    $ambiguous = true;
                }
            }
        }

        if ($ambiguous) {
            foreach ($missing as $i => $addr) {
                $arr[$i] = $addr->getUserInfo();
            }
            return $arr;
        } elseif ($error) {
            return PEAR::raiseError(_("Please resolve ambiguous or invalid addresses."), null, null, null, $arr);
        } else {
            $list = '';
            foreach ($arr as $elm) {
                if (substr($list, -1) == ';') {
                    $list .= ' ';
                } elseif (!empty($list)) {
                    $list .= ', ';
                }
                $list .= $elm;
            }
            return $list;
        }
    }

}
