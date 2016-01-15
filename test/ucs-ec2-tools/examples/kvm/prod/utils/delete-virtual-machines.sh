python - ./$1 <<END
import sys

f = open('./'+sys.argv[1],'r')
fw = open('./output.txt','w')

list = []

for line in f:
	s = line
	if 'kvm_server: ' in s:
		split = s.split(' ')
		fw.write(split[1])
	elif '[UCS' in s:
		if s[0] == '[':
			split = s.split('[')
			split = split[1].split(']')
			fw.write('build_'+split[0]+'\n')
END

#readarray array < ./output.txt
#declare -a array
#let i=0

i=0
count=i
while IFS=$'\n' read -r line_data; do
	#echo "$line_data"
	if [ "$i" = 0 ]; then
		kvm="$line_data"
	elif [ "$i" = 1 ]; then
		master="$line_data"
	elif [ "$i" = 2 ]; then
		subsystem="$line_data"
	fi
	
	count=$((i=i+1))
done < ./output.txt
rm ./output.txt
ssh "build@$kvm" "ucs-kt-remove --terminate $master"
ssh "build@$kvm" "ucs-kt-remove --terminate $subsystem"
