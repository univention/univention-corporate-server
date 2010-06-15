<?php
/**
 * The Turba_ListView:: class provides an interface for objects that
 * visualize Turba_lists.
 *
 * $Horde: turba/lib/ListView.php,v 1.17 2004/04/01 21:23:37 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_ListView {

    /**
     * The Turba_List object that we are visualizing.
     * @var object Turba_List $list
     */
    var $list;

    /**
     * The template used to display each row of the list.
     * @var string $template
     */
    var $template;

    /**
     * Constructs a new Turba_ListView object.
     *
     * @param $list     List of contacts to display.
     * @param $template What template file to display this contact with.
     */
    function Turba_ListView(&$list, $template)
    {
        $this->list = &$list;
        $this->template = $template;
    }

    /**
     * Renders the list contents into an HTML view.
     *
     * @return integer $count The number of objects in the list.
     */
    function display($min, $max)
    {
        $i = 0;
        $this->list->reset();

        while ($ob = $this->list->next()) {
            if ($i++ < $min || $i > $max) {
                continue;
            }

            include $this->template;
        }
        return $i;
    }

    /**
     * Renders the list contents that match $alpha into and HTML view.
     *
     * @param $alpha    The letter to display.
     */
    function displayAlpha($alpha)
    {
        $this->list->reset();
        $alpha = String::lower($alpha);

        $i = 0;
        while ($ob = $this->list->next()) {
            $name = Turba::formatName($ob);

            if ($alpha != '*' && String::lower($name{0}) != $alpha) {
                continue;
            }

            include $this->template;
            $i++;
        }
    }

}
