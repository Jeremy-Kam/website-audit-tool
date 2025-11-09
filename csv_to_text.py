import csv

input_file = "matches.csv"      # Your CSV file
output_file = "matches.txt"     # Output plain text file

with open(input_file, newline="", encoding="utf-8") as infile, \
     open(output_file, "w", encoding="utf-8") as outfile:

    reader = csv.reader(infile)

    for row in reader:
        # Join the elements of the row with ", " and write to file
        line = ", ".join(row)
        outfile.write(line + "\n")

print(f"Text file saved as {output_file}")
