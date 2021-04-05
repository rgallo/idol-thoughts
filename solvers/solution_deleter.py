import os
import re
import sys


def delete_solutions(dir_path, threshold):
    pattern = re.compile(r'^Best so far - Linear fail (\d*.\d*), fail rate (\d*.\d*)%$', re.MULTILINE)
    to_delete = []
    fail_rates = {}
    job_ids = {filename.rsplit("-", 1)[0] for filename in os.listdir(dir_path) if filename.endswith("details.txt")}
    for job_id in job_ids:
        with open(os.path.join(dir_path, "{}-details.txt".format(job_id))) as details_file:
            fail_rate = float(pattern.findall(details_file.read())[0][1])
            if fail_rate > threshold:
                to_delete.append((job_id, fail_rate, "under {}".format(threshold)))
            elif fail_rate in fail_rates:
                to_delete.append((job_id, fail_rate, "duplicate of {}".format(fail_rates[fail_rate])))
            else:
                fail_rates[fail_rate] = job_id
    if to_delete:
        for job_id, fail_rate, reason in to_delete:
            print("{}: Fail rate {}, {}".format(job_id, fail_rate, reason))
        confirm = input("Continue? (y/n) ")
        if confirm == 'y':
            for filename in os.listdir(dir_path):
                if any(filename.startswith(job_id) for job_id, _, _ in to_delete):
                    os.remove(os.path.join(dir_path, filename))
        else:
            print("fine")
    else:
        print("Nothing to delete")


if __name__ == "__main__":
    delete_solutions(sys.argv[1], float(sys.argv[2]))
