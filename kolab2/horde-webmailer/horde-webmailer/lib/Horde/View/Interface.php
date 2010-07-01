<?php
/**
 * @category Horde
 * @package Horde_View
 */

/**
 * Horde_View_Interface is a reference for classes to be used as Horde
 * Views. Implementing it is optional; type hinting is not used to
 * enforce the interface.
 *
 * @category Horde
 * @package Horde_View
 */
interface Horde_View_Interface {

    /**
     * Return a view variable
     *
     * @param string $name Variable name to retrieve
     */
    public function __get($name);

    /**
     * Assign a single view variable
     *
     * @param string $name Variable name to set
     * @param mixed $value The value of $name
     */
    public function __set($name, $value);

    /**
     * Accesses a helper object from within a template.
     *
     * @param string $name The helper name.
     * @param array $args The parameters for the helper.
     *
     * @return string The result of the helper output.
     */
    public function __call($name, $args);

    /**
     * Adds to the stack of template paths in LIFO order.
     *
     * @param string|array The directory (-ies) to add.
     */
    public function addTemplatePath($path);

    /**
     * Resets the stack of template paths.
     *
     * To clear all paths, use Horde_View::setTemplatePath(null).
     *
     * @param string|array The directory (-ies) to set as the path.
     */
    public function setTemplatePath($path);

    /**
     * Adds to the stack of helpers in LIFO order.
     *
     * @param Horde_View_Helper The helper instance to add.
     */
    public function addHelper($helper);

    /**
     * Sets the escape() callback.
     *
     * @param mixed $spec The callback for escape() to use.
     */
    public function setEscape($spec);

    /**
     * Assigns multiple variables to the view.
     *
     * The array keys are used as names, each assigned their
     * corresponding array value.
     *
     * @param array $array The array of key/value pairs to assign.
     *
     * @see __set()
     */
    public function assign($array);

    /**
     * Processes a template and returns the output.
     *
     * @param string $name The template name to process.
     *
     * @return string The template output.
     */
    public function render($name);

    /**
     * Escapes a value for output in a template.
     *
     * If escaping mechanism is one of htmlspecialchars or htmlentities, uses
     * {@link $_encoding} setting.
     *
     * @param mixed $var The output to escape.
     *
     * @return mixed The escaped value.
     */
    public function escape($var);

    /**
     * Set encoding to use with htmlentities() and htmlspecialchars()
     *
     * @param string $encoding
     */
    public function setEncoding($encoding);

    /**
     * Return current escape encoding
     *
     * @return string
     */
    public function getEncoding();

}
