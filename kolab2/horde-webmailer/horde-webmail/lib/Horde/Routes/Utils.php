<?php
/**
 * Horde Routes package
 *
 * This package is heavily inspired by the Python "Routes" library
 * by Ben Bangert (http://routes.groovie.org).  Routes is based
 * largely on ideas from Ruby on Rails (http://www.rubyonrails.org).
 *
 * @author  Maintainable Software, LLC. (http://www.maintainable.com)
 * @author  Mike Naberezny <mike@maintainable.com>
 * @license http://opensource.org/licenses/bsd-license.php BSD
 * @package Horde_Routes
 */

/**
 * Utility functions for use in templates and controllers
 *
 * @package Horde_Routes
 */
class Horde_Routes_Utils
{
    /**
     * @var Horde_Routes_Mapper
     */
    public $mapper;
    
    /**
     * Match data from last match; implements for urlFor() route memory
     * @var array
     */    
    public $mapperDict = array();
    
    /**
     * Callback function used for redirectTo()
     * @var callback
     */
    public $redirect;

    
    /**
     * Constructor
     *
     * @param  Horde_Routes_Mapper  $mapper    Mapper for these utilities
     * @param  callback             $redirect  Redirect callback for redirectTo()
     */
    public function __construct($mapper, $redirect = null)
    {
        $this->mapper   = $mapper;
        $this->redirect = $redirect;
    }
    
    /**
     * Generates a URL.
     *
     * All keys given to urlFor are sent to the Routes Mapper instance for
     * generation except for::
     *
     *     anchor          specified the anchor name to be appened to the path
     *     host            overrides the default (current) host if provided
     *     protocol        overrides the default (current) protocol if provided
     *     qualified       creates the URL with the host/port information as
     *                     needed
     *
     * The URL is generated based on the rest of the keys. When generating a new
     * URL, values will be used from the current request's parameters (if
     * present). The following rules are used to determine when and how to keep
     * the current requests parameters:
     *
     * * If the controller is present and begins with '/', no defaults are used
     * * If the controller is changed, action is set to 'index' unless otherwise
     *   specified
     *
     * For example, if the current request yielded a dict (associative array) of
     * array('controller'=>'blog', 'action'=>'view', 'id'=>2), with the standard
     * ':controller/:action/:id' route, you'd get the following results::
     *
     *     urlFor(array('id'=>4))                    =>  '/blog/view/4',
     *     urlFor(array('controller'=>'/admin'))     =>  '/admin',
     *     urlFor(array('controller'=>'admin'))      =>  '/admin/view/2'
     *     urlFor(array('action'=>'edit'))           =>  '/blog/edit/2',
     *     urlFor(array('action'=>'list', id=NULL))  =>  '/blog/list'
     *
     * **Static and Named Routes**
     *
     * If there is a string present as the first argument, a lookup is done
     * against the named routes table to see if there's any matching routes. The
     * keyword defaults used with static routes will be sent in as GET query
     * arg's if a route matches.
     *
     * If no route by that name is found, the string is assumed to be a raw URL.
     * Should the raw URL begin with ``/`` then appropriate SCRIPT_NAME data will
     * be added if present, otherwise the string will be used as the url with
     * keyword args becoming GET query args.
     */
    public function urlFor($first = array(), $second = array())
    {
        if (is_array($first)) {
            // urlFor(array('controller' => 'foo', ...))
            $routeName = null;
            $kargs = $first;
        } else {
            // urlFor('named_route')
            // urlFor('named_route', array('id' => 3, ...))
            // urlFor('static_path')
            $routeName = $first;
            $kargs = $second;
        }

        $anchor    = isset($kargs['anchor'])    ? $kargs['anchor']    : null;
        $host      = isset($kargs['host'])      ? $kargs['host']      : null;
        $protocol  = isset($kargs['protocol'])  ? $kargs['protocol']  : null;
        $qualified = isset($kargs['qualified']) ? $kargs['qualified'] : null;
        unset($kargs['qualified']);

        // Remove special words from kargs, convert placeholders
        foreach (array('anchor', 'host', 'protocol') as $key) {
            if (array_key_exists($key, $kargs)) {
                unset($kargs[$key]);
            }
            if (array_key_exists($key . '_', $kargs)) {
                $kargs[$key] = $kargs[$key . '_'];
                unset($kargs[$key . '_']);
            }
        }

        $route = null;
        $static = false;
        $encoding = $this->mapper->encoding;
        $environ = $this->mapper->environ;
        $url = '';

        if (isset($routeName)) {

            if (isset($this->mapper->routeNames[$routeName])) {
                $route = $this->mapper->routeNames[$routeName];
            }

            if ($route && array_key_exists('_static', $route->defaults)) {
                $static = true;
                $url = $route->routePath;
            }

            // No named route found, assume the argument is a relative path
            if ($route === null) {
                $static = true;
                $url = $routeName;
            }

            if ((substr($url, 0, 1) == '/') &&
                isset($environ['SCRIPT_NAME'])) {
                $url = $environ['SCRIPT_NAME'] . $url;
            }

            if ($static) {
                if (!empty($kargs)) {
                    $url .= '?';
                    $query_args = array();
                    foreach ($kargs as $key => $val) {
                        $query_args[] = urlencode(utf8_decode($key)) . '=' .
                            urlencode(utf8_decode($val));
                    }
                    $url .= implode('&', $query_args);
                }
            }
        }

        if (! $static) {
            if ($route) {
                $newargs = $route->defaults;
                foreach ($kargs as $key => $value) {
                    $newargs[$key] = $value;
                }

                // If this route has a filter, apply it
                if (!empty($route->filter)) {
                    $newargs = call_user_func($route->filter, $newargs);
                }

                $newargs = $this->_subdomainCheck($newargs);
            } else {
                $newargs = $this->_screenArgs($kargs);
            }

            $anchor = (isset($newargs['_anchor'])) ? $newargs['_anchor'] : $anchor;
            unset($newargs['_anchor']);

            $host = (isset($newargs['_host'])) ? $newargs['_host'] : $host;
            unset($newargs['_host']);

            $protocol = (isset($newargs['_protocol'])) ? $newargs['_protocol'] : $protocol;
            unset($newargs['_protocol']);

            $url = $this->mapper->generate($newargs);
        }

        if (!empty($anchor)) {
            $url .= '#' . self::urlQuote($anchor, $encoding);
        }

        if (!empty($host) || !empty($qualified) || !empty($protocol)) {
            $http_host   = isset($environ['HTTP_HOST']) ? $environ['HTTP_HOST'] : null;
            $server_name = isset($environ['SERVER_NAME']) ? $environ['SERVER_NAME'] : null;
            $fullhost = !is_null($http_host) ? $http_host : $server_name;

            if (empty($host) && empty($qualified)) {
                $host = explode(':', $fullhost);
                $host = $host[0];
            } else if (empty($host)) {
                $host = $fullhost;
            }
            if (empty($protocol)) {
                if (!empty($environ['HTTPS']) && $environ['HTTPS'] != 'off') {
                    $protocol = 'https';
                } else {
                    $protocol = 'http';
                }
            }
            if ($url !== null) {
                $url = $protocol . '://' . $host . $url;
            }
        }

        return $url;
    }

