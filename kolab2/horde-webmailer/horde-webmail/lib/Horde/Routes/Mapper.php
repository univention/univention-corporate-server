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
 * The mapper class handles URL generation and recognition for web applications
 *
 * The mapper class is built by handling associated arrays of information and passing
 * associated arrays back to the application for it to handle and dispatch the
 * appropriate scripts.
 *
 * @package Horde_Routes
 */
class Horde_Routes_Mapper
{
    /**
     * Filtered request environment with keys like SCRIPT_NAME
     * @var array
     */
    public $environ = array();

    /**
     * Callback function used to get array of controller names
     * @var callback
     */
    public $controllerScan;

    /**
     * Path to controller directory passed to controllerScan function
     * @var string
     */
    public $directory;

    /**
     * Call controllerScan callback before every route match?
     * @var boolean
     */
    public $alwaysScan;

    /**
     * Disable route memory and implicit defaults?
     * @var boolean
     */
    public $explicit;

    /**
     * Collect debug information during route match?
     * @var boolean
     */
    public $debug = false;

    /**
     * Use sub-domain support?
     * @var boolean
     */
    public $subDomains = false;

    /**
     * Array of sub-domains to ignore if using sub-domain support
     * @var array
     */
    public $subDomainsIgnore = array();

    /**
     * Append trailing slash ('/') to generated routes?
     * @var boolean
     */
    public $appendSlash = false;

    /**
     * Prefix to strip during matching and to append during generation
     * @var null|string
     */
    public $prefix = null;

    /**
     * Array of connected routes
     * @var array
     */
    public $matchList = array();

    /**
     * Array of connected named routes, indexed by name
     * @var array
     */
    public $routeNames = array();

    /**
     * Cache of URLs used in generate()
     * @var array
     */
    public $urlCache = array();

    /**
     * Encoding of routes URLs (not yet supported)
     * @var string
     */
    public $encoding = 'utf-8';

    /**
     * What to do on decoding errors?  'ignore' or 'replace'
     * @var string
     */
    public $decodeErrors = 'ignore';

    /**
     * Partial regexp used to match domain part of the end of URLs to match
     * @var string
     */
    public $domainMatch = '[^\.\/]+?\.[^\.\/]+';

    /**
     * Array of all connected routes, indexed by the serialized array of all
     * keys that each route could utilize.
     * @var array
     */
    public $maxKeys = array();

    /**
     * Array of all connected routes, indexed by the serialized array of the
     * minimum keys that each route needs.
     * @var array
     */
    public $minKeys = array();

    /**
     * Utility functions like urlFor() and redirectTo() for this Mapper
     * @var Horde_Routes_Utils
     */
    public $utils;

    /**
     * Have regular expressions been created for all connected routes?
     * @var boolean
     */
    protected $_createdRegs = false;

    /**
     * Have generation hashes been created for all connected routes?
     * @var boolean
     */
    protected $_createdGens = false;

    /**
     * Generation hashes created for all connected routes
     * @var array
     */
    protected $_gendict;

    /**
     * Temporary variable used to pass array of keys into _keysort() callback
     * @var array
     */
    protected $_keysortTmp;

    /**
     * Regular expression generated to match after the prefix
     * @var string
     */
    protected $_regPrefix = null;


    /**
     * Constructor.
     *
     * Keyword arguments ($kargs):
     *   ``controllerScan`` (callback)
     *     Function to return an array of valid controllers
     *
     *   ``redirect`` (callback)
     *     Function to perform a redirect for Horde_Routes_Utils->redirectTo()
     *
     *   ``directory`` (string)
     *     Path to the directory that will be passed to the
     *     controllerScan callback
     *
     *   ``alwaysScan`` (boolean)
     *     Should the controllerScan callback be called
     *     before every URL match?
     *
     *   ``explicit`` (boolean)
     *      Should routes be connected with the implicit defaults of
     *      array('controller'=>'content', 'action'=>'index', 'id'=>null)?
     *      When set to True, these will not be added to route connections.
     */
    public function __construct($kargs = array())
    {
        $defaultKargs = array('controllerScan' => 'Horde_Routes_Utils::controllerScan',
                              'directory'      => null,
                              'alwaysScan'     => false,
                              'explicit'       => false);
        $kargs = array_merge($defaultKargs, $kargs);

        // Most default assignments that were in the construct in the Python
        // version have been moved to outside the constructor unless they were variable

        $this->directory      = $kargs['directory'];
        $this->alwaysScan     = $kargs['alwaysScan'];
        $this->controllerScan = $kargs['controllerScan'];
        $this->explicit       = $kargs['explicit'];

        $this->utils = new Horde_Routes_Utils($this);
    }

