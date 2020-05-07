from tools.arff import Arff

class Collection:
    def __init__(self, name, data=[], attr_names=[], attr_types=[], label_count=0):
        self.name = name
        self.data = data
        self.attr_names = attr_names
        self.attr_types = attr_types
        self.label_count=label_count

    def import_data(self, filename, label_count):
        a = Arff(arff=filename, label_count=label_count)
        self.data.extend(a[:, :])
        self.attr_names = a.attr_names.copy()
        self.attr_types = a.attr_types.copy()
        self.label_count = label_count

    def add_entry(self, data):
        entry = []
        for i in range(len(self.attr_names)):
            name = self.attr_names[i]
            type = self.attr_types[i]
            if name in data and (type == 'real' and isinstance(data.get(name), float)):
                entry.append(data.get(name))
            elif name in data and type != 'real':
                entry.append(data.get(name))
            elif type == 'real':
                entry.append(float('nan'))
            else:
                entry.append('?')
        self.data.append(entry)

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
