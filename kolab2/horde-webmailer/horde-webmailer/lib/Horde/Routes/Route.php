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
 * The Route object holds a route recognition and generation routine.
 * See __construct() docs for usage.
 *
 * @package Horde_Routes
 */
class Horde_Routes_Route
{
    /**
     * The path for this route, such as ':controller/:action/:id'
     * @var string
     */
    public $routePath;

    /**
     * Encoding of this route (not yet supported)
     * @var string
     */
    public $encoding = 'utf-8';

    /**
     * What to do on decoding errors?  'ignore' or 'replace'
     * @var string
     */
    public $decodeErrors = 'replace';

    /**
     * Is this a static route?
     * @var string
     */
    public $static;

    /**
     * Filter function to operate on arguments before generation
     * @var callback
     */
    public $filter;
    
    /**
     * Is this an absolute path?  (Mapper will not prepend SCRIPT_NAME)
     * @var boolean
     */
    public $absolute;

    /**
     * Does this route use explicit mode (no implicit defaults)?
     * @var boolean
     */
    public $explicit;
    
    /**
     * Default keyword arguments for this route
     * @var array
     */
    public $defaults = array();

    /**
     * Array of keyword args for special conditions (method, subDomain, function)
     * @var array
     */
    public $conditions;

    /**
     * Maximum keys that this route could utilize.
     * @var array
     */
    public $maxKeys;

    /**
     * Minimum keys required to generate this route
     * @var array
     */
    public $minKeys;

    /**
     * Default keywords that don't exist in the path; can't be changed by an incomng URL.
     * @var array
     */
    public $hardCoded;

    /**
     * Requirements for this route
     * @var array
     */
    public $reqs;

    /**
     * Regular expression for matching this route
     * @var string
     */
    public $regexp;

    /**
     * Route path split by '/'
     * @var array
     */
    protected $_routeList;

    /**
     * Reverse of $routeList
     * @var array
     */
    protected $_routeBackwards;

    /**
     * Characters that split the parts of a URL
     * @var array
     */
    protected $_splitChars;

    /**
     * Last path part used by buildNextReg()
     * @var string
     */
    protected $_prior;

    /**
     * Requirements formatted as regexps suitable for preg_match()
     * @var array
     */
    protected $_reqRegs;

    /**
     * Member name if this is a RESTful route
     * @see resource()
     * @var null|string
     */
    protected $_memberName;

    /**
     * Collection name if this is a RESTful route
     * @see resource()
     * @var null|string
     */
    protected $_collectionName;

    /**
     * Name of the parent resource, if this is a RESTful route & has a parent
     * @see resource
     * @var string
     */
    protected $_parentResource;