    /**
     * Create and connect a new Route to the Mapper.
     *
     * Usage:
     *   $m = new Horde_Routes_Mapper();
     *   $m->connect(':controller/:action/:id');
     *   $m->connect('date/:year/:month/:day', array('controller' => "blog", 'action' => 'view');
     *   $m->connect('archives/:page', array('controller' => 'blog', 'action' => 'by_page',
     *                                       '     requirements' => array('page' => '\d{1,2}')));
     *   $m->connect('category_list',
     *               'archives/category/:section', array('controller' => 'blog', 'action' => 'category',
     *                                                   'section' => 'home', 'type' => 'list'));
     *   $m->connect('home',
     *               '',
     *               array('controller' => 'blog', 'action' => 'view', 'section' => 'home'));
     *
     * @param  mixed  $first   First argument in vargs, see usage above.
     * @param  mixed  $second  Second argument in varags
     * @param  mixed  $third   Third argument in varargs
     * @return void
     */
    public function connect($first, $second = null, $third = null)
    {
        if ($third !== null) {
            // 3 args given
            // connect('route_name', ':/controller/:action/:id', array('kargs'=>'here'))
            $routeName = $first;
            $routePath = $second;
            $kargs     = $third;
        } else if ($second !== null) {
            // 2 args given
            if (is_array($second)) {
                // connect(':/controller/:action/:id', array('kargs'=>'here'))
                $routeName = null;
                $routePath = $first;
                $kargs     = $second;
            } else {
                // connect('route_name', ':/controller/:action/:id')
                $routeName = $first;
                $routePath = $second;
                $kargs     = array();
            }
        } else {
            // 1 arg given
            // connect('/:controller/:action/:id')
            $routeName = null;
            $routePath = $first;
            $kargs     = array();
        }

        if (!in_array('_explicit', $kargs)) {
            $kargs['_explicit'] = $this->explicit;
        }

        $route = new Horde_Routes_Route($routePath, $kargs);

        if ($this->encoding != 'utf-8' || $this->decodeErrors != 'ignore') {
            $route->encoding = $this->encoding;
            $route->decodeErrors = $this->decodeErrors;
        }

        $this->matchList[] = $route;

        if (isset($routeName)) {
            $this->routeNames[$routeName] = $route;
        }

        if ($route->static) {
            return;
        }

        $exists = false;
        foreach ($this->maxKeys as $key => $value) {
            if (unserialize($key) == $route->maxKeys) {
                $this->maxKeys[$key][] = $route;
                $exists = true;
                break;
            }
        }

        if (!$exists) {
            $this->maxKeys[serialize($route->maxKeys)] = array($route);
        }

        $this->_createdGens = false;
    }

    /**
     * Create the generation hashes (arrays) for route lookups
     *
     * @return void
     */
    protected function _createGens()
    {
        // Use keys temporarily to assemble the list to avoid excessive
        // list iteration testing with foreach
        $controllerList = array();
        $actionList = array();

        // Assemble all the hardcoded/defaulted actions/controllers used
        foreach ($this->matchList as $route) {
            if ($route->static) {
                continue;
            }
            if (isset($route->defaults['controller'])) {
                $controllerList[] = $route->defaults['controller'];
            }
            if (isset($route->defaults['action'])) {
                $actionList[] = $route->defaults['action'];
            }
        }

        // Setup the lists of all controllers/actions we'll add each route
        // to.  We include the '*' in the case that a generate contains a
        // controller/action that has no hardcodes.
        $controllerList[] = "*";
        $actionList[] = "*";

        $actionList = array_unique($actionList);
        $controllerList = array_unique($controllerList);

        // Go through our list again, assemble the controllers/actions we'll
        // add each route to. If its hardcoded, we only add it to that dict key.
        // Otherwise we add it to every hardcode since it can be changed.
        $gendict = array();  // Our generated two-deep hash
        foreach ($this->matchList as $route) {
            if ($route->static) {
                continue;
            }
            $clist = $controllerList;
            $alist = $actionList;
            if (in_array('controller', $route->hardCoded)) {
                $clist = array($route->defaults['controller']);
            }
            if (in_array('action', $route->hardCoded)) {
                $alist = array($route->defaults['action']);
            }
            foreach ($clist as $controller) {
                foreach ($alist as $action) {
                    if (in_array($controller, array_keys($gendict))) {
                        $actiondict = &$gendict[$controller];
                    } else {
                        $gendict[$controller] = array();
                        $actiondict = &$gendict[$controller];
                    }
                    if (in_array($action, array_keys($actiondict))) {
                        $tmp = $actiondict[$action];
                    } else {
                        $tmp = array(array(), array());
                    }
                    $tmp[0][] = $route;
                    $actiondict[$action] = $tmp;
                }
            }
        }
        if (!isset($gendict['*'])) {
            $gendict['*'] = array();
        }
        $this->_gendict = $gendict;
        $this->_createdGens = true;
    }

