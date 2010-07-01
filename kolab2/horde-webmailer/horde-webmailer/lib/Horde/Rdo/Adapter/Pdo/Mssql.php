<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * MS-SQL PDO Horde_Rdo adapter
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Adapter_Pdo_Mssql extends Horde_Rdo_Adapter_Pdo {

    /**
     * Get the appropriate DML object and call the parent constructor.
     *
     * @param array $options Connection options.
     */
    public function __construct($options = array())
    {
        $this->dml = new Horde_Rdo_Query_Builder_Mssql();
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
        $tblinfo = $this->select('EXEC sp_columns @table_name = ' . $this->dml->quoteIdentifier($model->table));
        while ($col = $tblinfo->fetch()) {
            if (strpos($col['type_name'], ' ') !== false) {
                list($type, $identity) = explode(' ', $col['type_name']);
            } else {
                $type = $col['type_name'];
                $identity = '';
            }

            $model->addField($col['column_name'], array('type' => $type,
                                                        'null' => !(bool)$col['is_nullable'] == 'NO',
                                                        'default' => $col['column_def']));
            if (strtolower($identity) == 'identity') {
                $model->key = $col['column_name'];
            }
        }
    }

    /**
     * Build a connection string and connect to the database server.
     */
    protected function _connect()
    {
        parent::_connect();
        $this->_db->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
    }

    /**
     */
    protected function _lastInsertId($sequence)
    {
        return $this->selectOne('SELECT @@IDENTITY');
    }

}
