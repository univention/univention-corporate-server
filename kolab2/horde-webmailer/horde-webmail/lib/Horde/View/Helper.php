<?php
/**
 * @category Horde
 * @package Horde_View
 */

/**
 * Abstract class for Horde_View_Helper objects.
 *
 * @category Horde
 * @package Horde_View
 */
abstract class Horde_View_Helper {

    /**
     * The parent view invoking the helper
     *
     * @var Horde_View
     */
    protected $_view;

    /**
     * Create a helper for $view
     *
     * @param Horde_View $view The view to help.
     */
    public function __construct($view)
    {
        $this->_view = $view;
        $view->addHelper($this);
    }

    /**
     * Call chaining so other helpers can be called transparently.
     *
     * @param string $method The helper method.
     * @param array $args The parameters for the helper.
     *
     * @return string The result of the helper method.
     */
    public function __call($method, $args)
    {
        return call_user_func_array(array($this->_view, $method), $args);
    }

}