    /**
     * Creates the regexes for all connected routes
     *
     * @param  array $clist  controller list, controller_scan will be used otherwise
     * @return void
     */
    public function createRegs($clist = null)
    {
        if ($clist === null) {
            if ($this->directory === null) {
                $clist = call_user_func($this->controllerScan);
            } else {
                $clist = call_user_func($this->controllerScan, $this->directory);
            }
        }

        foreach ($this->maxKeys as $key => $val) {
            foreach ($val as $route) {
                $route->makeRegexp($clist);
            }
        }

        // Create our regexp to strip the prefix
        if (!empty($this->prefix)) {
            $this->_regPrefix = $this->prefix . '(.*)';
        }
        $this->_createdRegs = true;
    }

    /**
     * Internal Route matcher
     *
     * Matches a URL against a route, and returns a tuple (array) of the
     * match dict (array) and the route object if a match is successful,
     * otherwise it returns null.
     *
     * @param   string      $url  URL to match
     * @return  null|array        Match data if matched, otherwise null
     */
    protected function _match($url)
    {
        if (!$this->_createdRegs && !empty($this->controllerScan)) {
            $this->createRegs();
        } else if (!$this->_createdRegs) {
            $msg = 'You must generate the regular expressions before matching.';
            throw new Horde_Routes_Exception($msg);
        }

        if ($this->alwaysScan) {
            $this->createRegs();
        }

        $matchLog = array();
        if (!empty($this->prefix)) {
            if (preg_match('@' . $this->_regPrefix . '@', $url)) {
                $url = preg_replace('@' . $this->_regPrefix . '@', '$1', $url);
                if (empty($url)) {
                    $url = '/';
                }
            }
            else {
                return array(null, null, $matchLog);
            }
        }

        foreach ($this->matchList as $route) {
            if ($route->static) {
                if ($this->debug) {
                    $matchLog[] = array('route' => $route, 'static' => true);
                }
                continue;
            }

            $match = $route->match($url, array('environ'          => $this->environ,
                                               'subDomains'       => $this->subDomains,
                                               'subDomainsIgnore' => $this->subDomainsIgnore,
                                               'domainMatch'      => $this->domainMatch));
            if ($this->debug) {
                $matchLog[] = array('route' => $route, 'regexp' => (bool)$match);
            }
            if ($match) {
                return array($match, $route, $matchLog);
            }
        }

        return array(null, null, $matchLog);
    }

    /**
     * Match a URL against one of the routes contained.
     * It will return null if no valid match is found.
     *
     * Usage:
     *   $resultdict = $m->match('/joe/sixpack');
     *
     * @param  string      $url  URL to match
     * @param  array|null        Array if matched, otherwise null
     */
    public function match($url)
    {
        if (!strlen($url)) {
            $msg = 'No URL provided, the minimum URL necessary to match is "/"';
            throw new Horde_Routes_Exception($msg);
        }

        $result = $this->_match($url);

        if ($this->debug) {
            return array($result[0], $result[1], $result[2]);
        }

        return ($result[0]) ? $result[0] : null;
    }

