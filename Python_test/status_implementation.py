import csv

input_file = 'prototype2_celltowers.csv'
output_file = 'prototype2_celltowers_2.csv'

with open(input_file, 'r', newline='') as infile, open(output_file, 'w', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    for i, row in enumerate(reader):
        if i == 0:
            # Append new header column "status"
            row.append('status')
        else:
            # Append default value "YES" to each row
            row.append('YES')
        writer.writerow(row)
