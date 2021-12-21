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
            f.write('{"id": '+ f'"{i}"' + ', "name": "sid", "dataTypeName": "meta_data", "fieldName": ":sid", "position": 0, "renderTypeName": "meta_data", "format": {}, "flags": ["hidden"]}\n')

create_json(rnge_start=0, rnge_end=1_000_000, function='w+')

class Connector:
    def __init__(self):
        self.current_offset = 0
        self.prev_offset = -1
        self.prev_file_size = 0
        self.curr_file_size = 0
        self.output_file = 'badjson.txt'


    def stream_read_json(self, decoder=JSONDecoder(), buffer_size = 8192):
        self.curr_file_size = os.stat(self.output_file).st_size # Get the size of the file in bytes

        with open(self.output_file, 'r') as fileobj:
            # if the file has increased in size, go to last read position
            # otherwise start from the beginning
            if self.curr_file_size > self.prev_file_size:
                fileobj.seek(self.prev_file_size)

            
            buffer = ""

            for chunk in iter(partial(fileobj.read, buffer_size), ""):
                buffer += chunk
                # MUST HAVE THIS LINE OTHERWIES IT WILL ALWAYS GET STUCK AND INFINITELY INCREASE BUFFER
                buffer = buffer.strip()

                while buffer:
                    try:
                        result, index = decoder.raw_decode(buffer)
                    
                        # this is for my fake JSON, do actual stuff here
                        self.current_offset = abs(int(result['id']))
                        if self.current_offset > self.prev_offset:
                            self.prev_offset = self.current_offset
                            yield result

                        buffer = buffer[index:].lstrip()
                    except ValueError as e:
                        break
        self.prev_file_size = self.curr_file_size

t1 = Connector()
test = t1.stream_read_json()
last = ""

# Proof that every single item gets iterated over
# last would not be 999_999 if it failed previously
for index, i in enumerate(test):
    last = i
print(last)


# append 1_000_000:1_000_020 to the json
create_json(rnge_start=1_000_000, rnge_end=1_000_020, function='a')

# The file has since increased in size so this should only read from the new entires onwards
test = t1.stream_read_json()
for i in test:
    print(i)

# Overwrite the whole file starting at 1_000_020 going forward
create_json(rnge_start=1_000_020, rnge_end=1_000_050, function='w')

# Since the file was rewritter, start from 0
test = t1.stream_read_json()
for i in test:
    print(i)
