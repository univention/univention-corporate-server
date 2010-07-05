<?php
/**
 * @category Horde
 * @package Horde_View
 */

/**
 * Abstract base class for Horde_View to get private constructs out of
 * template scope.
 *
 * @category Horde
 * @package Horde_View
 */
abstract class Horde_View_Base {

    /**
     * Path stack for templates.
     *
     * @var array
     */
    private $_templatePath = array('./');

    /**
     * Template to execute. Stored in a private variable to keep it
     * out of the public view scope.
     *
     * @var string
     */
    private $_file = null;

    /**
     * Cache of helper objects.
     *
     * @var array
     */
    private $_helpers = array();

    /**
     * Callback for escaping.
     *
     * @var string
     */
    private $_escape = 'htmlspecialchars';

    /**
     * Encoding to use in escaping mechanisms; defaults to UTF-8.
     * @var string
     */
    private $_encoding = 'UTF-8';

    /**
     * Constructor.
     *
     * @param array $config Configuration key-value pairs.
     */
    public function __construct($config = array())
    {
        // user-defined escaping callback
        if (!empty($config['escape'])) {
            $this->setEscape($config['escape']);
        }

        // encoding
        if (!empty($config['encoding'])) {
            $this->setEncoding($config['encoding']);
        }

        // user-defined template path
        if (!empty($config['templatePath'])) {
            $this->addTemplatePath($config['templatePath']);
        }
    }

    /**
     * Return a view variable
     *
     * @param string $name Variable name to retrieve
     */
    public function __get($name)
    {
        return isset($this->name) ? $this->name : '';
    }

    /**
     * Assign a single view variable
     *
     * @param string $name Variable name to set
     * @param mixed $value The value of $name
     */
    public function __set($name, $value)
    {
        $this->$name = $value;
    }

    /**
     * Accesses a helper object from within a template.
     *
     * @param string $method The helper method.
     * @param array $args The parameters for the helper.
     *
     * @return string The result of the helper method.
     */
    public function __call($method, $args)
    {
        if (isset($this->_helpers[$method])) {
            return call_user_func_array(array($this->_helpers[$method], $method), $args);
        }

        throw new Horde_View_Exception('Helper for ' . $method . ' not found.');
    }

    /**
     * Adds to the stack of template paths in LIFO order.
     *
     * @param string|array The directory (-ies) to add.
     */
    public function addTemplatePath($path)
    {
        foreach ((array)$path as $dir) {
            // Attempt to strip any possible separator and append the
            // system directory separator.
            $dir = rtrim($dir, '\\/' . DIRECTORY_SEPARATOR)
                . DIRECTORY_SEPARATOR;

            // Add to the top of the stack.
            array_unshift($this->_templatePath, $dir);
        }
    }

    /**
     * Resets the stack of template paths.
     *
     * To clear all paths, use Horde_View::setTemplatePath(null).
     *
     * @param string|array The directory (-ies) to set as the path.
     */
    public function setTemplatePath($path)
    {
        $this->_templatePath = array();
        $this->addTemplatePath($path);
    }

    /**
     * Adds to the stack of helpers in LIFO order.
     *
     * @param Horde_View_Helper $helper The helper instance to add.
     */
    public function addHelper($helper)
    {
        foreach (get_class_methods($helper) as $method) {
            $this->_helpers[$method] = $helper;
        }
    }

    /**
     * Sets the escape() callback.
     *
     * @param mixed $spec The callback for escape() to use.
     */
    public function setEscape($spec)
    {
        $this->_escape = $spec;
    }

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
    public function assign($array)
    {
        foreach ($array as $key => $val) {
            $this->$key = $val;
        }
    }

    /**
     * Processes a template and returns the output.
     *
     * @param string $name The template to process.
     *
     * @return string The template output.
     */
    public function render($name)
    {
        // Find the template file name.
        $this->_file = $this->_template($name);

        // remove $name from local scope
        unset($name);

        ob_start();
        $this->_run($this->_file);
        return ob_get_clean();
    }

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
    public function escape($var)
    {
        if (in_array($this->_escape, array('htmlspecialchars', 'htmlentities'))) {
            return call_user_func($this->_escape, $var, ENT_QUOTES, $this->_encoding);
        }

        return call_user_func($this->_escape, $var);
    }

    /**
     * Set encoding to use with htmlentities() and htmlspecialchars()
     *
     * @param string $encoding
     */
    public function setEncoding($encoding)
    {
        $this->_encoding = $encoding;
    }

    /**
     * Return current escape encoding
     *
     * @return string
     */
    public function getEncoding()
    {
        return $this->_encoding;
    }

    /**
     * Finds a template from the available directories.
     *
     * @param $name string The base name of the template.
     */
    protected function _template($name)
    {
        if (!count($this->_templatePath)) {
            throw new Horde_View_Exception('No template directory set; unable to locate ' . $name);
        }

        foreach ($this->_templatePath as $dir) {
            if (is_readable($dir . $name)) {
                return $dir . $name;
            }
        }

        throw new Horde_View_Exception("\"$name\" not found in template path (\"" . implode(':', $this->_templatePath) . '")');
    }

    /**
     * Use to include the template in a scope that only allows public
     * members.
     *
     * @return mixed
     */
    abstract protected function _run();

}
