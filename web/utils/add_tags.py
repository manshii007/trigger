import http.client
import csv
import argparse
import json



def get_tags():
    conn = http.client.HTTPSConnection("www.backend.trigger.tessact.com")

    headers = {
        'authorization': "Token f5d079c6da23b4f56ff3b23abdf267c4fc893ff5",
        'cache-control': "no-cache",
        'postman-token': "49b0a290-eebf-8587-4571-73dd49c05c7f"
    }

    conn.request("GET", "/api/v1/tags/", headers=headers)

    res = conn.getresponse()
    data = res.read()

    print(data.decode("utf-8"))


def post_tags(tagName, ip):
    conn = http.client.HTTPConnection(ip)

    payload = "name="+tagName+"&category=Others"

    # headers = {
    #     'authorization': "Token f5d079c6da23b4f56ff3b23abdf267c4fc893ff5",
    #     'content-type': "application/x-www-form-urlencoded",
    #     'cache-control': "no-cache",
    #     'postman-token': "b510d3d4-a741-8dac-cb74-f18452a7e109"
    # }

    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'authorization': "Token 066f5ac60e1ccca396b0490f9ca814bd2647ec7e",
        'cache-control': "no-cache",
    }
    conn.request("POST", "/api/v1/tags/", payload, headers)

    res = conn.getresponse()
    data = res.read()

    print(data.decode("utf-8"))


def read_csv(filePath):
    with open(filePath, 'r') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            # row = row[1:len(row)-1]
            print(row[0])
            print(', '.join(row))
            break


def read_txt(mainFilePath, validIdPath):
    valid_ids = []
    with open(validIdPath, 'r') as txtfile:
        for row in txtfile.readlines():
            valid_ids.append(row.strip())
    words = []
    with open(mainFilePath, 'r') as txtfile:
        count = 0
        for row in txtfile.readlines():
            tagName = row[10:-1]
            if(row[0:9] in valid_ids):
                words.append(tagName)
                # post_tags(tagName)
                count += 1
                print(str(count) + "/1000")
    with open('data.json', 'w+') as dataFile:
        json.dump(words,dataFile, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file')
    parser.add_argument('-v', '--valid')
    parser.add_argument('-p', '--ip')

    args = parser.parse_args()

    if args.valid:
        read_txt(args.file, args.valid)
    else :
        with open(args.file, 'r') as data:
            data_list = json.load(data)
        for name in data_list:
            post_tags(name, args.ip)
