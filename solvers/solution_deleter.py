import os
import re
import sys


def delete_solutions(dir_path, threshold, patternchoice):
    if not patternchoice == "mofo":
        pattern = re.compile(r'^max underestimate (-?[\d\.]*), max overestimate (-?[\d\.]*), unexvar (-?[\d\.]*)$', re.MULTILINE)                
    else:
        pattern = re.compile(r'^Best so far - Linear fail ([-\.\d]*), fail rate ([-\.\d]*)%$', re.MULTILINE)
    to_delete = []
    fail_rates = {}
    unexvars = {}
    job_ids = {filename.rsplit("-", 1)[0] for filename in os.listdir(dir_path) if filename.endswith("details.txt")}
    if not patternchoice == "mofo":
        file_format = "-" + patternchoice + "details.txt"
    else:
        file_format = "-details.txt"
    for job_id in job_ids:
        with open(os.path.join(dir_path, "{}".format(job_id) + file_format)) as details_file:
            if not patternchoice == "mofo":
                underestimate, overestimate, unexvar = pattern.findall(details_file.read())[0]
                fail_rate = max(abs(float(underestimate)), abs(float(overestimate)))                
            else:
                fail_rate = float(pattern.findall(details_file.read())[0][1])                
            if fail_rate > threshold:
                to_delete.append((job_id, fail_rate, "under {}".format(threshold)))
            elif fail_rate in fail_rates:
                if not patternchoice == "mofo":
                    if unexvar in unexvars:
                        to_delete.append((job_id, fail_rate, "duplicate of {}".format(fail_rates[fail_rate])))
                else:
                    to_delete.append((job_id, fail_rate, "duplicate of {}".format(fail_rates[fail_rate])))
            else:
                fail_rates[fail_rate] = job_id
                if not patternchoice == "mofo":
                    unexvars[unexvar] = job_id
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
    delete_solutions(sys.argv[1], float(sys.argv[2]), sys.argv[3])
