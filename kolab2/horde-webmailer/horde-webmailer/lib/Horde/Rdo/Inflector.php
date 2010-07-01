<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Rdo Inflector class.
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Inflector {

    /**
     * Rules for pluralizing English nouns.
     *
     * @var array
     */
    protected static $_pluralizationRules = array(
        '/move$/i' => 'moves',
        '/sex$/i' => 'sexes',
        '/child$/i' => 'children',
        '/man$/i' => 'men',
        '/foot$/i' => 'feet',
        '/person$/i' => 'people',
        '/(quiz)$/i' => '$1zes',
        '/^(ox)$/i' => '$1en',
        '/(m|l)ouse$/i' => '$1ice',
        '/(matr|vert|ind)ix|ex$/i' => '$1ices',
        '/(x|ch|ss|sh)$/i' => '$1es',
        '/([^aeiouy]|qu)ies$/i' => '$1y',
        '/([^aeiouy]|qu)y$/i' => '$1ies',
        '/(?:([^f])fe|([lr])f)$/i' => '$1$2ves',
        '/sis$/i' => 'ses',
        '/([ti])um$/i' => '$1a',
        '/(buffal|tomat)o$/i' => '$1oes',
        '/(bu)s$/i' => '$1ses',
        '/(alias|status)$/i' => '$1es',
        '/(octop|vir)us$/i' => '$1i',
        '/(ax|test)is$/i' => '$1es',
        '/s$/i' => 's',
        '/$/' => 's',
    );

    /**
     * Rules for singularizing English nouns.
     *
     * @var array
     */
    protected static $_singularizationRules = array(
        '/cookies$/i' => 'cookie',
        '/moves$/i' => 'move',
        '/sexes$/i' => 'sex',
        '/children$/i' => 'child',
        '/men$/i' => 'man',
        '/feet$/i' => 'foot',
        '/people$/i' => 'person',
        '/databases$/i'=> 'database',
        '/(quiz)zes$/i' => '\1',
        '/(matr)ices$/i' => '\1ix',
        '/(vert|ind)ices$/i' => '\1ex',
        '/^(ox)en/i' => '\1',
        '/(alias|status)es$/i' => '\1',
        '/([octop|vir])i$/i' => '\1us',
        '/(cris|ax|test)es$/i' => '\1is',
        '/(shoe)s$/i' => '\1',
        '/(o)es$/i' => '\1',
        '/(bus)es$/i' => '\1',
        '/([m|l])ice$/i' => '\1ouse',
        '/(x|ch|ss|sh)es$/i' => '\1',
        '/(m)ovies$/i' => '\1ovie',
        '/(s)eries$/i' => '\1eries',
        '/([^aeiouy]|qu)ies$/i' => '\1y',
        '/([lr])ves$/i' => '\1f',
        '/(tive)s$/i' => '\1',
        '/(hive)s$/i' => '\1',
        '/([^f])ves$/i' => '\1fe',
        '/(^analy)ses$/i' => '\1sis',
        '/((a)naly|(b)a|(d)iagno|(p)arenthe|(p)rogno|(s)ynop|(t)he)ses$/i' => '\1\2sis',
        '/([ti])a$/i' => '\1um',
        '/(n)ews$/i' => '\1ews',
        '/(.*)s$/i' => '\1',
    );

    /**
     * @var array An array of words with the same singular and plural
     * spellings.
     */
    protected static $_singularEqualsPlural = array(
        'aircraft',
        'cannon',
        'deer',
        'equipment',
        'fish',
        'information',
        'money',
        'moose',
        'rice',
        'series',
        'sheep',
        'species',
        'swine',
    );

    /**
     * Transform a table name to a mapper class name.
     *
     * @param string $table The database table name to look up.
     *
     * @return Horde_Rdo_Mapper A new Mapper instance if it exists, else null.
     */
    public function tableToMapper($table)
    {
        if (class_exists(($class = ucwords($table) . 'Mapper'))) {
            return new $class;
        }
        return null;
    }

    /**
     * Transform a mapper instance to a database table name.
     *
     * @param Horde_Rdo_Mapper The Mapper instance to get the database table name for.
     *
     * @return string The database table name.
     */
    public function mapperToTable($mapper)
    {
        return $this->pluralize(strtolower(str_replace('Mapper', '', get_class($mapper))));
    }

    /**
     * Transform a mapper class to and entity class name.
     *
     * @param Horde_Rdo_Mapper $mapper The Mapper to get the entity class for.
     *
     * @return string A Horde_Rdo_Base concrete class name if the class exists, else null.
     */
    public function mapperToEntity($mapper)
    {
        $class = str_replace('Mapper', '', get_class($mapper));
        if (class_exists($class)) {
            return $class;
        }
        return null;
    }

    /**
     * Singular English word to pluralize.
     *
     * @param string $word Word to pluralize.
     *
     * @return string Plural form of $word.
     */
    public function pluralize($word)
    {
        if (in_array($word, self::$_singularEqualsPlural)) {
            return $word;
        }

        /*
        foreach (self::$_pluralizationRules as $regexp => $replacement) {
            if (preg_match($regexp, $word)) {
                return preg_replace($regexp, $replacement, $word);
            }
        }
        return $word;
        */

        foreach (self::$_pluralizationRules as $regexp => $replacement) {
            $plural = preg_replace($regexp, $replacement, $word, -1, $matches);
            if ($matches > 0) {
                return $plural;
            }
        }

        return $word;
    }

    /**
     * Plural English word to singularize.
     *
     * @param string $word Word to singularize.
     *
     * @return string Singular form of $word.
     */
    public function singularize($word)
    {
        if (in_array($word, self::$_singularEqualsPlural)) {
            return $word;
        }

        foreach (self::$_singularizationRules as $regexp => $replacement) {
            $singular = preg_replace($regexp, $replacement, $word, -1, $matches);
            if ($matches > 0) {
                return $singular;
            }
        }

        return $word;
    }

}
