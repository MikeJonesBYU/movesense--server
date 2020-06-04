#!/usr/bin/env python3
import asyncio
import aiomysql
from random import randint


from constants import TIME
from tools.arff import Arff
from tools.analyzer import Analyzer
from tools.errors import CollectionError


class Collection:
    # Data Types
    INTEGER  = 'int'
    STRING   = 'string'
    REAL     = 'real'
    VALUE_NA = '?'

    # Window Defaults
    WINDOW_SIZE    = 50
    WINDOW_OVERLAP = 25

    # MySQL Settings
    HOST     = '127.0.0.1'
    PORT     = 3306
    USER     = 'girrowfe'
    PASSWORD = ''

    def __init__(self, name, data=[], attr_names=[], attr_types=[],
                 window_size=WINDOW_SIZE,
                 window_overlap=WINDOW_OVERLAP,
                 analyzer=None):
        self.name           = name
        self.data           = data
        self.attr_names     = attr_names
        self.attr_types     = attr_types
        self.window_size    = window_size
        self.window_overlap = window_overlap
        self.analyzer       = analyzer

    def import_data(self, filename):
        a = Arff(arff=filename)
        self.data.extend(a[:, :])
        self.attr_names = a.attr_names.copy()
        self.attr_types = a.attr_types.copy()

    def get_entry_by_value(self, feature_names, values):
        # Ensure that both metadata and value to filter by is sent
        if len(feature_names) != len(values):
            return None

        for i in range(len(feature_names)):
            name = feature_names[i]
            value = values[i]
            if name not in self.attr_names:
                return None

    # def get_entries_by_span(self, feature_names, start, stop, value):
        
    async def add_entry(self, data):
        entry = []
        for i in range(len(self.attr_names)):
            name = self.attr_names[i]
            type = self.attr_types[i]
            if name in data and (type == self.REAL and isinstance(data.get(name), float)):
                entry.append(float(data.get(name)))
            elif name in data and (type == self.INTEGER and isinstance(data.get(name), int)):
                entry.append(int(data.get(name)))
            elif name in data and type == self.STRING:
                entry.append(data.get(name))
            elif type == self.REAL or type == self.INTEGER:
                print('unable to enter value {} for name {}'.format(data.get(name), name))
                entry.append(float('nan'))
            else:
                entry.append(self.VALUE_NA)
        self.data.append(entry)

        # Analyze latest window if ready
        if len(self.data) % self.window_overlap == 0 and \
            len(self.data) >= self.window_size:
            analysis = await self.analyze_window(start=(-1*self.window_size))

        # Not ready yet, don't return anything
        else:
            analysis = None

        return analysis

    def write_to_file(self, filename, append=False):        
        if append:
            f = open(filename, 'a')
        else:
            f = open(filename, 'w')

        f.write('@relation {}\n'.format(self.name))
        for i in range(len(self.attr_names)):
            f.write('@attribute {} {}\n'.format(self.attr_names[i],
                                                self.attr_types[i]))

        f.write('@data\n')
        f.write('%\n% {} instances\n%\n')
        for entry in self.data:
            for value in entry[:-1]:
                f.write('{},'.format(value))
            f.write('{}\n'.format(entry[-1]))
        f.write('%\n%\n%')
        f.close()

    async def analyze_all(self, window_size=None, window_overlap=None):
        analysis = []
        # Use initialized window_overlap if not overridden
        if window_overlap is not None and isinstance(window_overlap, int):
            bo = window_overlap
        else:
            bo = self.window_overlap
        
        # Use initialized window_size if not overridden
        if window_size is not None and isinstance(window_size, int):
            bs = window_size
        else:
            bs = self.window_size

        for i in range(len(self.data) // bo):
            start = i * bs
            end = start + bs

            # Only analyze full windows
            if end >= len(self.data):
                break
            analysis.append(self.analyze_window(start, end))
        return analysis

    async def analyze_window(self, start=0, end=-1):
        window = [row[3:] for row in self.data]
        
        # TODO: Send window to be analyzed by ML & generate report
        # Placeholder analysis that finds all even timestamps in window
        # print()
        # print('COLLECTION::{}::DUMMY_ANALYSIS'.format(self.name))
        # analysis = {'name': self.name, 'values': []}
        # for entry in window:
        #     print(entry)
        #     if entry[1] % 2 == 0:
        #         analysis['values'].append(entry[1])
        # print()
        # print()
        # print('COLLECTION::{}::WINDOW_ANALYSIS'.format(self.name))
        # print('COLLECTION::{}::WINDOW {}'.format(self.name, window))
        # if self.analyzer is None:
        #     return None
        # prediction = self.analyzer.predict(window)
        # analysis = {'name': self.name, 'value': prediction}
        # print('COLLECTION::{}::PREDICTION {}'.format(self.name, prediction))
        # print()

        labels = ['jump', 'not jump', 'not jump']
        idx = randint(0, 9) % len(labels)

        analysis = {'name': self.name, 'value': labels[idx]}

        return analysis       

    # async def analyze_one(self, id):

    async def create_table(self):
        conn = await aiomysql.connect(host=self.HOST, port=self.PORT,
                                      user=self.USER, password=self.PASSWORD,
                                      db=self.name)
        cur = await conn.cursor()
        async with conn.cursor() as cur:
            # Construct create table query
            # Handle ID label manually; assumes ID is a field in the data
            create_table = ('CREATE TABLE IF NOT EXISTS {} '
                            '(id INT UNSIGNED NOT NULL AUTO_INCREMENT'
                            .format(self.name))
            for i in range(len(self.attr_names) - 1):
                name = self.attr_names[i+1]
                type = self.attr_types[i+1]
                if type == self.REAL:
                    type = 'FLOAT'
                elif type == self.INTEGER:
                    type = 'INT'
                else:
                    type = 'TEXT'
                create_table += ', {} {}'.format(name, type)
            create_table += ', PRIMARY KEY(id));'

            # Create table if not already there
            await cur.execute(create_table)
            await conn.commit()
        conn.close()

    async def save_to_db(self):
        conn = await aiomysql.connect(host=self.HOST, port=self.PORT,
                                      user=self.USER, password=self.PASSWORD,
                                      db=self.name)
        cur = await conn.cursor()
        async with conn.cursor() as cur:
            table_exists = await self.table_exists()
            if not table_exists:
                await self.create_table()

            # Update table to reflect current data state
            # Construct query
            update_query = "INSERT INTO {} ({}) values (%s".format(
                self.name, ", ".join(self.attr_names))
            for i in range(len(self.attr_names) - 1):
                update_query += ",%s"
            update_query += ") ON DUPLICATE KEY UPDATE "
            for i in range(len(self.attr_names) - 1):
                update_query += "{} = VALUES({}), ".format(
                    self.attr_names[i], self.attr_names[i])
            update_query += "{} = VALUES({})".format(
                self.attr_names[-1], self.attr_names[-1])

            # Execute query
            await cur.executemany(update_query, self.data)
            await conn.commit()

        conn.close()

    async def table_exists(self):
        exists = False
        conn = await aiomysql.connect(host=self.HOST, port=self.PORT,
                                      user=self.USER, password=self.PASSWORD,
                                      db=self.name)
        cur = await conn.cursor()
        async with conn.cursor() as cur:
            await cur.execute(("SELECT COUNT(*) "
                               "FROM information_schema.tables "
                               "WHERE {} = '{0}'".format(self.name)))
            if cur.fetchone()[0] == 1:
                exists = True
        conn.close()
        return exists

    async def load_from_db(self):
        if not self.table_exists():
            raise CollectionError('Unable to load from db: no db found!')

    def __str__(self):
        s = '__{}__\n'.format(self.name)
        s += 'attributes: ['
        for i in range(len(self.attr_names) - 1):
            if i < len(self.attr_types):
                s += '{}({})'.format(self.attr_names[i], self.attr_types[i])
            else:
                s += '{}'.format(self.attr_names[i])
            s += ','
        if i < len(self.attr_types):
            s += '{}({})]\n'.format(self.attr_names[i], self.attr_types[i])
        else:
            s += '{}]\n'.format(self.attr_names[i])
        
        s += 'data:\n{}'.format(self.data)
        return s
