<?php
/**
 * Represent a single query or a tree of many query elements uniformly to clients.
 *
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Query {

    /**
     * @var Horde_Rdo_Mapper
     */
    public $mapper;

    /**
     * @var string
     */
    public $conjunction = 'AND';

    /**
     * @var array
     */
    public $fields = array('*');

    /**
     * @var array
     */
    public $tests = array();

    /**
     * @var array
     */
    public $relationships = array();

    /**
     * @var array
     */
    protected $_sortby = array();

    /**
     * @var integer
     */
    public $limit;

    /**
     * @var integer
     */
    public $limitOffset = null;

    /**
     * Turn any of the acceptable query shorthands into a full
     * Horde_Rdo_Query object. If you pass an existing Horde_Rdo_Query
     * object in, it will be cloned before it's returned so that it
     * can be safely modified.
     *
     * @param mixed $query The query to convert to an object.
     * @param Horde_Rdo_Mapper $mapper The Mapper object governing this query.
     *
     * @return Horde_Rdo_Query The full Horde_Rdo_Query object.
     */
    public static function create($query, $mapper = null)
    {
        if ($query instanceof Horde_Rdo_Query ||
            $query instanceof Horde_Rdo_Query_Literal) {
            $query = clone($query);
            if (!is_null($mapper)) {
                $query->setMapper($mapper);
            }
            return $query;
        }

        $q = new Horde_Rdo_Query($mapper);

        if (is_scalar($query)) {
            $q->addTest($mapper->model->key, '=', $query);
        } elseif ($query) {
            $q->combineWith('AND');
            foreach ($query as $key => $value) {
                $q->addTest($key, '=', $value);
            }
        }

        return $q;
    }

    /**
     * @param  Horde_Rdo_Mapper  $mapper  Rdo mapper base class
     */
    public function __construct($mapper = null)
    {
        $this->setMapper($mapper);
    }

    /**
     * @param Horde_Rdo_Mapper $mapper Rdo mapper base class
     *
     * @return Horde_Rdo_Query Return the query object for fluent chaining.
     */
    public function setMapper($mapper)
    {
        if ($mapper === $this->mapper) {
            return $this;
        }

        $this->mapper = $mapper;

        // Fetch all non-lazy-loaded fields for the mapper.
        $this->setFields($mapper->fields, $mapper->model->table . '.');

        if (!is_null($mapper)) {
            // Add all non-lazy relationships.
            foreach ($mapper->relationships as $relationship => $rel) {
                if (isset($rel['mapper'])) {
                    $m = new $rel['mapper']();
                } else {
                    $m = $this->mapper->inflector->tableToMapper($relationship);
                    if (is_null($m)) {
                        throw new Horde_Rdo_Exception('Unable to find a Mapper class for eager-loading relationship ' . $relationship);
                    }
                }

                // Add the fields for this relationship to the query.
                $this->addFields($m->fields, $m->model->table . '.@');

                switch ($rel['type']) {
                case Horde_Rdo::ONE_TO_ONE:
                case Horde_Rdo::MANY_TO_ONE:
                    if (isset($rel['query'])) {
                        $query = $this->_fillJoinPlaceholders($m, $mapper, $rel['query']);
                    } else {
                        $query = array($mapper->model->table . '.' . $rel['foreignKey'] => new Horde_Rdo_Query_Literal($m->model->table . '.' . $m->model->key));
                    }
                    $this->addRelationship($relationship, array('mapper' => $m,
                                                                'type' => $rel['type'],
                                                                'query' => $query));
                    break;

                case Horde_Rdo::CUSTOM:
                    if ($rel['mode'] == Horde_Rdo::FIND_ALL) {
                        // Don't eager load multiples.
                        continue;
                    }

                    $query = $this->_fillJoinPlaceholders($m, $mapper, $rel['query']);
                    $args = array('mapper' => $m, 'query' => $query);
                    if (isset($rel['join_type'])) {
                        $args['join_type'] = $rel['join_type'];
                    }
                    $this->addRelationship($relationship, $args);
                    break;
                }
            }
        }

        return $this;
    }

    /**
     * @param array $fields The fields to load with this query.
     *
     * @return Horde_Rdo_Query Returns self for fluent method chaining.
     */
    public function setFields($fields, $fieldPrefix = null)
    {
        if (!is_array($fields)) {
            $fields = array($fields);
        }
        if (!is_null($fieldPrefix)) {
            array_walk($fields, array($this, '_prefix'), $fieldPrefix);
        }
        $this->fields = $fields;
        return $this;
    }

    /**
     * @param array $fields Additional Fields to load with this query.
     *
     * @return Horde_Rdo_Query Returns self for fluent method chaining.
     */
    public function addFields($fields, $fieldPrefix = null)
    {
        if (!is_null($fieldPrefix)) {
            array_walk($fields, array($this, '_prefix'), $fieldPrefix);
        }
        $this->fields = array_merge($this->fields, $fields);
    }

    /**
     * @param string $conjunction SQL conjunction such as "AND", "OR".
     */
    public function combineWith($conjunction)
    {
        $this->conjunction = $conjunction;
        return $this;
    }

    /**
     */
    public function addTest($field, $test, $value)
    {
        $this->tests[] = array('field' => $field,
                               'test'  => $test,
                               'value' => $value);
        return $this;
    }

    /**
     */
    public function addRelationship($relationship, $args)
    {
        if (!isset($args['mapper'])) {
            throw new InvalidArgumentException('Relationships must contain a Horde_Rdo_Mapper object.');
        }
        if (!isset($args['table'])) {
            $args['table'] = $args['mapper']->model->table;
        }
        if (!isset($args['type'])) {
            $args['type'] = Horde_Rdo::MANY_TO_MANY;
        }
        if (!isset($args['join_type'])) {
            switch ($args['type']) {
            case Horde_Rdo::ONE_TO_ONE:
            case Horde_Rdo::MANY_TO_ONE:
                $args['join_type'] = 'INNER JOIN';
                break;

            default:
                $args['join_type'] = 'LEFT JOIN';
            }
        }

        $this->relationships[$relationship] = $args;
        return $this;
    }

    /**
     * Add a sorting rule.
     *
     * @param string $field The field to sort by.
     * @param constant $direction Sort ascending (Horde_Rdo::SORT_ASC)
     * or descending (Horde_Rdo::SORT_DESC).
     */
    public function sortBy($field, $direction = Horde_Rdo::SORT_ASC)
    {
        $this->_sortby[] = array($field, $direction);
        return $this;
    }

    /**
     */
    public function clearSort()
    {
        $this->_sortby = array();
        return $this;
    }

    /**
     * Restrict the query to a subset of the results.
     *
     * @param integer $limit Number of items to fetch.
     * @param integer $offset Offset to start fetching at.
     */
    public function limit($limit, $offset = null)
    {
        $this->limit = $limit;
        $this->limitOffset = $offset;
        return $this;
    }

    /**
     * Accessor for any fields that we want some logic around.
     *
     * @param string $key
     */
    public function __get($key)
    {
        switch ($key) {
        case 'sortby':
            if (!$this->_sortby && $this->mapper->defaultSortRules) {
                // Add in any default sort values, if none are already
                // set.
                foreach ($this->mapper->defaultSortRules as $sort) {
                    if (is_array($sort)) {
                        $this->sortBy($sort[0], $sort[1]);
                    } else {
                        $this->sortBy($sort);
                    }
                }
            }
            return $this->_sortby;
        }

        throw new InvalidArgumentException('Undefined property ' . $key);
    }

    /**
     * Callback for array_walk to prefix all elements of an array with
     * a given prefix.
     */
    protected function _prefix(&$fieldName, $key, $prefix)
    {
        $fieldName = $prefix . $fieldName;
    }

    /**
     * Take a query array and replace @field@ placeholders with values
     * that will match in the load query.
     *
     * @param Horde_Rdo_Mapper $m1 Left-hand mapper
     * @param Horde_Rdo_Mapper $m2 Right-hand mapper
     * @param array $query The query to process placeholders on.
     *
     * @return array The query with placeholders filled in.
     */
    protected function _fillJoinPlaceholders($m1, $m2, $query)
    {
        $q = array();
        foreach (array_keys($query) as $field) {
            $value = $query[$field];
            if (preg_match('/^@(.*)@$/', $value, $matches)) {
                $q[$m1->model->table . '.' . $field] = new Horde_Rdo_Query_Literal($m2->model->table . '.' . $matches[1]);
            } else {
                $q[$m1->model->table . '.' . $field] = $value;
            }
        }

        return $q;
    }

}
