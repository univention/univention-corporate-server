<?php
// $Horde: turba/lib/ObjectView/List.php,v 1.7 2004/05/20 16:39:09 jan Exp $

require_once './lib/ObjectView.php';

/**
 * The Turba_ObjectView_List:: class provides a set of methods for
 * visualizing a Turba_AbstractObject as a plain list of attributes.
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @version  $Revision: 1.1.2.1 $
 * @since Turba 0.0.1
 * @package Turba
 */
class Turba_ObjectView_List extends Turba_ObjectView {

    /**
     * Constructs a new Turba_ObjectView_List object.
     *
     * @param $object   The object to display.
     * @param $template What template file to display this object with.
     */
    function Turba_ObjectView_List(&$object, $template)
    {
        $this->Turba_ObjectView($object, $template);
    }


    /**
     * Renders the object into an HTML view.
     */
    function display()
    {
    }

}
?>
