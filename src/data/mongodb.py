import pymongo
import gzip, io, json
import os, glob, datetime

class DB_Create:


    def __init__(self):
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.mydb = self.myclient["mydatabase"]
        self.metadata = self.mydb["metadata"]
        self.pdfparse = self.mydb["pdf_parses"]
        self.datadir = "/home/sumeetkd/codes/Quazar/purchaser/S2ORC/sample/20200705v1/full"


    def __latest_entry(self, collection=None):
        """
        Calculate the datetime for the latest entry in the mongodb collection
        TODO Sort the timezone issue
        :param collection:
        Choose the collection to be analyzed
        :return:
        Returns the datetime with the tzinfo removed.
        """
        if collection is None:
            collection = self.metadata
        latest = self.metadata.find({}, {'limit': 1}).sort([('$natural',-1)])[0]
        dbtime = latest["_id"].generation_time
        return dbtime.replace(tzinfo=None)

    def __latestfile(self,type='metadata'):
        """
        Find the date of the latest file in the directory
        :param type:
        The type of batch that needs to be processed values can be metadata or pdf_parses
        :return:
        datetime of the latest file
        """
        LatestFile = max(glob.iglob(os.path.join(self.datadir, type, '*.gz')), key=os.path.getmtime)
        time = os.path.getmtime(LatestFile)
        return datetime.datetime.fromtimestamp(time)


    def filelist(self,type='metadata'):
        """
        Returns a file list for database entry
        :param type:
        Standard is metadata and can be changed to pdf_parses.
        :return:
        The file list for the type specified
        """
        file_list = []
        metadata_folder = os.path.join(self.datadir, 'metadata')
        for root, dirs, files in os.walk(metadata_folder):
            for file in files:
                if file.endswith(".gz"):
                     file_list.append(os.path.join(root, file))
        return file_list


    def insert(self, collection=None, batches=None):
        """
        Inserts the data from the batches to the mongodb collection
        :param collection:
        Name of the mongodb collection to insert the data into
        :param batches:
        List of files that will be processed and entered into database
        :return:
        Confirmation of completion
        """
        if collection is None:
            collection = self.metadata
        if batches is None:
            batches = self.filelist('metadata')
        for batch in batches:
            with gzip.open(batch,'rb') as gz:
                f = io.BufferedReader(gz)
                for line in f:
                    dict = json.loads(line)
                    x = collection.insert_one(dict)
        return print("Completed")


    def update(self):
        if self.__latest_entry() < self.__latestfile():
            self.insert()
        else:
            print("Updated metadata database")

        if self.__latest_entry(self.pdfparse) < self.__latestfile('pdf_parses'):
            self.insert(self.pdfparse, self.filelist('pdf_parses'))
        else:
            print("Updated pdf parse database")


    def create(self):
        dblist = self.myclient.list_database_names()
        if "mydatabase" in dblist:
            print("The database exists.")
            collist = self.mydb.list_collection_names()
            if ("metadata" in collist) and ("pdf_parses" in collist):
                print("The collections exist")
            self.update()
        else:
            print("Doesn't exist")
            self.insert()
            self.insert(self.pdfparse, self.filelist('pdf_parses'))
