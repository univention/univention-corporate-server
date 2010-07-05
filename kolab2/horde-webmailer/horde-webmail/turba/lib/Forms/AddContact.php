<?php
/**
 * @package Turba
 *
 * $Horde: turba/lib/Forms/AddContact.php,v 1.9.2.3 2008-10-25 01:36:42 chuck Exp $
 */

/** Turba_ContactForm */
require_once dirname(__FILE__) . '/Contact.php';

/**
 * @package Turba
 */
class Turba_AddContactForm extends Turba_ContactForm {

    var $_contact = null;

    function Turba_AddContactForm(&$vars, &$contact)
    {
        global $addSources, $notification;

        parent::Horde_Form($vars, _("Add Contact"));
        $this->_contact = &$contact;

        $this->setButtons(_("Add"));
        $this->addHidden('', 'url', 'text', false);
        $this->addHidden('', 'key', 'text', false);

        /* Check if a source selection box is required. */
        if (count($addSources) > 1) {
            /* Multiple sources, show a selection box. */
            $options = array();
            foreach ($addSources as $key => $config) {
                $options[$key] = $config['title'];
            }
            $v = &$this->addVariable(_("Choose an address book"), 'source', 'enum', true, false, null, array($options, true));
            $action = Horde_Form_Action::factory('submit');
            $v->setAction($action);
            $v->setOption('trackchange', true);
            if (is_null($vars->get('formname')) &&
                $vars->get($v->getVarName()) != $vars->get('__old_' . $v->getVarName())) {
                $notification->push(sprintf(_("Selected address book \"%s\"."), $addSources[$vars->get('source')]['title']), 'horde.message');
            }
        } else {
            /* One source, no selection box but store the value in a
             * hidden field. */
            $this->addHidden('', 'source', 'text', true);
        }

        if ($this->_contact) {
            parent::_addFields($this->_contact);
        }
    }

    function validate()
    {
        if (!$this->_vars->get('source')) {
            return false;
        }
        return parent::validate($this->_vars);
    }

    function execute()
    {
        global $driver, $notification;

        /* Form valid, save data. */
        $this->getInfo($this->_vars, $info);
        $source = $info['source'];
        foreach ($info['object'] as $info_key => $info_val) {
            if ($GLOBALS['attributes'][$info_key]['type'] == 'image' && !empty($info_val['file'])) {
                $this->_contact->setValue($info_key, file_get_contents($info_val['file']));
                $this->_contact->setValue($info_key . 'type', $info_val['type']);
            } else {
                $this->_contact->setValue($info_key, $info_val);
            }
        }
        $contact = $this->_contact->attributes;
        unset($contact['__owner']);

        /* Create Contact. */
        $key = $driver->add($contact);
        if (is_a($key, 'PEAR_Error')) {
            Horde::logMessage($key, __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            // Try 3 times to get the new entry. We retry to allow setups like
            // LDAP replication to work.
            for ($i = 0; $i < 3; $i++) {
                $ob = $driver->getObject($key);
                if (!is_a($ob, 'PEAR_Error')) {
                    $notification->push(sprintf(_("%s added."), $ob->getValue('name')), 'horde.success');
                    header('Location: ' . (!empty($info['url']) ? $info['url'] : $ob->url('Contact', true)));
                    exit;
                }
                sleep(1);
            }
            Horde::logMessage($ob, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        $notification->push(_("There was an error adding the new contact. Contact your system administrator for further help."), 'horde.error');
    }

}
