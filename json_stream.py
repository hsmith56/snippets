import json
from json import JSONDecoder
from functools import partial
from json.decoder import JSONDecodeError
import os
import logging


# helper function to create random malformatted json
def create_json(rnge_start, rnge_end, function):
    with open('badjson.txt', function) as f:
        for i in range(rnge_start, rnge_end):
            f.write('{"id": '+ f'"{i}"' + ', "name": "sid", "Random thing here": "random value here as well","dataTypeName": "meta_data", "fieldName": ":sid", "position": 0, "renderTypeName": "meta_data", "format": {}, "flags": ["hidden"]}\n')

create_json(rnge_start=0, rnge_end=1_000_000, function='w+')

class Connector:
    def __init__(self):
        self.current_offset = 0
        self.prev_offset = -1
        self.prev_file_size = 0
        self.curr_file_size = 0
        self.output_file = 'badjson.txt'


    def stream_read_json(self, decoder=JSONDecoder(), buffer_size = 8192):
        # Get the size of the file in bytes
        self.curr_file_size = os.stat(self.output_file).st_size

        with open(self.output_file, 'r') as fileobj:
            # If the file has increased in size, go to last read position
            # in order to avoid rereading lines, otherwise start from the beginning
            if self.curr_file_size > self.prev_file_size:
                fileobj.seek(self.prev_file_size)
            buffer = ""

            for chunk in iter(partial(fileobj.read, buffer_size), ""):
                buffer += chunk
                # MUST HAVE THIS LINE OTHERWIES IT ALMOST ALWAYS
                # GETS STUCK AND INFINITELY INCREASES BUFFER
                buffer = buffer.strip()

                while buffer:
                    try:
                        result, index = decoder.raw_decode(buffer)
                    
                        # This is for my fake JSON, do actual stuff here
                        self.current_offset = int(result['id'])
                        if self.current_offset > self.prev_offset:
                            self.prev_offset = self.current_offset
                            yield result

                        buffer = buffer[index:].lstrip()
                    except ValueError as e:
                        break

        self.prev_file_size = self.curr_file_size

t1 = Connector()
test = t1.stream_read_json()
# On first read file is 1_000_000 lines long, each id corresponds
# to the index so we can easily test if the object was converted to JSON or not
for index, i in enumerate(test):
    assert i['id'] == str(index), f"Failed to match index {index} to JSON in Test 1"
else:
    print('All Tests passed for initial read of 1,000,000 lines')


create_json(rnge_start=1_000_000, rnge_end=1_000_020, function='a')
# append 1_000_000:1_000_020 to the json
# The file will increase in size so this
# should only read from the new entires onwards

test = t1.stream_read_json()
for index, i in enumerate(test):
    assert i['id'] == str(index+1_000_000), f"Failed to match index {index} to JSON in Test 2"
print('All Tests passed for appending to file and starting from correct location')


create_json(rnge_start=1_000_020, rnge_end=1_000_050, function='w')
# Overwrite the whole file starting at 1_000_020 going forward
# Since the file was rewritten, start from beginning of file

test = t1.stream_read_json()
for index, i in enumerate(test):
    assert i['id'] == str(index+1_000_020), f"Failed to match index {index} to JSON in Test 3"
print('All Tests passed for new file being written to and starting over')
