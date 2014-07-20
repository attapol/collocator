for f in arcs*
do
	echo $f
	gsed -i 's/^\([^\t]*\)\t\([^\t]*\)\t\([^\t]*\)\t\(.*\)/\1\t\2\t\3/g' $f
	head $f
done