    /**
     * Match a URL against one of the routes contained.
     * It will return null if no valid match is found, otherwise
     * a result dict (array) and a route object is returned.
     *
     * Usage:
     *   list($resultdict, $resultobj) = $m->match('/joe/sixpack');
     *
     * @param  string      $url  URL to match
     * @param  array|null        Array if matched, otherwise null
     */
    public function routematch($url)
    {
        $result = $this->_match($url);

        if ($this->debug) {
            return array($result[0], $result[1], $result[2]);
        }

        return ($result[0]) ? array($result[0], $result[1]) : null;
    }

    /**
     * Generates the URL from a given set of keywords
     * Returns the URL text, or null if no URL could be generated.
     *
     * Usage:
     *   $m->generate(array('controller' => 'content', 'action' => 'view', 'id' => 10));
     *
     * @param   array        $kargs  Keyword arguments (key/value pairs)
     * @return  null|string          URL text or null
     */
    public function generate($kargs = array())
    {
        // Generate ourself if we haven't already
        if (!$this->_createdGens) {
            $this->_createGens();
        }

        if ($this->appendSlash) {
            $kargs['_appendSlash'] = true;
        }

        if (!$this->explicit) {
            if (!in_array('controller', array_keys($kargs))) {
                $kargs['controller'] = 'content';
            }
            if (!in_array('action', array_keys($kargs))) {
                $kargs['action'] = 'index';
            }
        }

        $environ = $this->environ;
        $controller = isset($kargs['controller']) ? $kargs['controller'] : null;
        $action = isset($kargs['action']) ? $kargs['action'] : null;

        // If the URL didn't depend on the SCRIPT_NAME, we'll cache it
        // keyed by just the $kargs; otherwise we need to cache it with
        // both SCRIPT_NAME and $kargs:
        $cacheKey = $kargs;
        if (!empty($environ['SCRIPT_NAME'])) {
            $cacheKeyScriptName = sprintf('%s:%s', $environ['SCRIPT_NAME'], $cacheKey);
        } else {
            $cacheKeyScriptName = $cacheKey;
        }

        // Check the URL cache to see if it exists, use it if it does.
        foreach (array($cacheKey, $cacheKeyScriptName) as $key) {
            if (in_array($key, array_keys($this->urlCache))) {
                return $this->urlCache[$key];
            }
        }

        $actionList = isset($this->_gendict[$controller]) ? $this->_gendict[$controller] : $this->_gendict['*'];

        list($keyList, $sortCache) =
            (isset($actionList[$action])) ? $actionList[$action] : ((isset($actionList['*'])) ? $actionList['*'] : array(null, null));

        if ($keyList === null) {
            return null;
        }

        $keys = array_keys($kargs);

        // necessary to pass $keys to _keysort() callback used by PHP's usort()
        $this->_keysortTmp = $keys;

        $newList = array();
        foreach ($keyList as $route) {
            $tmp = Horde_Routes_Utils::arraySubtract($route->minKeys, $keys);
            if (count($tmp) == 0) {
                $newList[] = $route;
            }
        }
        $keyList = $newList;

        // inline python function keysort() moved below as _keycmp()

        $this->_keysort($keyList);

        foreach ($keyList as $route) {
            $fail = false;
            foreach ($route->hardCoded as $key) {
                $kval = isset($kargs[$key]) ? $kargs[$key] : null;
                if ($kval == null) {
                    continue;
                }

                if ($kval != $route->defaults[$key]) {
                    $fail = true;
                    break;
                }
            }
            if ($fail) {
                continue;
            }

            $path = $route->generate($kargs);

            if ($path) {
                if ($this->prefix) {
                    $path = $this->prefix . $path;
                }
                if (!empty($environ['SCRIPT_NAME']) && !$route->absolute) {
                    $path = $environ['SCRIPT_NAME'] . $path;
                    $key = $cacheKeyScriptName;
                } else {
                    $key = $cacheKey;
                }
                if ($this->urlCache != null) {
                    $this->urlCache[$key] = $path;
                }
                return $path;
            } else {
                continue;
            }
        }
        return null;
    }