    /**
     *  Initialize a route, with a given routepath for matching/generation
     *
     *  The set of keyword args will be used as defaults.
     *
     *  Usage:
     *      $route = new Horde_Routes_Route(':controller/:action/:id');
     *
     *      $route = new Horde_Routes_Route('date/:year/:month/:day',
     *                      array('controller'=>'blog', 'action'=>'view'));
     *
     *      $route = new Horde_Routes_Route('archives/:page',
     *                      array('controller'=>'blog', 'action'=>'by_page',
     *                            'requirements' => array('page'=>'\d{1,2}'));
     *
     *  Note:
     *      Route is generally not called directly, a Mapper instance connect()
     *      method should be used to add routes.
     */
    public function __construct($routePath, $kargs = array())
    {
        $this->routePath = $routePath;

        // Don't bother forming stuff we don't need if its a static route
        $this->static = isset($kargs['_static']) ? $kargs['_static'] : false;

        $this->filter = isset($kargs['_filter']) ? $kargs['_filter'] : null;
        unset($kargs['_filter']);

        $this->absolute = isset($kargs['_absolute']) ? $kargs['_absolute'] : false;
        unset($kargs['absolute']);

        // Pull out the member/collection name if present, this applies only to
        // map.resource
        $this->_memberName = isset($kargs['_memberName']) ? $kargs['_memberName'] : null;
        unset($kargs['_memberName']);

        $this->_collectionName = isset($kargs['_collectionName']) ? $kargs['_collectionName'] : null;
        unset($kargs['_collectionName']);

        $this->_parentResource = isset($kargs['_parentResource']) ? $kargs['_parentResource'] : null;
        unset($kargs['_parentResource']);

        // Pull out route conditions
        $this->conditions = isset($kargs['conditions']) ? $kargs['conditions'] : null;
        unset($kargs['conditions']);

        // Determine if explicit behavior should be used
        $this->explicit = isset($kargs['_explicit']) ? $kargs['_explicit'] : false;
        unset($kargs['_explicit']);

        // Reserved keys that don't count
        $reservedKeys = array('requirements');

        // Name has been changed from the Python version
        // This is a list of characters natural splitters in a URL
        $this->_splitChars = array('/', ',', ';', '.', '#');

        // trip preceding '/' if present
        if (substr($this->routePath, 0, 1) == '/') {
            $routePath = substr($this->routePath, 1);
        }

        // Build our routelist, and the keys used in the route
        $this->_routeList = $this->_pathKeys($routePath);
        $routeKeys = array();
        foreach ($this->_routeList as $key) {
            if (is_array($key)) { $routeKeys[] = $key['name']; }
        }

        // Build a req list with all the regexp requirements for our args
        $this->reqs = isset($kargs['requirements']) ? $kargs['requirements'] : array();
        $this->_reqRegs = array();
        foreach ($this->reqs as $key => $value) {
            $this->_reqRegs[$key] = '@^' . str_replace('@', '\@', $value) . '$@';
        }

        // Update our defaults and set new default keys if needed. defaults
        // needs to be saved
        list($this->defaults, $defaultKeys) = $this->_defaults($routeKeys, $reservedKeys, $kargs);

        // Save the maximum keys we could utilize
        $this->maxKeys = array_unique(array_merge($defaultKeys, $routeKeys));
        list($this->minKeys, $this->_routeBackwards) = $this->_minKeys($this->_routeList);

        // Populate our hardcoded keys, these are ones that are set and don't
        // exist in the route
        $this->hardCoded = array();
        foreach ($this->maxKeys as $key) {
            if (!in_array($key, $routeKeys) && $this->defaults[$key] != null) {
                $this->hardCoded[] = $key;
            }
        }
    }

    /**
     * Utility method to walk the route, and pull out the valid
     * dynamic/wildcard keys
     *
     * @param  string  $routePath  Route path
     * @return array               Route list
     */
    protected function _pathKeys($routePath)
    {
        $collecting = false;
        $current = '';
        $doneOn = array();
        $varType = '';
        $justStarted = false;
        $routeList = array();

        foreach (preg_split('//', $routePath, -1, PREG_SPLIT_NO_EMPTY) as $char) {
            if (!$collecting && in_array($char, array(':', '*'))) {
                $justStarted = true;
                $collecting = true;
                $varType = $char;
                if (strlen($current) > 0) {
                   $routeList[] = $current;
                   $current = '';
                }
            } else if ($collecting && $justStarted) {
                $justStarted = false;
                if ($char == '(') {
                    $doneOn = array(')');
                } else {
                    $current = $char;
                    // Basically appends '-' to _splitChars
                    // Helps it fall in line with the Python idioms.
                    $doneOn = $this->_splitChars + array('-');
                }
            } else if ($collecting && !in_array($char, $doneOn)) {
                $current .= $char;
            } else if ($collecting) {
                $collecting = false;
                $routeList[] = array('type' => $varType, 'name' => $current);
                if (in_array($char, $this->_splitChars)) {
                    $routeList[] = $char;
                }
                $doneOn = $varType = $current = '';
            } else {
                $current .= $char;
            }
        }
        if ($collecting) {
            $routeList[] = array('type' => $varType, 'name' => $current);
        } else if (!empty($current)) {
            $routeList[] = $current;
        }
        return $routeList;
    }

