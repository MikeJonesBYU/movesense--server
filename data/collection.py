#!/usr/bin/env python3

from constants import TIME
from tools.arff import Arff


class Collection:
    # Data Types
    INTEGER       = 'int'
    STRING        = 'string'
    REAL          = 'real'
    VALUE_NA      = '?'

    # Batch Defaults
    BATCH_SIZE    = 50
    BATCH_OVERLAP = 25

    def __init__(self, name, data=[], attr_names=[], attr_types=[],
                 labels=[], batch_size=BATCH_SIZE,
                 batch_overlap=BATCH_OVERLAP):
        self.name           = name
        self.data           = data
        self.attr_names     = attr_names
        self.attr_types     = attr_types
        self.labels         = labels
        self.batch_size     = batch_size
        self.batch_overlap  = batch_overlap

    def import_data(self, filename, label_count):
        a = Arff(arff=filename, label_count=label_count)
        self.data.extend(a[:, :])
        self.attr_names = a.attr_names.copy()
        self.attr_types = a.attr_types.copy()
        self.label_count = label_count

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

        # Analyze latest batch if ready for it
        if len(self.data) % self.batch_overlap == 0 and \
            len(self.data) >= self.batch_size:
            analysis = await self.analyze_batch(start=(-1*self.batch_size))

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

    async def analyze_all(self, batch_size=None, batch_overlap=None):
        analysis = []
        # Use initialized batch_overlap if not overridden
        if batch_overlap is not None and isinstance(batch_overlap, int):
            bo = batch_overlap
        else:
            bo = self.batch_overlap
        
        # Use initialized batch_size if not overridden
        if batch_size is not None and isinstance(batch_size, int):
            bs = batch_size
        else:
            bs = self.batch_size

        for i in range(len(self.data) // bo):
            start = i * bs
            end = start + bs

            # Only analyze full batches
            if end >= len(self.data):
                break
            analysis.append(self.analyze_batch(start, end))
        return analysis

    async def analyze_batch(self, start=0, end=-1):
        batch = self.data[start:end]
        
        # TODO: Send batch to be analyzed by ML & generate report
        # Placeholder analysis that finds all even timestamps in batch
        print()
        print('COLLECTION::{}::DUMMY_ANALYSIS'.format(self.name))
        analysis = {'name': self.name, 'values': []}
        for entry in batch:
            print(entry)
            if entry[1] % 2 == 0:
                analysis['values'].append(entry[1])
        print()

        return analysis       

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