    /**
     * Issues a redirect based on the arguments.
     *
     * Redirects *should* occur as a "302 Moved" header, however the web
     * framework may utilize a different method.
     *
     * All arguments are passed to urlFor() to retrieve the appropriate URL, then
     * the resulting URL it sent to the redirect function as the URL.
     *
     * @param   mixed  $first   First argument in varargs, same as urlFor()
     * @param   mixed  $second  Second argument in varargs
     * @return  mixed           Result of redirect callback
     */
    public function redirectTo($first = array(), $second = array())
    {
        $target = $this->urlFor($first, $second);
        return call_user_func($this->redirect, $target);
    }

    /**
     * Scan a directory for PHP files and use them as controllers.  Used
     * as the default scanner callback for Horde_Routes_Mapper.  See the
     * constructor of that class for more information.
     *
     * Given a directory with:
     *   foo.php, bar.php, baz.php
     * Returns an array:
     *   foo, bar, baz
     *
     * @param  string  $dirname  Directory to scan for controller files
     * @param  string  $prefix   Prefix controller names (optional)
     * @return array             Array of controller names
     */
    public static function controllerScan($dirname = null, $prefix = '')
    {
        $controllers = array();

        if ($dirname === null) {
            return $controllers;
        }

        $baseregexp = preg_quote($dirname . DIRECTORY_SEPARATOR, '/');

        foreach (new RecursiveIteratorIterator(
                 new RecursiveDirectoryIterator($dirname)) as $entry) {
                     
            if ($entry->isFile()) {
                 // match .php files that don't start with an underscore
                 if (preg_match('/^[^_]{1,1}.*\.php$/', basename($entry->getFilename())) != 0) {
                    // strip off base path: dirname/admin/users.php -> admin/users.php
                    $controller = preg_replace("/^$baseregexp(.*)\.php/", '\\1', $entry->getPathname());
                    
                    // add to controller list
                    $controllers[] = $prefix . $controller;
                }
            }
        }

        usort($controllers, 'Horde_Routes_Utils::longestFirst');
        return $controllers;
    }