    /**
     * Utility function to walk the route backwards
     *
     * Will determine the minimum keys we must have to generate a
     * working route.
     *
     * @param  array  $routeList  Route path split by '/'
     * @return array              [minimum keys for route, route list reversed]
     */
    protected function _minKeys($routeList)
    {
        $minKeys = array();
        $backCheck = array_reverse($routeList);
        $gaps = false;
        foreach ($backCheck as $part) {
            if (!is_array($part) && !in_array($part, $this->_splitChars)) {
                $gaps = true;
                continue;
            } else if (!is_array($part)) {
                continue;
            }
            $key = $part['name'];
            if (array_key_exists($key, $this->defaults) && !$gaps)
                continue;
            $minKeys[] = $key;
            $gaps = true;
        }
        return array($minKeys, $backCheck);
    }

    /**
     * Creates a default array of strings
     *
     * Puts together the array of defaults, turns non-null values to strings,
     * and add in our action/id default if they use and do not specify it
     *
     * Precondition: $this->_defaultKeys is an array of the currently assumed default keys
     *
     * @param  array  $routekeys     All the keys found in the route path
     * @param  array  $reservedKeys  Array of keys not in the route path
     * @param  array  $kargs         Keyword args passed to the Route constructor
     * @return array                 [defaults, new default keys]
     */
    protected function _defaults($routeKeys, $reservedKeys, $kargs)
    {
        $defaults = array();
        
        // Add in a controller/action default if they don't exist
        if ((!in_array('controller', $routeKeys)) &&
            (!in_array('controller', array_keys($kargs))) &&
            (!$this->explicit)) {
            $kargs['controller'] = 'content';
        }
        
        if (!in_array('action', $routeKeys) && 
            (!in_array('action', array_keys($kargs))) &&
            (!$this->explicit)) {
            $kargs['action'] = 'index';
        }

        $defaultKeys = array();
        foreach (array_keys($kargs) as $key) {
            if (!in_array($key, $reservedKeys)) {
                $defaultKeys[] = $key;
            }
        }

        foreach ($defaultKeys as $key) {
            if ($kargs[$key] !== null) {
                $defaults[$key] = (string)$kargs[$key];
            } else {
                $defaults[$key] = null;
            }
        }

        if (in_array('action', $routeKeys) &&
            (!array_key_exists('action', $defaults)) &&
            (!$this->explicit)) {
            $defaults['action'] = 'index';
        }

        if (in_array('id', $routeKeys) &&
            (!array_key_exists('id', $defaults)) &&
            (!$this->explicit)) {
            $defaults['id'] = null;
        }

        $newDefaultKeys = array();
        foreach (array_keys($defaults) as $key) {
            if (!in_array($key, $reservedKeys)) {
                $newDefaultKeys[] = $key;
            }
        }
        return array($defaults, $newDefaultKeys);
    }

    /**
     * Create the regular expression for matching.
     *
     * Note: This MUST be called before match can function properly.
     *
     * clist should be a list of valid controller strings that can be
     * matched, for this reason makeregexp should be called by the web
     * framework after it knows all available controllers that can be
     * utilized.
     *
     * @param  array  $clist  List of all possible controllers
     * @return void
     */
    public function makeRegexp($clist)
    {
        list($reg, $noreqs, $allblank) = $this->buildNextReg($this->_routeList, $clist);

        if (empty($reg)) {
            $reg = '/';
        }
        $reg = $reg . '(/)?$';
        if (substr($reg, 0, 1) != '/') {
            $reg = '/' . $reg;
        }
        $reg = '^' . $reg;

        $this->regexp = $reg;
    }

