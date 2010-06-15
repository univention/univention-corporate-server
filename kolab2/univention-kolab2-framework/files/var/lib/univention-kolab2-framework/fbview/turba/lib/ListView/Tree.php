<?php
// $Horde: turba/lib/ListView/Tree.php,v 1.9 2004/05/20 16:39:08 jan Exp $

require_once './lib/ListView.php';

/**
 * The Turba_ListView_Tree:: class provides a set of methods for
 * visualizing a Turba_List as a tree.
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @version  $Revision: 1.1.2.1 $
 * @since Turba 0.0.1
 * @package Turba
 */
class Turba_ListView_Tree extends Turba_ListView {

    /**
     * Constructs a new Turba_ListView_Tree object.
     *
     * @param $list     List of objects to display.
     * @param $template What template file to display each object with.
     */
    function Turba_ListView_Tree(&$list, $template)
    {
        $this->Turba_ListView($list, $template);
    }

    /**
     * Renders the list contents into an HTML view.
     */
    function display()
    {
    }

}
?>
