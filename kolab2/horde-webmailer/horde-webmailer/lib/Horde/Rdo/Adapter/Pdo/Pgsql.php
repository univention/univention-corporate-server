<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * PostgreSQL PDO Horde_Rdo adapter
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Adapter_Pdo_Pgsql extends Horde_Rdo_Adapter_Pdo {

    /**
     * Get the appropriate DML object and call the parent constructor.
     *
     * @param array $options Connection options.
     */
    public function __construct($options = array())
    {
        $this->dml = new Horde_Rdo_Query_Builder_Pgsql();
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
        $r = $this->select('SELECT * FROM ' . $this->dml->quoteIdentifier($model->table) . ' LIMIT 0');
        $indices = array();
        for ($i = 0; $i < $r->columnCount(); ++$i) {
            $col = $r->getColumnMeta($i);
            $model->addField($col['name']);
            $model->setFieldType($col['name'], $col['native_type']);
            $indices[$i + 1] = $col['name'];
        }

        $sql = 'SELECT i.indisunique, i.indisprimary, i.indkey FROM pg_class c, ' .
            'pg_index i WHERE c.oid = i.indrelid AND c.relname = ' .
            $this->_db->quote($model->table);

        $idxresult = $this->select($sql);
        while ($idx = $idxresult->fetch()) {
            if ($idx['indisprimary'] == 't') {
                $keys = explode(' ', $idx['indkey']);
                foreach ($keys as $key) {
                    // TODO: accumulate composite keys.
                    $model->key = $indices[$key];
                }
            }
        }
    }

}