    /**
     * Recursively build a regexp given a path, and a controller list.
     *
     * Returns the regular expression string, and two booleans that can be
     * ignored as they're only used internally by buildnextreg.
     *
     * @param  array  $path   The RouteList for the path
     * @param  array  $clist  List of all possible controllers
     * @return array          [array, boolean, boolean]
     */
    public function buildNextReg($path, $clist)
    {
        if (!empty($path)) {
            $part = $path[0];
        } else {
            $part = '';
        }

        // noreqs will remember whether the remainder has either a string
        // match, or a non-defaulted regexp match on a key, allblank remembers
        // if the rest could possible be completely empty
        list($rest, $noreqs, $allblank) = array('', true, true);

        if (count($path) > 1) {
            $this->_prior = $part;
            list($rest, $noreqs, $allblank) = $this->buildNextReg(array_slice($path, 1), $clist);
        }

        if (is_array($part) && $part['type'] == ':') {
            $var = $part['name'];
            $partreg = '';

            // First we plug in the proper part matcher
            if (array_key_exists($var, $this->reqs)) {
                $partreg = '(?P<' . $var . '>' . $this->reqs[$var] . ')';
            } else if ($var == 'controller') {
                $partreg = '(?P<' . $var . '>' . implode('|', array_map('preg_quote', $clist)) . ')';
            } else if (in_array($this->_prior, array('/', '#'))) {
                $partreg = '(?P<' . $var . '>[^' . $this->_prior . ']+?)';
            } else {
                if (empty($rest)) {
                    $partreg = '(?P<' . $var . '>[^/]+?)';
                } else {
                    $partreg = '(?P<' . $var . '>[^' . implode('', $this->_splitChars) . ']+?)';
                }
            }

            if (array_key_exists($var, $this->reqs)) {
                $noreqs = false;
            }
            if (!array_key_exists($var, $this->defaults)) {
                $allblank = false;
                $noreqs = false;
            }

            // Now we determine if its optional, or required. This changes
            // depending on what is in the rest of the match. If noreqs is
            // true, then its possible the entire thing is optional as there's
            // no reqs or string matches.
            if ($noreqs) {
                // The rest is optional, but now we have an optional with a
                // regexp. Wrap to ensure that if we match anything, we match
                // our regexp first. It's still possible we could be completely
                // blank as we have a default
                if (array_key_exists($var, $this->reqs) && array_key_exists($var, $this->defaults)) {
                    $reg = '(' . $partreg . $rest . ')?';

                // Or we have a regexp match with no default, so now being
                // completely blank form here on out isn't possible
                } else if (array_key_exists($var, $this->reqs)) {
                    $allblank = false;
                    $reg = $partreg . $rest;

                // If the character before this is a special char, it has to be
                // followed by this
                } else if (array_key_exists($var, $this->defaults) && in_array($this->_prior, array(',', ';', '.'))) {
                    $reg = $partreg . $rest;

                // Or we have a default with no regexp, don't touch the allblank
                } else if (array_key_exists($var, $this->defaults)) {
                    $reg = $partreg . '?' . $rest;

                // Or we have a key with no default, and no reqs. Not possible
                // to be all blank from here
                } else {
                    $allblank = false;
                    $reg = $partreg . $rest;
                }

            // In this case, we have something dangling that might need to be
            // matched
            } else {
                // If they can all be blank, and we have a default here, we know
                // its safe to make everything from here optional. Since
                // something else in the chain does have req's though, we have
                // to make the partreg here required to continue matching
                if ($allblank && array_key_exists($var, $this->defaults)) {
                    $reg = '(' . $partreg . $rest . ')?';

                // Same as before, but they can't all be blank, so we have to
                // require it all to ensure our matches line up right
                } else {
                    $reg = $partreg . $rest;
                }
            }
        } else if (is_array($part) && $part['type'] == '*') {
            $var = $part['name'];
            if ($noreqs) {
                $reg = '(?P<' . $var . '>.*)' . $rest;
                if (!array_key_exists($var, $this->defaults)) {
                    $allblank = false;
                    $noreqs = false;
                }
            } else {
                if ($allblank && array_key_exists($var, $this->defaults)) {
                    $reg = '(?P<' . $var . '>.*)' . $rest;
                } else if (array_key_exists($var, $this->defaults)) {
                    $reg = '(?P<' . $var . '>.*)' . $rest;
                } else {
                    $allblank = false;
                    $noreqs = false;
                    $reg = '(?P<' . $var . '>.*)' . $rest;
                }
            }
        } else if ($part && in_array(substr($part, -1), $this->_splitChars)) {
            if ($allblank) {
                $reg = preg_quote(substr($part, 0, -1)) . '(' . preg_quote(substr($part, -1)) . $rest . ')?';
            } else {
                $allblank = false;
                $reg = preg_quote($part) . $rest;
            }

        // We have a normal string here, this is a req, and it prevents us from
        // being all blank
        } else {
            $noreqs = false;
            $allblank = false;
            $reg = preg_quote($part) . $rest;
        }

        return array($reg, $noreqs, $allblank);
    }

