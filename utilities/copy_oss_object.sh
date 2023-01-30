#!/bin/bash
# 
if [[ $# -eq 0 ]]
then
   data_date=$(date -d "20201218" +%Y%m%d)
elif [[ $1 == [2-3][0-9][0-9][0-9][0-1][0-9][0-3][0-9] ]]
then
   data_date=$1
else
    echo "$USAGE"
    echo "Default data_date is yesterday."
    exit 1
fi

for i in {0..15} #从20201218 到 20210102
do
    dir=$(date -d "$data_date $i days" +%Y%m%d)
    echo "$dir"
    for j in {0..1000} #每天1000个文件 
        do
        		#真正执行的时候去掉echo ""这层
                echo "oci os object copy --bucket-name <bucket> --destination-bucket <bucket> --destination-region <region> --source-object-name year=2020/month=12/day=18/part00000.parq.gz --destination-object-name  year=${dir:0:4}/month=${dir:4:2}/day=${dir:6:2}/part${j}.parq.gz"
        done
done
