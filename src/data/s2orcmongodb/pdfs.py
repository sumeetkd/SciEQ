import pymongo
import gzip, io, json, os
import time
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["s2orc"]
pdfs = mydb["pdfparses"]
def insertpdfdata(file):
    start = time.time()
    with gzip.open(file,'rb') as gz:
        f = io.BufferedReader(gz)
        for line in f:
            pdf_dict = json.loads(line)
            x = pdfs.insert_one(pdf_dict)
    end = time.time()
    print(end - start) 

directory = '/home/sumeetkd/DataDrive/20200705v1/full/pdf_parses'
 
# iterate over files in
# that directory
for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        print(f)
        insertpdfdata(f)
myclient.close()
