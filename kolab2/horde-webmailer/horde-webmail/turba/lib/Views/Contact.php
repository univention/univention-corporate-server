<?php
/**
 * @package Turba
 */

/** Turba_ContactForm */
require_once TURBA_BASE . '/lib/Forms/Contact.php';

/**
 * The Turba_View_Contact:: class provides an API for viewing events.
 *
 * $Horde: turba/lib/Views/Contact.php,v 1.16.2.2 2008-02-29 04:38:11 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Turba 2.2
 * @package Turba
 */
class Turba_View_Contact {

    /**
     * @var Turba_Object
     */
    var $contact;

    /**
     * @var boolean
     */
    var $print = false;

    /**
     * @param Turba_Object &$contact
     */
    function Turba_View_Contact(&$contact, $print = null)
    {
        $this->contact = &$contact;
        if (!is_null($print)) {
            $this->print = $print;
        }

        /* Set print link. */
        if (!$this->print) {
            $GLOBALS['print_link'] = Util::addParameter($this->contact->url(), 'print', 1);
        }
    }

    function getTitle()
    {
        if (!$this->contact || is_a($this->contact, 'PEAR_Error')) {
            return _("Not Found");
        }
        return $this->contact->getValue('name');
    }

    function html($active = true)
    {
        global $conf, $prefs, $registry;

        if (!$this->contact || is_a($this->contact, 'PEAR_Error') || !$this->contact->hasPermission(PERMS_READ)) {
            echo '<h3>' . _("The requested contact was not found.") . '</h3>';
            return;
        }

        $vars = new Variables();
        $form = &new Turba_ContactForm($vars, $this->contact);
        $userId = Auth::getAuth();

        /* Get the contact's history. */
        if ($this->contact->getValue('__uid')) {
            $history = &Horde_History::singleton();
            $log = $history->getHistory($this->contact->getGuid());
            if ($log && !is_a($log, 'PEAR_Error')) {
                foreach ($log->getData() as $entry) {
                    switch ($entry['action']) {
                    case 'add':
                        if ($userId != $entry['who']) {
                            $createdby = sprintf(_("by %s"), Turba::getUserName($entry['who']));
                        } else {
                            $createdby = _("by me");
                        }
                        $v = &$form->addVariable(_("Created"), 'object[__created]', 'text', false, false);
                        $v->disable();
                        $vars->set('object[__created]', strftime($prefs->getValue('date_format'), $entry['ts']) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $entry['ts']) . ' ' . @htmlspecialchars($createdby, ENT_COMPAT, NLS::getCharset()));
                        break;

                    case 'modify':
                        if ($userId != $entry['who']) {
                            $modifiedby = sprintf(_("by %s"), Turba::getUserName($entry['who']));
                        } else {
                            $modifiedby = _("by me");
                        }
                        $v = &$form->addVariable(_("Last Modified"), 'object[__modified]', 'text', false, false);
                        $v->disable();
                        $vars->set('object[__modified]', strftime($prefs->getValue('date_format'), $entry['ts']) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $entry['ts']) . ' ' . @htmlspecialchars($modifiedby, ENT_COMPAT, NLS::getCharset()));
                        break;
                    }
                }
            }
        }

        echo '<div id="Contact"' . ($active ? '' : ' style="display:none"') . '>';
        $form->renderInactive(new Horde_Form_Renderer(), $vars);

        /* Comments. */
        if (!empty($conf['comments']['allow']) && $registry->hasMethod('forums/doComments')) {
            $comments = $registry->call('forums/doComments', array('turba', $this->contact->driver->name . '.' . $this->contact->getValue('__key'), 'commentCallback'));
            if (is_a($comments, 'PEAR_Error')) {
                Horde::logMessage($comments, __FILE__, __LINE__, PEAR_LOG_DEBUG);
                $comments = array();
            }
        }
        if (!empty($comments['threads'])) {
            echo '<br />' . $comments['threads'];
        }
        if (!empty($comments['comments']) && !$this->print) {
            echo '<br />' . $comments['comments'];
        }

        echo '</div>';

        if ($active && $GLOBALS['browser']->hasFeature('dom')) {
            if ($this->contact->hasPermission(PERMS_EDIT)) {
                require_once TURBA_BASE . '/lib/Views/EditContact.php';
                $edit = new Turba_View_EditContact($this->contact);
                $edit->html(false);
            }
            if ($this->contact->hasPermission(PERMS_DELETE)) {
                require_once TURBA_BASE . '/lib/Views/DeleteContact.php';
                $delete = new Turba_View_DeleteContact($this->contact);
                $delete->html(false);
            }
        }
    }

}
