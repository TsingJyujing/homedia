#!/bin/python
# -*- coding: utf-8 -*-

"""
Created on 2017-2-4
@author: Yuan Yi fan
管理各种各样的连接，SSH，MongoDB，PostgreSQL等等
"""

try:
    import os
    import yaml
    import json
    import paramiko
    from utility.files import walk_files


    class SSHConnection:
        def __init__(self, host, user, passwd, port=22, timeout=5):
            self.__host = host
            self.__port = port
            self.__user = user
            self.__passwd = passwd
            self.__timeout = timeout

        def __enter__(self):
            self.ssh_conn = paramiko.SSHClient()
            self.ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_conn.connect(self.__host, self.__port, username=self.__user, password=self.__passwd,
                                  timeout=self.__timeout)
            tansport = paramiko.Transport((self.__host, self.__port))
            tansport.connect(username=self.__user, password=self.__passwd)
            self.sftp_conn = paramiko.SFTPClient.from_transport(tansport)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.sftp_conn.close()
            self.ssh_conn.close()


    class ExtSSHConnection(SSHConnection):
        def __init__(self, host, user, passwd):
            SSHConnection.__init__(self, host, user, passwd)

        def write_file(self, filename, data):
            with self.sftp_conn.file(filename, "wb") as rmfp:
                rmfp.write(data)

        def write_json(self, filename, object, encode_format="UTF-8"):
            self.write_file(filename, json.dumps(object).encode(encode_format))

        def write_yaml(self, filename, object):
            self.write_file(filename, yaml.dump(object))

        def run_command(self, command):
            _, stdout, stderr = self.ssh_conn.exec_command(command)
            return (_, stdout.read(), stderr.read())

        def create_dir(self, dir_path):
            self.run_command("mkdir -p \"%s\"" % dir_path)

        def upload_walk_dir(self, local_dir, remote_dir):
            if remote_dir.endswith("/"):
                remote_dir += "/"
            all_files = walk_files(local_dir)
            for x in all_files:
                filename = os.path.split(x)[-1]
                remote_file = os.path.split(x)[0].replace(local_dir, remote_dir, 1)
                path = remote_file.replace('\\', '/')
                _ = self.ssh_conn.exec_command('mkdir -p "%s"' % path)
                remote_filename = os.path.join(path, filename)
                self.sftp_conn.put(x, remote_filename)

        def upload_dir(self, local_dir, remote_dir):
            files = os.listdir(local_dir)
            self.create_dir(remote_dir)
            for file in files:
                full_local_file = os.path.join(local_dir, file)
                if not os.path.isdir(full_local_file):
                    full_remote_file = os.path.join(remote_dir, file).replace("\\", "/")
                    self.sftp_conn.put(full_local_file, full_remote_file)

except:
    print("Error while importing yaml/paramiko\nTry: pip install pyyaml paramiko")

    class SSHConnection:
        def __init__(self):
            raise Exception("Key modules hasn't imported.")


    class ExtSSHConnection:
        def __init__(self):
            raise Exception("Key modules hasn't imported.")


try:
    import pymongo

    # generate_mongodb_connection = pymongo.MongoClient


    class MongoDBConnection:
        def __init__(self, host="127.0.0.1", port=27017):
            self.host = host
            self.port = port

        def __enter__(self):
            self.conn = pymongo.MongoClient(self.host, self.port)
            return self.conn

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.conn.close()


    class MongoDBDatabase:
        def __init__(self, db_name, host="127.0.0.1", port=27017):
            self.host = host
            self.port = port
            assert db_name is not None
            self.db_name = db_name

        def __enter__(self):
            self.conn = pymongo.MongoClient(self.host, self.port)
            return self.conn.get_database(self.db_name)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.conn.close()


    class MongoDBCollection:
        def __init__(self, db_name, coll_name, host="127.0.0.1", port=27017):
            self.host = host
            self.port = port
            assert db_name is not None
            assert coll_name is not None
            self.db_name = db_name
            self.coll_name = coll_name

        def __enter__(self):
            self.conn = pymongo.MongoClient(self.host, self.port)
            return self.conn.get_database(self.db_name).get_collection(self.coll_name)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.conn.close()
except:
    print("Warning: Error while importing pymongo.\nTry: pip install pymongo.")


    class MongoDBConnection:
        def __init__(self):
            raise Exception("Key modules hasn't imported.")


    class MongoDBDatabase:
        def __init__(self):
            raise Exception("Key modules hasn't imported.")


    class MongoDBCollection:
        def __init__(self):
            raise Exception("Key modules hasn't imported.")

try:
    import psycopg2


    class PgSQLConnection:
        def __init__(self, host="127.0.0.1", port=5432, database="postgres"):
            self.host = host
            self.port = port
            self.database = database

        def __enter__(self):
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database)
            return self.conn

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.conn.close()
except:
    print("Warning: Error while importing psycopg2.\nTry: pip install psycopg2.")


    class PgSQLConnection:
        def __init__(self):
            raise Exception("Key modules hasn't imported.")