    /**
     * Private function that takes a dict, and screens it against the current
     * request dict to determine what the dict should look like that is used.
     * This is responsible for the requests "memory" of the current.
     */
    private function _screenArgs($kargs)
    {
        if ($this->mapper->explicit && $this->mapper->subDomains) {
            return $this->_subdomainCheck($kargs);
        } else if ($this->mapper->explicit) {
            return $kargs;
        }

        $controllerName = (isset($kargs['controller'])) ? $kargs['controller'] : null;

        if (!empty($controllerName) && substr($controllerName, 0, 1) == '/') {
            // If the controller name starts with '/', ignore route memory
            $kargs['controller'] = substr($kargs['controller'], 1);
            return $kargs;
        } else if (!empty($controllerName) && !array_key_exists('action', $kargs)) {
            // Fill in an action if we don't have one, but have a controller
            $kargs['action'] = 'index';
        }

        $memoryKargs = $this->mapperDict;

        // Remove keys from memory and kargs if kargs has them as null
        foreach ($kargs as $key => $value) {
             if ($value === null) {
                 unset($kargs[$key]);
                 if (array_key_exists($key, $memoryKargs)) {
                     unset($memoryKargs[$key]);
                 }
             }
        }

        // Merge the new args on top of the memory args
        foreach ($kargs as $key => $value) {
            $memoryKargs[$key] = $value;
        }

        // Setup a sub-domain if applicable
        if (!empty($this->mapper->subDomains)) {
            $memoryKargs = $this->_subdomainCheck($memoryKargs);
        }

        return $memoryKargs;
    }

    /**
     * Screen the kargs for a subdomain and alter it appropriately depending
     * on the current subdomain or lack therof.
     */
    private function _subdomainCheck($kargs)
    {
        if ($this->mapper->subDomains) {
            $subdomain = (isset($kargs['subDomain'])) ? $kargs['subDomain'] : null;
            unset($kargs['subDomain']);

            $environ = $this->mapper->environ;
            $http_host   = isset($environ['HTTP_HOST']) ? $environ['HTTP_HOST'] : null;
            $server_name = isset($environ['SERVER_NAME']) ? $environ['SERVER_NAME'] : null;
            $fullhost = !is_null($http_host) ? $http_host : $server_name;

            $hostmatch = explode(':', $fullhost);
            $host = $hostmatch[0];
            $port = '';
            if (count($hostmatch) > 1) {
                $port .= ':' . $hostmatch[1];
            }

            $subMatch = '^.+?\.(' . $this->mapper->domainMatch . ')$';
            $domain = preg_replace("@$subMatch@", '$1', $host);

            if ($subdomain && (substr($host, 0, strlen($subdomain)) != $subdomain)
                    && (! in_array($subdomain, $this->mapper->subDomainsIgnore))) {
                $kargs['_host'] = $subdomain . '.' . $domain . $port;
            } else if (($subdomain === null || in_array($subdomain, $this->mapper->subDomainsIgnore))
                    && $domain != $host) {
                $kargs['_host'] = $domain . $port;
            }
            return $kargs;
        } else {
            return $kargs;
        }
    }

    /**
     * Quote a string containing a URL in a given encoding.
     *
     * @todo This is a placeholder.  Multiple encodings aren't yet supported.
     *
     * @param  string  $url       URL to encode
     * @param  string  $encoding  Encoding to use
     */
    public static function urlQuote($url, $encoding = null)
    {
        if ($encoding === null) {
            return str_replace('%2F', '/', urlencode($url));
        } else {
            return str_replace('%2F', '/', urlencode(utf8_decode($url)));
        }
    }

    /**
     * Callback used by usort() in controllerScan() to sort controller
     * names by the longest first.
     *
     * @param   string  $fst  First string to compare
     * @param   string  $lst  Last string to compare
     * @return  integer       Difference of string length (first - last)
     */
    public static function longestFirst($fst, $lst) {
        return strlen($lst) - strlen($fst);
    }

    /**
     */
    public static function arraySubtract($a1, $a2)
    {
        foreach ($a2 as $key) {
            if (in_array($key, $a1)) {
                unset($a1[array_search($key, $a1)]);
            }
        }
        return $a1;
    }
}