    /**
     * Generate routes for a controller resource
     *
     * The $memberName name should be the appropriate singular version of the
     * resource given your locale and used with members of the collection.
     *
     * The $collectionName name will be used to refer to the resource
     * collection methods and should be a plural version of the $memberName
     * argument. By default, the $memberName name will also be assumed to map
     * to a controller you create.
     *
     * The concept of a web resource maps somewhat directly to 'CRUD'
     * operations. The overlying things to keep in mind is that mapping a
     * resource is about handling creating, viewing, and editing that
     * resource.
     *
     * All keyword arguments ($kargs) are optional.
     *
     * ``controller``
     *     If specified in the keyword args, the controller will be the actual
     *     controller used, but the rest of the naming conventions used for
     *     the route names and URL paths are unchanged.
     *
     * ``collection``
     *     Additional action mappings used to manipulate/view the entire set of
     *     resources provided by the controller.
     *
     *     Example::
     *
     *         $map->resource('message', 'messages',
     *                        array('collection' => array('rss' => 'GET)));
     *         # GET /message;rss (maps to the rss action)
     *         # also adds named route "rss_message"
     *
     * ``member``
     *      Additional action mappings used to access an individual 'member'
     *      of this controllers resources.
     *
     *      Example::
     *
     *          $map->resource('message', 'messages',
     *                         array('member' => array('mark' => 'POST')));
     *          # POST /message/1;mark (maps to the mark action)
     *          # also adds named route "mark_message"
     *
     *  ``new``
     *      Action mappings that involve dealing with a new member in the
     *      controller resources.
     *
     *      Example::
     *
     *          $map->resource('message', 'messages',
     *                         array('new' => array('preview' => 'POST')));
     *          # POST /message/new;preview (maps to the preview action)
     *          # also adds a url named "preview_new_message"
     *
     *  ``pathPrefix``
     *      Prepends the URL path for the Route with the pathPrefix given.
     *      This is most useful for cases where you want to mix resources
     *      or relations between resources.
     *
     *  ``namePrefix``
     *      Perpends the route names that are generated with the namePrefix
     *      given. Combined with the pathPrefix option, it's easy to
     *      generate route names and paths that represent resources that are
     *      in relations.
     *
     *      Example::
     *
     *          map.resource('message', 'messages',
     *                       array('controller' => 'categories',
     *                             'pathPrefix' => '/category/:category_id',
     *                             'namePrefix' => 'category_')));
     *              # GET /category/7/message/1
     *              # has named route "category_message"
     *
     *  ``parentResource``
     *      An assoc. array containing information about the parent resource,
     *      for creating a nested resource. It should contain the ``$memberName``
     *      and ``collectionName`` of the parent resource. This assoc. array will
     *      be available via the associated ``Route`` object which can be
     *      accessed during a request via ``request.environ['routes.route']``
     *
     *      If ``parentResource`` is supplied and ``pathPrefix`` isn't,
     *      ``pathPrefix`` will be generated from ``parentResource`` as
     *      "<parent collection name>/:<parent member name>_id".
     *
     *      If ``parentResource`` is supplied and ``namePrefix`` isn't,
     *      ``namePrefix`` will be generated from ``parentResource`` as
     *      "<parent member name>_".
     *
     *      Example::
     *
     *          $m = new Horde_Routes_Mapper();
     *          $utils = $m->utils;
     *
     *          $m->resource('location', 'locations',
     *                       array('parentResource' =>
     *                              array('memberName' => 'region',
     *                                    'collectionName' => 'regions'))));
     *          # pathPrefix is "regions/:region_id"
     *          # namePrefix is "region_"
     *
     *          $utils->urlFor('region_locations', array('region_id'=>13));
     *          # '/regions/13/locations'
     *
     *          $utils->urlFor('region_new_location', array('region_id'=>13));
     *          # '/regions/13/locations/new'
     *
     *          $utils->urlFor('region_location',
     *                        array('region_id'=>13, 'id'=>60));
     *          # '/regions/13/locations/60'
     *
     *          $utils->urlFor('region_edit_location',
     *                        array('region_id'=>13, 'id'=>60));
     *          # '/regions/13/locations/60;edit'
     *
     *   Overriding generated ``pathPrefix``::
     *
     *      $m = new Horde_Routes_Mapper();
     *      $utils = new Horde_Routes_Utils();
     *
     *      $m->resource('location', 'locations',
     *                   array('parentResource' =>
     *                         array('memberName' => 'region',
     *                               'collectionName' => 'regions'),
     *                         'pathPrefix' => 'areas/:area_id')));
     *       # name prefix is "region_"
     *
     *       $utils->urlFor('region_locations', array('area_id'=>51));
     *       # '/areas/51/locations'
     *
     *   Overriding generated ``namePrefix``::
     *
     *       $m = new Horde_Routes_Mapper
     *      $m->resource('location', 'locations',
     *                   array('parentResource' =>
     *                         array('memberName' => 'region',
     *                               'collectionName' => 'regions'),
     *                         'namePrefix' => '')));
     *       # pathPrefix is "regions/:region_id"
     *
     *       $utils->urlFor('locations', array('region_id'=>51));
     *       # '/regions/51/locations'
     *
     * @param  string  $memberName      Singular version of the resource name
     * @param  string  $collectionName  Collection name (plural of $memberName)
     * @param  array   $kargs           Keyword arguments (see above)
     * @return void
     */
    public function resource($memberName, $collectionName, $kargs = array())
    {
        $defaultKargs = array('collection' => array(),
                              'member' => array(),
                              'new' => array(),
                              'pathPrefix' => null,
                              'namePrefix' => null,
                              'parentResource' => null);
        $kargs = array_merge($defaultKargs, $kargs);

        // Generate ``pathPrefix`` if ``pathPrefix`` wasn't specified and
        // ``parentResource`` was. Likewise for ``namePrefix``. Make sure
        // that ``pathPrefix`` and ``namePrefix`` *always* take precedence if
        // they are specified--in particular, we need to be careful when they
        // are explicitly set to "".
        if ($kargs['parentResource'] !== null) {
            if ($kargs['pathPrefix'] === null) {
                $kargs['pathPrefix'] = $kargs['parentResource']['collectionName'] . '/:'
                                     . $kargs['parentResource']['memberName']     . '_id';
            }
            if ($kargs['namePrefix'] === null) {
                $kargs['namePrefix'] = $kargs['parentResource']['memberName'] . '_';
            }
        } else {
            if ($kargs['pathPrefix'] === null) {
                $kargs['pathPrefix'] = '';
            }
            if ($kargs['namePrefix'] === null) {
                $kargs['namePrefix'] = '';
            }
        }

        // Ensure the edit and new actions are in and GET
        $kargs['member']['edit'] = 'GET';
        $kargs['new']['new'] = 'GET';

        // inline python method swap() moved below as _swap()

        $collectionMethods = $this->_swap($kargs['collection'], array());
        $memberMethods = $this->_swap($kargs['member'], array());
        $newMethods = $this->_swap($kargs['new'], array());

        // Insert create, update, and destroy methods
        if (!isset($collectionMethods['POST'])) {
            $collectionMethods['POST'] = array();
        }
        array_unshift($collectionMethods['POST'], 'create');

        if (!isset($memberMethods['PUT'])) {
            $memberMethods['PUT'] = array();
        }
        array_unshift($memberMethods['PUT'], 'update');

        if (!isset($memberMethods['DELETE'])) {
            $memberMethods['DELETE'] = array();
        }
        array_unshift($memberMethods['DELETE'], 'delete');

        // If there's a path prefix option, use it with the controller
        $controller = $this->_stripSlashes($collectionName);
        $kargs['pathPrefix'] = $this->_stripSlashes($kargs['pathPrefix']);
        if ($kargs['pathPrefix']) {
            $path = $kargs['pathPrefix'] . '/' . $controller;
        } else {
            $path = $controller;
        }
        $collectionPath = $path;
        $newPath = $path . '/new';
        $memberPath = $path . '/:(id)';

        $options = array(
            'controller' => (isset($kargs['controller']) ? $kargs['controller'] : $controller),
            '_memberName'     => $memberName,
            '_collectionName' => $collectionName,
            '_parentResource' => $kargs['parentResource']
        );

        // inline python method requirements_for() moved below as _requirementsFor()

        // Add the routes for handling collection methods
        foreach ($collectionMethods as $method => $lst) {
            $primary = ($method != 'GET' && isset($lst[0])) ? array_shift($lst) : null;
            $routeOptions = $this->_requirementsFor($method, $options);

            foreach ($lst as $action) {
                $routeOptions['action'] = $action;
                $routeName = sprintf('%s%s_%s', $kargs['namePrefix'], $action, $collectionName);

                $this->connect($routeName,
                               sprintf("%s;%s", $collectionPath, $action),
                               $routeOptions);
                $this->connect('formatted_' . $routeName,
                               sprintf("%s.:(format);%s", $collectionPath, $action),
                               $routeOptions);
            }
            if ($primary) {
                $routeOptions['action'] = $primary;
                $this->connect($collectionPath, $routeOptions);
                $this->connect($collectionPath . '.:(format)', $routeOptions);
            }
        }

        // Specifically add in the built-in 'index' collection method and its
        // formatted version
        $connectkargs = array('action' => 'index',
                              'conditions' => array('method' => array('GET')));
        $this->connect($kargs['namePrefix'] . $collectionName,
                       $collectionPath,
                       array_merge($connectkargs, $options));

        $connectkargs = array('action' => 'index',
                              'conditions' => array('method' => array('GET')));
        $this->connect('formatted_' . $kargs['namePrefix'] . $collectionName,
                       $collectionPath . '.:(format)',
                       array_merge($connectkargs, $options));

        // Add the routes that deal with new resource methods
        foreach ($newMethods as $method => $lst) {
            $routeOptions = $this->_requirementsFor($method, $options);
            foreach ($lst as $action) {
                if ($action == 'new' && $newPath) {
                    $path = $newPath;
                } else {
                    $path = sprintf('%s;%s', $newPath, $action);
                }

                $name = 'new_' . $memberName;
                if ($action != 'new') {
                    $name = $action . '_' . $name;
                }
                $routeOptions['action'] = $action;
                $this->connect($kargs['namePrefix'] . $name, $path, $routeOptions);

                if ($action == 'new' && $newPath) {
                    $path = $newPath . '.:(format)';
                } else {
                    $path = sprintf('%s.:(format);%s', $newPath, $action);
                }

                $this->connect('formatted_' . $kargs['namePrefix'] . $name,
                               $path, $routeOptions);
            }
        }

        $requirementsRegexp = '[\w\-_]+';

        // Add the routes that deal with member methods of a resource
        foreach ($memberMethods as $method => $lst) {
            $routeOptions = $this->_requirementsFor($method, $options);
            $routeOptions['requirements'] = array('id' => $requirementsRegexp);

            if (!in_array($method, array('POST', 'GET', 'any'))) {
                $primary = array_shift($lst);
            } else {
                $primary = null;
            }

            foreach ($lst as $action) {
                $routeOptions['action'] = $action;
                $this->connect(sprintf('%s%s_%s', $kargs['namePrefix'], $action, $memberName),
                               sprintf('%s;%s', $memberPath, $action),
                               $routeOptions);
                $this->connect(sprintf('formatted_%s%s_%s', $kargs['namePrefix'], $action, $memberName),
                               sprintf('%s.:(format);%s', $memberPath, $action),
                               $routeOptions);
            }

            if ($primary) {
                $routeOptions['action'] = $primary;
                $this->connect($memberPath, $routeOptions);
            }
        }

        // Specifically add the member 'show' method
        $routeOptions = $this->_requirementsFor('GET', $options);
        $routeOptions['action'] = 'show';
        $routeOptions['requirements'] = array('id' => $requirementsRegexp);
        $this->connect($kargs['namePrefix'] . $memberName, $memberPath, $routeOptions);
        $this->connect('formatted_' . $kargs['namePrefix'] . $memberName,
                       $memberPath . '.:(format)', $routeOptions);
    }

