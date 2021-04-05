import csv
import json
import os
import sys


def write_solutions(dir_path):
    job_ids = {filename.rsplit("-", 1)[0] for filename in os.listdir(dir_path) if os.path.isfile(filename)}
    for job_id in job_ids:
        if not os.path.isfile(os.path.join(dir_path, "{}-solution.json".format(job_id))):
            result = []
            for suffix in ("terms.csv", "mods.csv", "ballparkmods.csv"):
                with open(os.path.join(dir_path, "{}-{}".format(job_id, suffix))) as f:
                    for line in csv.DictReader(f):
                        result.extend([float(val) for val in (line["a"], line["b"], line["c"])])
            with open(os.path.join(dir_path, "{}-solution.json".format(job_id)), "w") as f:
                json.dump(result, f)


if __name__ == "__main__":
    write_solutions(sys.argv[1])
