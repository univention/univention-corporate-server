<?php
/**
 * @package Turba
 *
 * $Horde: turba/lib/Forms/EditContact.php,v 1.6.2.5 2008-08-12 22:05:57 jan Exp $
 */

/** Turba_ContactForm */
require_once dirname(__FILE__) . '/Contact.php';

/**
 * @package Turba
 */
class Turba_EditContactForm extends Turba_ContactForm {

    var $_source;
    var $_contact;

    function Turba_EditContactForm(&$vars, &$contact)
    {
        global $conf;

        parent::Horde_Form($vars, '', 'Turba_View_EditContact');
        $this->_contact = &$contact;

        $this->setButtons(_("Save"));
        $this->addHidden('', 'url', 'text', false);
        $this->addHidden('', 'source', 'text', true);
        $this->addHidden('', 'key', 'text', false);

        parent::_addFields($this->_contact);

        if ($conf['documents']['type'] != 'none') {
            $this->addVariable(_("Add file"), 'vfs', 'file', false);
        }

        $object_values = $vars->get('object');
        $object_keys = array_keys($contact->attributes);
        foreach ($object_keys as $info_key) {
            if (!isset($object_values[$info_key])) {
                $object_values[$info_key] = $contact->getValue($info_key);
            }
        }
        $vars->set('object', $object_values);
        $vars->set('source', $contact->getSource());
    }

    function getSource()
    {
        return $this->_source;
    }

    function execute()
    {
        global $conf, $notification;

        if (!$this->validate($this->_vars)) {
            return PEAR::raiseError('Invalid');
        }

        /* Form valid, save data. */
        $this->getInfo($this->_vars, $info);

        /* Update the contact. */
        foreach ($info['object'] as $info_key => $info_val) {
            if ($info_key != '__key') {
                if ($GLOBALS['attributes'][$info_key]['type'] == 'image' && !empty($info_val['file'])) {
                    $this->_contact->setValue($info_key, file_get_contents($info_val['file']));
                    if (isset($info_val['type'])) {
                        $this->_contact->setValue($info_key . 'type', $info_val['type']);
                    }
                } else {
                    $this->_contact->setValue($info_key, $info_val);
                }
            }
        }

        $result = $this->_contact->store();
        if (!is_a($result, 'PEAR_Error')) {
            if ($conf['documents']['type'] != 'none' && isset($info['vfs'])) {
                $result = $this->_contact->addFile($info['vfs']);
                if (is_a($result, 'PEAR_Error')) {
                    $notification->push(sprintf(_("\"%s\" updated, but saving the uploaded file failed: %s"), $this->_contact->getValue('name'), $result->getMessage()), 'horde.warning');
                } else {
                    $notification->push(sprintf(_("\"%s\" updated."), $this->_contact->getValue('name')), 'horde.success');
                }
            } else {
                $notification->push(sprintf(_("\"%s\" updated."), $this->_contact->getValue('name')), 'horde.success');
            }
            return true;
        } else {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            $notification->push(_("There was an error saving the contact. Contact your system administrator for further help."), 'horde.error');
            return $result;
        }
    }

}

/**
 * @package Turba
 */
class Turba_EditContactGroupForm extends Turba_EditContactForm {

    function Turba_EditContactGroupForm(&$vars, &$contact)
    {
        $this->addHidden('', 'objectkeys', 'text', false);
        $this->addHidden('', 'original_source', 'text', false);
        $this->addHidden('', 'actionID', 'text', false);

        parent::Turba_EditContactForm($vars, $contact);
        $vars->set('actionID', 'groupedit');

        $objectkeys = $vars->get('objectkeys');
        $source = $vars->get('source');
        $key = $vars->get('key');
        if ($source . ':' . $key == $objectkeys[0]) {
            /* First contact */
            $this->setButtons(_("Next"));
        } elseif ($source . ':' . $key == $objectkeys[count($objectkeys) - 1]) {
            /* Last contact */
            $this->setButtons(_("Previous"));
        } else {
            /* In between */
            $this->setButtons(_("Previous"));
            $this->appendButtons(_("Next"));
        }
        $this->appendButtons(_("Finish"));
    }

    function renderActive($renderer, &$vars, $action, $method)
    {
        parent::renderActive($renderer, $vars, $action, $method);

        /* Read the columns to display from the preferences. */
        $source = $vars->get('source');
        $sources = Turba::getColumns();
        $columns = isset($sources[$source]) ? $sources[$source] : array();

        require_once TURBA_BASE . '/lib/List.php';
        require_once TURBA_BASE . '/lib/ListView.php';
        $results = new Turba_List($vars->get('objectkeys'));
        $listView = new Turba_ListView($results, array('Group' => true), $columns);
        echo '<br />' . $listView->getPage($numDisplayed);
    }

    function execute()
    {
        $result = parent::execute();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->getInfo($this->_vars, $info);

        $next_page = Horde::applicationUrl('edit.php', true);
        $next_page = Util::addParameter($next_page,
                                        array('source' => $info['source'],
                                              'original_source' => $info['original_source'],
                                              'objectkeys' => $info['objectkeys'],
                                              'url' => $info['url'],
                                              'actionID' => 'groupedit'),
                                        null, false);
        $objectkey = array_search($info['source'] . ':' . $info['key'], $info['objectkeys']);

        $submitbutton = $this->_vars->get('submitbutton');
        if ($submitbutton == _("Finish")) {
            $next_page = Horde::url('browse.php', true);
            if ($info['original_source'] == '**search') {
                $next_page = Util::addParameter($next_page, 'key', $info['original_source'], false);
            } else {
                $next_page = Util::addParameter($next_page, 'source', $info['original_source'], false);
            }
        } elseif ($submitbutton == _("Previous") && $info['source'] . ':' . $info['key'] != $info['objectkeys'][0]) {
            /* Previous contact */
            list(, $previous_key) = explode(':', $info['objectkeys'][$objectkey - 1]);
            $next_page = Util::addParameter($next_page, 'key', $previous_key, false);
            if ($this->getOpenSection()) {
                $next_page = Util::addParameter($next_page, '__formOpenSection', $this->getOpenSection(), false);
            }
        } elseif ($submitbutton == _("Next") &&
                  $info['source'] . ':' . $info['key'] != $info['objectkeys'][count($info['objectkeys']) - 1]) {
            /* Next contact */
            list(, $next_key) = explode(':', $info['objectkeys'][$objectkey + 1]);
            $next_page = Util::addParameter($next_page, 'key', $next_key, false);
            if ($this->getOpenSection()) {
                $next_page = Util::addParameter($next_page, '__formOpenSection', $this->getOpenSection(), false);
            }
        }

        header('Location: ' . $next_page);
        exit;
    }

}