    /**
     * Match a url to our regexp.
     *
     * While the regexp might match, this operation isn't
     * guaranteed as there's other factors that can cause a match to fail
     * even though the regexp succeeds (Default that was relied on wasn't
     * given, requirement regexp doesn't pass, etc.).
     *
     * Therefore the calling function shouldn't assume this will return a
     * valid dict, the other possible return is False if a match doesn't work
     * out.
     *
     * @param  string  $url  URL to match
     * @param  array         Keyword arguments
     * @return null|array    Array of match data if matched, Null otherwise
     */
    public function match($url, $kargs = array())
    {
        $defaultKargs = array('environ'          => array(),
                              'subDomains'       => false,
                              'subDomainsIgnore' => array(),
                              'domainMatch'      => '');
        $kargs = array_merge($defaultKargs, $kargs);

        // Static routes don't match, they generate only
        if ($this->static) {
            return false;
        }

        if (substr($url, -1) == '/' && strlen($url) > 1) {
            $url = substr($url, 0, -1);
        }

        // Match the regexps we generated
        $match = preg_match('@' . str_replace('@', '\@', $this->regexp) . '@', $url, $matches);
        if ($match == 0) {
            return false;
        }

        $host = isset($kargs['environ']['HTTP_HOST']) ? $kargs['environ']['HTTP_HOST'] : null;
        if ($host !== null && !empty($kargs['subDomains'])) {
            $host = substr($host, 0, strpos(':', $host));
            $subMatch = '@^(.+?)\.' . $kargs['domainMatch'] . '$';
            $subdomain = preg_replace($subMatch, '$1', $host);
            if (!in_array($subdomain, $kargs['subDomainsIgnore'] && $host != $subdomain)) {
                $subDomain = $subdomain;
            }
        }

        if (!empty($this->conditions)) {
            if (array_key_exists('method', $this->conditions) &&
                (empty($kargs['environ']['REQUEST_METHOD']) ||
                 !in_array($kargs['environ']['REQUEST_METHOD'], $this->conditions['method']))) {
                return false;
            }

            // Check sub-domains?
            $use_sd = isset($this->conditions['subDomain']) ? $this->conditions['subDomain'] : null;
            if (!empty($use_sd) && empty($subDomain)) {
                return false;
            }
            if (is_array($use_sd) && !in_array($subDomain, $use_sd)) {
                return false;
            }
        }
        $matchDict = $matches;

        // Clear out int keys as PHP gives us both the named subgroups and numbered subgroups
        foreach ($matchDict as $key => $val) {
            if (is_int($key)) {
                unset($matchDict[$key]);
            }
        }
        $result = array();
        $extras = Horde_Routes_Utils::arraySubtract(array_keys($this->defaults), array_keys($matchDict));

        foreach ($matchDict as $key => $val) {
            // TODO: character set decoding
            if ($key != 'path_info' && $this->encoding) {
                $val = urldecode($val);
            }

            if (empty($val) && array_key_exists($key, $this->defaults) && !empty($this->defaults[$key])) {
                $result[$key] = $this->defaults[$key];
            } else {
                $result[$key] = $val;
            }
        }

        foreach ($extras as $key) {
            $result[$key] = $this->defaults[$key];
        }

        // Add the sub-domain if there is one
        if (!empty($kargs['subDomains'])) {
            $result['subDomain'] = $subDomain;
        }

        // If there's a function, call it with environ and expire if it
        // returns False
        if (!empty($this->conditions) && array_key_exists('function', $this->conditions) &&
            !call_user_func_array($this->conditions['function'], array($kargs['environ'], $result))) {
            return false;
        }

        return $result;
    }

