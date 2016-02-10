$password =  "%(domain_password)s"| ConvertTo-SecureString -asPlainText -Force
$domain = "%(domain)s"
$username = "%(domain)s\%(domain_user)s" 
$credential = New-Object System.Management.Automation.PSCredential($username,$password)
Add-Computer -DomainName $domain -Credential $credential
