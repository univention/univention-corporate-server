<?php
/**
 * Horde_Form for deleting address books.
 *
 * $Horde: turba/lib/Forms/DeleteAddressBook.php,v 1.1.2.2 2008-08-25 17:10:16 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @package Turba
 */

/** Variables */
require_once 'Horde/Variables.php';

/** Horde_Form */
require_once 'Horde/Form.php';

/** Horde_Form_Renderer */
require_once 'Horde/Form/Renderer.php';

/**
 * The Turba_DeleteAddressbookForm class provides the form for
 * deleting an address book.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Turba 2.2
 * @package Turba
 */
class Turba_DeleteAddressBookForm extends Horde_Form {

    /**
     * Address book being deleted
     */
    var $_addressbook;

    function Turba_DeleteAddressBookForm(&$vars, &$addressbook)
    {
        $this->_addressbook = &$addressbook;
        parent::Horde_Form($vars, sprintf(_("Delete %s"), $addressbook->get('name')));

        $this->addHidden('', 'a', 'text', true);
        $this->addVariable(sprintf(_("Really delete the address book \"%s\"? This cannot be undone and all contacts in this address book will be permanently removed."), $this->_addressbook->get('name')), 'desc', 'description', false);

        $this->setButtons(array(_("Delete"), _("Cancel")));
    }

    /**
     * @TODO Remove share from 'addressbooks' pref
     */
    function execute()
    {
        // If cancel was clicked, return false.
        if ($this->_vars->get('submitbutton') == _("Cancel")) {
            return false;
        }

        if ($this->_addressbook->get('owner') != Auth::getAuth()) {
            return PEAR::raiseError(_("You do not have permissions to delete this address book."));
        }

        $driver = &Turba_Driver::singleton($this->_addressbook->getName());
        if (is_a($driver, 'PEAR_Error')) {
            return $driver;
        }

        // We have a Turba_Driver, try to delete the address book.
        $result = $driver->deleteAll();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Address book successfully deleted from backend, remove the
        // share.
        $result = $GLOBALS['turba_shares']->removeShare($this->_addressbook);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (isset($_SESSION['turba']['source']) && $_SESSION['turba']['source'] == Util::getFormData('deleteshare')) {
            unset($_SESSION['turba']['source']);
        }

        $abooks = explode("\n", $GLOBALS['prefs']->getValue('addressbooks'));
        if (($pos = array_search($this->_addressbook->getName(), $abooks)) !== false) {
            unset($abooks[$pos]);
            $GLOBALS['prefs']->setValue('addressbooks', implode("\n", $abooks));
        }

        return true;
    }

}
