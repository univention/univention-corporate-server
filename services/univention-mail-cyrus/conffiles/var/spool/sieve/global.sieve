require "fileinto";
if header :matches "X-Spam-Status" "Yes,*" {
	redirect "@%@mail/antispam/globalfolder@%@";
	stop; 
}