    /**
     * Generate a URL from ourself given a set of keyword arguments
     *
     * @param  array  $kargs   Keyword arguments
     * @param  boolean|string  False if generation failed, URL otherwise
     */
    public function generate($kargs)
    {
        $defaultKargs = array('_ignoreReqList' => false,
                              '_appendSlash'   => false);
        $kargs = array_merge($defaultKargs, $kargs);

        $_appendSlash = $kargs['_appendSlash'];
        unset($kargs['_appendSlash']);

        $_ignoreReqList = $kargs['_ignoreReqList'];
        unset($kargs['_ignoreReqList']);

        // Verify that our args pass any regexp requirements
        if (!$_ignoreReqList) {
            foreach ($this->reqs as $key => $v) {
                $value = (isset($kargs[$key])) ? $kargs[$key] : null;

                if (!empty($value) && !preg_match($this->_reqRegs[$key], $value)) {
                    return false;
                }
            }
        }

        // Verify that if we have a method arg, it's in the method accept list.
        // Also, method will be changed to _method for route generation.
        $meth = (isset($kargs['method'])) ? $kargs['method'] : null;

        if ($meth) {
            if ($this->conditions && isset($this->conditions['method']) &&
                (!in_array(strtoupper($meth), $this->conditions['method']))) {

                return false;
            }
            unset($kargs['method']);
        }

        $routeList = $this->_routeBackwards;
        $urlList = array();
        $gaps = false;
        foreach ($routeList as $part) {
            if (is_array($part) && $part['type'] == ':') {
                $arg = $part['name'];

                // For efficiency, check these just once
                $hasArg = array_key_exists($arg, $kargs);
                $hasDefault = array_key_exists($arg, $this->defaults);

                // Determine if we can leave this part off
                // First check if the default exists and wasn't provided in the
                // call (also no gaps)
                if ($hasDefault && !$hasArg && !$gaps) {
                    continue;
                }

                // Now check to see if there's a default and it matches the
                // incoming call arg
                if (($hasDefault && $hasArg) && $kargs[$arg] == $this->defaults[$arg] && !$gaps) {
                    continue;
                }

                // We need to pull the value to append, if the arg is NULL and
                // we have a default, use that
                if ($hasArg && $kargs[$arg] === null && $hasDefault && !$gaps) {
                    continue;

                // Otherwise if we do have an arg, use that
                } else if ($hasArg) {
                    $val = ($kargs[$arg] === null) ? 'null' : $kargs[$arg];
                } else if ($hasDefault && $this->defaults[$arg] != null) {
                    $val = $this->defaults[$arg];

                // No arg at all? This won't work
                } else {
                    return false;
                }

                $urlList[] = Horde_Routes_Utils::urlQuote($val, $this->encoding);
                if ($hasArg) {
                    unset($kargs[$arg]);
                }
                $gaps = true;
            } else if (is_array($part) && $part['type'] == '*') {
                $arg = $part['name'];
                $kar = (isset($kargs[$arg])) ? $kargs[$arg] : null;
                if ($kar != null) {
                    $urlList[] = Horde_Routes_Utils::urlQuote($kar, $this->encoding);
                    $gaps = true;
                }
            } else if (!empty($part) && in_array(substr($part, -1), $this->_splitChars)) {
                if (!$gaps && in_array($part, $this->_splitChars)) {
                    continue;
                } else if (!$gaps) {
                    $gaps = true;
                    $urlList[] = substr($part, 0, -1);
                } else {
                    $gaps = true;
                    $urlList[] = $part;
                }
            } else {
                $gaps = true;
                $urlList[] = $part;
            }
        }

        $urlList = array_reverse($urlList);
        $url = implode('', $urlList);
        if (substr($url, 0, 1) != '/') {
            $url = '/' . $url;
        }

        $extras = $kargs;
        foreach ($this->maxKeys as $key) {
            unset($extras[$key]);
        }
        $extras = array_keys($extras);

        if (!empty($extras)) {
            if ($_appendSlash && substr($url, -1) != '/') {
                $url .= '/';
            }
            $url .= '?';
            $newExtras = array();
            foreach ($kargs as $key => $value) {
                if (in_array($key, $extras) && ($key != 'action' || $key != 'controller')) {
                     $newExtras[$key] = $value;
                }
            }
            $url .= http_build_query($newExtras);
        } else if ($_appendSlash && substr($url, -1) != '/') {
            $url .= '/';
        }
        return $url;
    }

}