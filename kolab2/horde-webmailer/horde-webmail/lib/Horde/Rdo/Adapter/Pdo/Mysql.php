<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * MySQL PDO Horde_Rdo adapter
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Adapter_Pdo_Mysql extends Horde_Rdo_Adapter_Pdo {

    /**
     * Get the appropriate DML object and call the parent constructor.
     *
     * @param array $options Connection options.
     */
    public function __construct($options = array())
    {
        $this->dml = new Horde_Rdo_Query_Builder_Mysql();
        parent::__construct($options);
    }

    /**
     * Get a description of the database table that $model is going to
     * reflect.
     *
     * @param Horde_Rdo_Model $model The Model object to load.
     */
    public function loadModel($model)
    {
        $r = $this->select('SHOW COLUMNS FROM ' . $this->dml->quoteIdentifier($model->table));
        while ($f = $r->fetch()) {
            $model->addField($f['Field'], array_change_key_case($f, CASE_LOWER));
            if ($f['Key'] == 'PRI') {
                $model->key = $f['Field'];
            }
        }

        return $model;
    }

    /**
     * Build a connection string and connect to the database server.
     */
    protected function _connect()
    {
        parent::_connect();
        $this->_db->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
        $this->_db->setAttribute(PDO::MYSQL_ATTR_USE_BUFFERED_QUERY, true);
    }

}
