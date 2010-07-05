<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Horde_Rdo (Rampage Data Objects) namespace - holds constants and
 * global Rdo functions.
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo {

    /**
     * Find mode for returning just the first matching result. The
     * backend will limit the search if possible, and only a single
     * object will be returned (or null).
     */
    const FIND_FIRST = 'FIND_FIRST';

    /**
     * Find mode for returning all results. Even if no results are
     * found an empty iterator will be returned.
     */
    const FIND_ALL = 'FIND_ALL';

    /**
     * One-to-one relationships.
     */
    const ONE_TO_ONE = 1;

    /**
     * One-to-many relationships (this object has many children).
     */
    const ONE_TO_MANY = 2;

    /**
     * Many-to-one relationships (this object is one of many children
     * of a single parent).
     */
    const MANY_TO_ONE = 3;

    /**
     * Many-to-many relationships (this object relates to many
     * objects, each of which relate to many objects of this type).
     */
    const MANY_TO_MANY = 4;

    /**
     * Custom relationships defined by a query. These can be any of
     * the 4 basic relationship types (one-to-one, one-to-many,
     * many-to-one, many-to-many), but also carry additional
     * qualifiers.
     */
    const CUSTOM = 5;

    /**
     * Ascending sort order
     */
    const SORT_ASC = 'ASC';

    /**
     * Descending sort order
     */
    const SORT_DESC = 'DESC';

    /**
     * Global adapter object.
     *
     * @var Horde_Rdo_Adapter
     */
    protected static $_adapter;

    /**
     * Global inflector object.
     *
     * @var Horde_Rdo_Inflector
     */
    protected static $_inflector;

    /**
     * Get the global adapter object.
     *
     * @return Horde_Rdo_Adapter
     */
    public static function getAdapter()
    {
        return self::$_adapter;
    }

    /**
     * Set a global database adapter.
     *
     * @param Horde_Rdo_Adapter $adapter
     */
    public static function setAdapter($adapter)
    {
        self::$_adapter = $adapter;
    }

    /**
     * Get the global inflector object.
     *
     * @return Horde_Rdo_Inflector
     */
    public static function getInflector()
    {
        if (!self::$_inflector) {
            self::$_inflector = new Horde_Rdo_Inflector;
        }
        return self::$_inflector;
    }

    /**
     * Set a custom global inflector.
     *
     * @param Horde_Rdo_Inflector $inflector
     */
    public static function setInflector($inflector)
    {
        self::$_inflector = $inflector;
    }

}
