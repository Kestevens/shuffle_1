#Count votes of one country

# INPUT FROM TEXT FILE AND OUTPUT REDUCED RESULTS IN JSON FORMAT
from pyspark.sql import SparkSession
import json

# Initialize Spark session
spark = SparkSession.builder \
    .appName("SongVoteCount") \
    .master("local[*]") \
    .getOrCreate()

# Define the path to the input file
input_file = "generated_votes_se.txt" # OR "generated_votes_be.txt"

# Read the data from the text file into an RDD
rdd = spark.sparkContext.textFile(input_file)

# Process the RDD
mapped = rdd.map(lambda line: line.strip().split(",")) \
            .map(lambda fields: ((fields[0], fields[2]), 1))

reduced = mapped.reduceByKey(lambda a, b: a + b)

grouped = reduced.map(lambda x: (x[0][0], (x[0][1], x[1]))) \
                 .groupByKey() \
                 .mapValues(list)

result = grouped.map(lambda x: {
    "country": x[0],
    "votes": [{"song_number": song, "count": count} for song, count in x[1]]
}).collect()

# Save the result to a JSON file
output_file = "reduced_votes.json"
with open(output_file, "w") as f:
    json.dump(result, f, indent=4)

print(f"Results have been saved to {output_file}")


