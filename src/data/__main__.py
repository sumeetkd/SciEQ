from data import DB_Create

def main():
    """
    To be run whenever the database needs to be built or updated.
    Run this before using the remaining system
    :return:
    """
    setupDB = DB_Create()
    setupDB.create()

if __name__ == '__main__':
    main()