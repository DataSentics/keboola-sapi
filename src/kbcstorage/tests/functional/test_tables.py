import os
import unittest
import tempfile
import csv
import warnings
from requests import exceptions
from kbcstorage.tables import Tables
from kbcstorage.buckets import Buckets


class TestTables(unittest.TestCase):
    def setUp(self):
        self.tables = Tables(os.getenv('KBC_TEST_API_URL'),
                             os.getenv('KBC_TEST_TOKEN'))
        self.buckets = Buckets(os.getenv('KBC_TEST_API_URL'),
                               os.getenv('KBC_TEST_TOKEN'))
        try:
            self.buckets.delete('in.c-py-test-tables', force=True)
        except exceptions.HTTPError as e:
            if e.response.status_code != 404:
                raise
        self.buckets.create(name='py-test-tables', stage='in')
        # https://github.com/boto/boto3/issues/454
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        try:
            self.buckets.delete('in.c-py-test-tables', force=True)
        except exceptions.HTTPError as e:
            if e.response.status_code != 404:
                raise

    def test_create_table_minimal(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        table_info = self.tables.detail(table_id)
        with self.subTest():
            self.assertEqual(table_id, table_info['id'])
        with self.subTest():
            self.assertEqual('in.c-py-test-tables', table_info['bucket']['id'])

    def test_create_table_primary_key(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
            writer.writerow({'col1': 'pong', 'col2': 'ping'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables',
                                      primary_key=['col1', 'col2'])
        table_info = self.tables.detail(table_id)
        with self.subTest():
            self.assertEqual(table_id, table_info['id'])
        with self.subTest():
            self.assertEqual('in.c-py-test-tables', table_info['bucket']['id'])
        with self.subTest():
            self.assertEqual(['col1', 'col2'], table_info['primaryKey'])

    def test_table_detail(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        table_info = self.tables.detail(table_id)
        with self.subTest():
            self.assertEqual(table_id, table_info['id'])
        with self.subTest():
            self.assertEqual('some-table', table_info['name'])
        with self.subTest():
            self.assertTrue('in.c-py-test-tables.some-table' in table_info['uri'])
        with self.subTest():
            self.assertEqual([], table_info['primaryKey'])
        with self.subTest():
            self.assertEqual(['col1', 'col2'], table_info['columns'])
        with self.subTest():
            self.assertTrue('created' in table_info)
        with self.subTest():
            self.assertTrue('lastImportDate' in table_info)
        with self.subTest():
            self.assertTrue('lastChangeDate' in table_info)
        with self.subTest():
            self.assertTrue('rowsCount' in table_info)
        with self.subTest():
            self.assertTrue('metadata' in table_info)
        with self.subTest():
            self.assertTrue('bucket' in table_info)
        with self.subTest():
            self.assertTrue('columnMetadata' in table_info)

    def test_delete_table(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        table_info = self.tables.detail(table_id)
        self.assertEqual(table_id, table_info['id'])
        self.tables.delete(table_id)
        try:
            self.tables.detail('some-totally-non-existent-table')
        except exceptions.HTTPError as e:
            if e.response.status_code != 404:
                raise

    def test_invalid_create(self):
        try:
            self.tables.detail('some-totally-non-existent-table')
        except exceptions.HTTPError as e:
            if e.response.status_code != 404:
                raise

    def test_import_table_incremental(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        table_info = self.tables.detail(table_id)
        with self.subTest():
            self.assertEqual(table_id, table_info['id'])
        with self.subTest():
            self.assertEqual(1, table_info['rowsCount'])

        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'foo', 'col2': 'bar'})
        os.close(file)
        self.tables.load(table_id=table_id, file_path=path,
                         is_incremental=True)
        table_info = self.tables.detail(table_id)
        with self.subTest():
            self.assertEqual(table_id, table_info['id'])
        with self.subTest():
            self.assertEqual(2, table_info['rowsCount'])

    def test_import_table_no_incremental(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        table_info = self.tables.detail(table_id)
        with self.subTest():
            self.assertEqual(table_id, table_info['id'])
        with self.subTest():
            self.assertEqual(1, table_info['rowsCount'])

        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'foo', 'col2': 'bar'})
        os.close(file)
        self.tables.load(table_id=table_id, file_path=path,
                         is_incremental=False)
        table_info = self.tables.detail(table_id)
        with self.subTest():
            self.assertEqual(table_id, table_info['id'])
        with self.subTest():
            self.assertEqual(1, table_info['rowsCount'])

    def test_table_preview(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
            writer.writerow({'col1': 'foo', 'col2': 'bar'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        contents = self.tables.preview(table_id=table_id)
        lines = contents.split('\n')
        self.assertEqual(['', '"col1","col2"', '"foo","bar"', '"ping","pong"'],
                         sorted(lines))

    def test_table_export(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
            writer.writerow({'col1': 'foo', 'col2': 'bar'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        result = self.tables.export(table_id=table_id)
        self.assertIsNotNone(result)

    def test_table_export_file_plain(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
            writer.writerow({'col1': 'foo', 'col2': 'bar'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        temp_path = tempfile.TemporaryDirectory()
        local_path = self.tables.export_to_file(table_id=table_id,
                                                path_name=temp_path.name,
                                                is_gzip=False)
        with open(local_path, mode='rt') as file:
            lines = file.readlines()
        self.assertEqual(['"col1","col2"\n', '"foo","bar"\n',
                          '"ping","pong"\n'],
                         sorted(lines))

    def test_table_export_file_gzip(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
            writer.writerow({'col1': 'foo', 'col2': 'bar'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        temp_path = tempfile.TemporaryDirectory()
        local_path = self.tables.export_to_file(table_id=table_id,
                                                path_name=temp_path.name,
                                                is_gzip=True)
        with open(local_path, mode='rt') as file:
            lines = file.readlines()
        self.assertEqual(['"col1","col2"\n', '"foo","bar"\n',
                          '"ping","pong"\n'],
                         sorted(lines))

    def test_table_export_sliced(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path,
                                      bucket_id='in.c-py-test-tables')
        table_info = self.tables.detail(table_id)
        with self.subTest():
            self.assertEqual(table_id, table_info['id'])
        with self.subTest():
            self.assertEqual(1, table_info['rowsCount'])

        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'foo', 'col2': 'bar'})
        os.close(file)
        self.tables.load(table_id=table_id, file_path=path,
                         is_incremental=True)
        temp_path = tempfile.TemporaryDirectory()
        local_path = self.tables.export_to_file(table_id=table_id,
                                                path_name=temp_path.name)
        with open(local_path, mode='rt') as file:
            lines = file.readlines()
        self.assertEqual(['"col1","col2"\n', '"foo","bar"\n',
                          '"ping","pong"\n'],
                         sorted(lines))

    def test_table_columns(self):
        file, path = tempfile.mkstemp(prefix='sapi-test')
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['col1', 'col2', 'col3', 'col4'],
                                    lineterminator='\n', delimiter=',',
                                    quotechar='"')
            writer.writeheader()
            writer.writerow({'col1': 'ping', 'col2': 'pong', 'col3': 'king', 'col4': 'kong'})
        os.close(file)
        table_id = self.tables.create(name='some-table', file_path=path, bucket_id='in.c-py-test-tables')
        temp_path = tempfile.TemporaryDirectory()
        local_path = self.tables.export_to_file(table_id=table_id,
                                                path_name=temp_path.name,
                                                is_gzip=False,
                                                columns=['col3', 'col2'])

        with open(local_path, mode='rt') as file:
            lines = file.readlines()
        self.assertEqual(['"col3","col2"\n', '"king","pong"\n'], sorted(lines))
