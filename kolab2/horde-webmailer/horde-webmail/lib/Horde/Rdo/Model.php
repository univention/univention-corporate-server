<?php
/**
 * Model class for Rdo.
 *
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Model {

    /**
     */
    protected $_fields = array();

    /**
     */
    public $table;

    /**
     */
    const INTEGER = 'int';

    /**
     */
    const NUMBER = 'number';

    /**
     */
    const STRING = 'string';

    /**
     */
    const TEXT = 'text';

    /**
     * Fill the model using the mapper's backend.
     */
    public function load($mapper)
    {
        $mapper->adapter->loadModel($this);
    }

    /**
     */
    public static function __set_state($properties)
    {
        $model = new Horde_Rdo_Model();
        foreach ($properties as $key => $val) {
            $model->$key = $val;
        }
    }

    /**
     */
    public function hasField($field)
    {
        return isset($this->_fields[$field]);
    }

    /**
     */
    public function addField($field, $params = array())
    {
        $params = array_merge(array('key' => null, 'null' => false), $params);

        if (!strncasecmp($params['null'], 'n', 1)) {
            $params['null'] = false;
        } elseif (!strncasecmp($params['null'], 'y', 1)) {
            $params['null'] = true;
        }

        $this->_fields[$field] = $params;
        if (isset($params['type'])) {
            $this->setFieldType($field, $params['type']);
        }
    }

    /**
     */
    public function getField($field)
    {
        return isset($this->_fields[$field]) ? $this->_fields[$field] : null;
    }

    /**
     */
    public function getFields()
    {
        return $this->_fields;
    }

    /**
     */
    public function listFields()
    {
        return array_keys($this->_fields);
    }

    /**
     */
    public function setFieldType($field, $rawtype)
    {
        if (stripos($rawtype, 'int') !== false) {
            $this->_fields[$field]['type'] = self::INTEGER;
        } elseif (stripos($rawtype, 'char') !== false) {
            $this->_fields[$field]['type'] = self::STRING;
        } elseif (stripos($rawtype, 'float') !== false
                  || stripos($rawtype, 'decimal') !== false) {
            $this->_fields[$field]['type'] = self::NUMBER;
        } elseif ($rawtype == 'text') {
            $this->_fields[$field]['type'] = self::TEXT;
        }
    }

}
