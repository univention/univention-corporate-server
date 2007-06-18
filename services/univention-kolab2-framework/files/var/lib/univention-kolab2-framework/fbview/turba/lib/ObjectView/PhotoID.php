<?php
// $Horde: turba/lib/ObjectView/PhotoID.php,v 1.7 2004/05/20 16:39:09 jan Exp $

require_once TURBA_BASE . '/lib/ObjectView.php';

/**
 * The Turba_ObjectView_photoID:: class provides a set of methods for
 * visualizing a Turba_AbstractObject as a drivers-license like photo id.
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @version  $Revision: 1.1.2.1 $
 * @since Turba 0.0.1
 * @package Turba
 */
class Turba_ObjectView_photoID extends Turba_ObjectView {

    /**
     * Constructs a new Turba_ObjectView_photoID object.
     *
     * @param $object   The object to display.
     * @param $template What template file to display this object with.
     */
    function Turba_ObjectView_photoID(&$object, $template)
    {
        $this->Turba_ObjectView($object);
    }


    /**
     * Renders the object into an HTML view.
     */
    function display()
    {
    }

}
?>
