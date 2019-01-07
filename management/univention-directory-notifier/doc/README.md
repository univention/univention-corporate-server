file:/var/lib/univention-ldap/listener/listener
	:c:macro:FILE_NAME_LISTENER
	List of transactions
	written by OpenLDAP translog overlay (or cascaded UDL -o)
	read by UDN
	Format: text-file with lines `TID:int DN:str CMD:char`

file:/var/lib/univention-ldap/notify/transaction
	:c:macro:FILE_NAME_TF
	List of transactions
	managed by UDN only
	Format: text-file with lines `TID:int DN:str CMD:char`

file:/var/lib/univention-ldap/notify/transaction.index
	:c:macro:FILE_NAME_TF_IDX
	Binary index to map transaction number to file position of transaction line in :file:`transaction`.
	managed by UDN only
	Format: C packed struct
