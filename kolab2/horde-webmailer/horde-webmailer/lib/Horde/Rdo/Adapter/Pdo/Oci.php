<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * OCI PDO Horde_Rdo adapter
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Adapter_Pdo_Oci extends Horde_Rdo_Adapter_Pdo {

    /**
     * Get the appropriate DML object and call the parent constructor.
     *
     * @param array $options Connection options.
     */
    public function __construct($options = array())
    {
        $this->dml = new Horde_Rdo_Query_Builder_Oracle();
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
        $table = $this->dml->quoteIdentifier(strtoupper($model->table));
        $tblinfo = $this->select('SELECT column_name, data_type, data_length, nullable, data_default FROM all_tab_columns WHERE table_name = '
                                 . $table);
        while ($col = $tblinfo->fetch()) {
            $model->addField($col['column_name'], array('type' => $col['data_type'],
                                                        'null' => ($col['nullable'] != 'N'),
                                                        'default' => $col['data_default'],
                                                        'length' => $col['data_length']));
        }

        // Only fetch the first primary key for now.
        $model->key = $this->selectOne('SELECT DISTINCT b.column_name FROM all_constraints a, all_cons_columns b WHERE a.table_name = '
                                       . $table . ' AND a.constraint_type = \'P\' AND b.constraint_name = a.constraint_name');
    }

    /**
     */
    protected function _lastInsertId($sequence)
    {
        $data = $this->selectOne('SELECT ' . $this->dml->quoteIdentifier($sequence) . '.currval FROM dual');
    }

}
