<?php
/**
 * @category Horde
 * @package Horde_View
 */

/**
 * Concrete class for handling views.
 *
 * @category Horde
 * @package Horde_View
 */
class Horde_View extends Horde_View_Base {

    /**
     * Includes the template in a scope with only public variables.
     *
     * @param string The template to execute. Not declared in the
     * function signature so it stays out of the view's public scope.
     */
    protected function _run()
    {
        $oldShortOpenTag = ini_set('short_open_tag', 1);
        include func_get_arg(0);
        ini_set('short_open_tag', $oldShortOpenTag);
    }

}
