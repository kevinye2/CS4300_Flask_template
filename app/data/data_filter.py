import os
import json

def getLatestDate(fname):
    with open('app/data/case_data/' + fname) as open_file:
        fd = open_file.read()
        res = json.loads(fd)
        print(res[len(res) - 1][3])

def shortenResults():
    for fname in os.listdir('app/data/case_data'):
        if '.json' in fname:
            with open('app/data/case_data/' + fname) as open_file:
                ret = []
                fd = open_file.read()
                res = json.loads(fd)
                for elem in res:
                    ret.append((elem[0], elem[1],
                        elem[2][0:min(5000, len(elem[2]))], elem[3]))
                json.dump(ret, open('app/data/case_data/v' + fname, 'w'))

def shortenSingleResult(fname):
    with open('app/data/case_data/' + fname) as open_file:
        ret = []
        fd = open_file.read()
        res = json.loads(fd)
        for elem in res:
            ret.append((elem[0], elem[1],
                elem[2][0:min(5000, len(elem[2]))], elem[3]))
        json.dump(ret, open('app/data/case_data/v' + fname, 'w'))
#shortenSingleResult('set8.json')
#getLatestDate('set5.json')
#shortenResults()

a = [[1, 2, 3], [4, 5, 6]]
b = [[7, 8, 9], [10, 11, 12]]
c = [a, b]
print([cur_elem for cur_array in c for cur_elem in cur_array])
