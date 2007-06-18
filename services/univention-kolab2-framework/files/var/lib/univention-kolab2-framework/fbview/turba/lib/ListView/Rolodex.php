<?php
// $Horde: turba/lib/ListView/Rolodex.php,v 1.10 2004/05/20 16:39:08 jan Exp $

require_once TURBA_BASE . '/lib/ListView.php';

/**
 * The Turba_ListView_Rolodex:: class provides a set of methods for
 * visualizing a Turba_list as a rolodex.
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @version  $Revision: 1.1.2.1 $
 * @since Turba 0.0.1
 * @package Turba
 */
class Turba_ListView_Rolodex extends Turba_ListView {

    /**
     * Constructs a new Turba_ListView_Rolodex object.
     *
     * @param $list     List of objects to display.
     * @param $template What template file to display each object with.
     */
    function Turba_ListView_Rolodex(&$list)
    {
        $this->Turba_ListView($list);
    }

    /**
     * Renders the list contents into an HTML view.
     */
    function display()
    {
    }

}
?>