    /**
     * Returns a new dict to be used for all route creation as
     * the route options.
     * @see resource()
     *
     * @param  string  $method   Request method ('get', 'post', etc.) or 'any'
     * @param  array   $options  Assoc. array to populate with 'conditions' key
     * @return                   $options populated
     */
    protected function _requirementsFor($meth, $options)
    {
        if ($meth != 'any') {
            $options['conditions'] = array('method' => array(strtoupper($meth)));
        }
        return $options;
    }

    /**
     * Swap the keys and values in the dict, and uppercase the values
     * from the dict during the swap.
     * @see resource()
     *
     * @param  array  $dct     Input dict (assoc. array)
     * @param  array  $newdct  Output dict to populate
     * @return array           $newdct populated
     */
    protected function _swap($dct, $newdct)
    {
        foreach ($dct as $key => $val) {
            $newkey = strtoupper($val);
            if (!isset($newdct[$newkey])) {
                $newdct[$newkey] = array();
            }
            $newdct[$newkey][] = $key;
        }
        return $newdct;
    }

    /**
     * Sort an array of Horde_Routes_Routes to using _keycmp() for the comparision
     * to order them ideally for matching.
     *
     * An unfortunate property of PHP's usort() is that if two members compare
     * equal, their order in the sorted array is undefined (see PHP manual).
     * This is unsuitable for us because the order that the routes were
     * connected to the mapper is significant.
     *
     * Uses this method uses merge sort algorithm based on the
     * comments in http://www.php.net/usort
     *
     * @param  array  $array  Array Horde_Routes_Route objects to sort (by reference)
     * @return void
     */
    protected function _keysort(&$array)
    {
        // arrays of size < 2 require no action.
        if (count($array) < 2) { return; }

        // split the array in half
        $halfway = count($array) / 2;
        $array1 = array_slice($array, 0, $halfway);
        $array2 = array_slice($array, $halfway);

        // recurse to sort the two halves
        $this->_keysort($array1);
        $this->_keysort($array2);

        // if all of $array1 is <= all of $array2, just append them.
        if ($this->_keycmp(end($array1), $array2[0]) < 1) {
            $array = array_merge($array1, $array2);
            return;
        }

        // merge the two sorted arrays into a single sorted array
        $array = array();
        $ptr1 = 0;
        $ptr2 = 0;
        while ($ptr1 < count($array1) && $ptr2 < count($array2)) {
            if ($this->_keycmp($array1[$ptr1], $array2[$ptr2]) < 1) {
                $array[] = $array1[$ptr1++];
            }
            else {
                $array[] = $array2[$ptr2++];
            }
        }

        // merge the remainder
        while ($ptr1 < count($array1)) { $array[] = $array1[$ptr1++]; }
        while ($ptr2 < count($array2)) { $array[] = $array2[$ptr2++]; }
        return;
    }

