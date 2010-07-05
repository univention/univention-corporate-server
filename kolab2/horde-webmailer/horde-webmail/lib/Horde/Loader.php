<?php
/**
 * @package Horde_Loader
 */
class Horde_Loader {

    /**
     * Autoload implementation automatically registered with
     * spl_autoload_register.
     *
     * We ignore E_WARNINGS when trying to include files so that if our
     * autoloader doesn't find a file, we pass on to the next autoloader (if
     * any) or to the PHP class not found error. We don't want to suppress all
     * errors, though, or else we'll end up silencing parse errors or
     * redefined class name errors, making debugging especially difficult.
     *
     * @param string $class  Class name to load (or interface).
     */
    public static function loadClass($class)
    {
        $file = str_replace(array('::', '_'), '/', $class) . '.php';
        $oldErrorReporting = error_reporting(E_ALL ^ E_WARNING);
        include $file;
        error_reporting($oldErrorReporting);
    }

    /**
     * Add a new path to the include_path we're loading from.
     *
     * @param string $path      The directory to add.
     * @param boolean $prepend  Add to the beginning of the stack?
     *
     * @return string  The new include_path.
     */
    public static function addClassPath($path, $prepend = true)
    {
        $include_path = get_include_path();
        if ($include_path == $path
            || strpos($include_path, PATH_SEPARATOR . $path)
            || strpos($include_path, $path . PATH_SEPARATOR) !== false) {
            // The path is already present in our stack; don't re-add it.
            return $include_path;
        }

        if ($prepend) {
            $include_path = $path . PATH_SEPARATOR . $include_path;
        } else {
            $include_path .= PATH_SEPARATOR . $path;
        }
        set_include_path($include_path);

        return $include_path;
    }

}

/* Register the autoloader in a way to play well with as many configurations
 * as possible. */
if (function_exists('spl_autoload_register')) {
    spl_autoload_register(array('Horde_Loader', 'loadClass'));
    if (function_exists('__autoload')) {
        spl_autoload_register('__autoload');
    }
} elseif (!function_exists('__autoload')) {
    function __autoload($class)
    {
        return Horde_Loader::loadClass($class);
    }
}
