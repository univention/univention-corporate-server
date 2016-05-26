#$d = [adsi]"LDAP://w2k12.test"
#$d.PSBase.UserName = "w2k12\Administrator"
#$d.PSBase.Password = "univention"
#
#$searcher = New-Object System.DirectoryServices.DirectorySearcher($d)
#$searcher.filter = "(sAMAccountName=test1)"

#$Results = $searcher.FindOne()
#
#
#
#If ($Results -eq $Null) {"Users does not exist in AD"}
#Else {
#   "User found in AD"
#   $Results
#   }
#
#$name = "test7"
#
##$new = $d.Create("User", "cn=" + $name)
##$new.Put("sAMAccountName", $name)
##$new.Put("givenName", "test1")
##$new.Put("sn", "test1")
##$new.Put("displayName", "test1")
##$new.Put("Description", "AD User created by VB Script")
##$new.Put("userAccountControl", 544)
##
##$new.SetInfo()
##$new.SetPassword("Univention.99")