    /**
     * Compare two Horde_Route_Routes objects by their keys against
     * the instance variable $keysortTmp.  Used by _keysort().
     *
     * @param  array  $a  First dict (assoc. array)
     * @param  array  $b  Second dict
     * @return integer
     */
    protected function _keycmp($a, $b)
    {
        $keys = $this->_keysortTmp;
        $am = $a->minKeys;
        $a = $a->maxKeys;
        $b = $b->maxKeys;

        $lendiffa = count(array_diff($keys, $a));
        $lendiffb = count(array_diff($keys, $b));

        // If they both match, don't switch them
        if ($lendiffa == 0 && $lendiffb == 0) {
            return 0;
        }

        // First, if $a matches exactly, use it
        if ($lendiffa == 0) {
            return -1;
        }

        // Or $b matches exactly, use it
        if ($lendiffb == 0) {
            return 1;
        }

        // Neither matches exactly, return the one with the most in common
        if ($this->_cmp($lendiffa, $lendiffb) != 0) {
            return $this->_cmp($lendiffa, $lendiffb);
        }

        // Neither matches exactly, but if they both have just as much in common
        if (count($this->_arrayUnion($keys, $b)) == count($this->_arrayUnion($keys, $a))) {
            return $this->_cmp(count($a), count($b));

        // Otherwise, we return the one that has the most in common
        } else {
            return $this->_cmp(count($this->_arrayUnion($keys, $b)), count($this->_arrayUnion($keys, $a)));
        }
    }

    /**
     * Create a union of two arrays.
     *
     * @param  array  $a  First array
     * @param  array  $b  Second array
     * @return array      Union of $a and $b
     */
    protected function _arrayUnion($a, $b)
    {
        return array_merge(array_diff($a, $b), array_diff($b, $a), array_intersect($a, $b));
    }

    /**
     * Equivalent of Python's cmp() function.
     *
     * @param  integer|float  $a  First item to compare
     * @param  integer|flot   $b  Second item to compare
     * @param  integer            Result of comparison
     */
    protected function _cmp($a, $b)
    {
        if ($a < $b) {
            return -1;
        }
        if ($a == $b) {
            return 0;
        }
        return 1;
    }

    /**
     * Trims slashes from the beginning or end of a part/URL.
     *
     * @param  string  $name  Part or URL with slash at begin/end
     * @return string         Part or URL with begin/end slashes removed
     */
    protected function _stripSlashes($name)
    {
        if (substr($name, 0, 1) == '/') {
            $name = substr($name, 1);
        }
        if (substr($name, -1, 1) == '/') {
            $name = substr($name, 0, -1);
        }
        return $name;
    }

}

