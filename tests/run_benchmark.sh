
for size in 1000000 10000000 ; do
    for backend in TKagg agg cairo; do
	echo ${size} ${backend}
	python test_writing.py ${backend} ${size} > ${backend}_${size}.out;
     done
done
