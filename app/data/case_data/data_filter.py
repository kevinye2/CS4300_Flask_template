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
#shortenSingleResult('tester_static.json')
getLatestDate('set8.json')
#shortenResults()
