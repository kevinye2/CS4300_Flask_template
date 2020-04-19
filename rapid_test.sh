tester="curl localhost:5000/inccounter"
concat=$tester
for i in {0..2000}
do
 concat="${concat} & ${tester}"
done
eval $concat
