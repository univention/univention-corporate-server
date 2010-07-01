<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Sqlite PDO Horde_Rdo adapter
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Adapter_Pdo_Sqlite extends Horde_Rdo_Adapter_Pdo {

    /**
     * Get the appropriate DML object and call the parent constructor.
     *
     * @param array $options Connection options.
     */
    public function __construct($options = array())
    {
        $this->dml = new Horde_Rdo_Query_Builder_Sqlite();
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
        $tblinfo = $this->select('PRAGMA table_info(' . $this->dml->quoteIdentifier($model->table) . ')');
        while ($col = $tblinfo->fetch()) {
            $model->addField($col['name'], array('type' => $col['type'],
                                                 'null' => !(bool)$col['notnull'],
                                                 'default' => $col['dflt_value']));
            if ($col['pk'] == '1') {
                $model->key = $col['name'];
            }
        }
    }

    /**
     * Build a connection string and connect to the database server.
     */
    protected function _connect()
    {
        if (!$this->getOption('dsn')) {
            $this->setOption('dsn', $this->getOption('database'));
        }
        parent::_connect();
        $this->_db->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
    }

}
