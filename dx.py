from pipeline import Pipe
from pathlib import Path
import tempfile
import shutil


def add2(x):
    return x+2

def idempotent(x):
    return x

def compute(f0, f1):
    print(f0, f1)
    return f1

def return_input(f0):
    print(f0)
    return f0

def touch_output(f0, f1):
    # Helper function, returns the output
    f1.touch()
    return f1.name

def test_idempotent():
    # Make sure the input is returned exactly, even with multiprocessing
    n = 2000
    result = Pipe(range(n))(idempotent, -1)
    unexpected = list(range(n))
    assert unexpected == result

def test_shuffle():
    # Make sure data is shuffled, VERY unlikey for this to fail on it's own
    n = 2000
    result = Pipe(range(n), shuffle=True)(idempotent, 1)
    unexpected = list(range(n))
    assert unexpected != result

test_shuffle()
test_idempotent()
exit()

def create_env(names):
    '''
    Returns a temporary directory with empty files created using names.
    '''
    source = tempfile.mkdtemp()
    
    for name in names:
        (Path(source) / name).touch()

    return Path(source)

def test_check_output_files():
    '''
    Makes sure output files are created.
    '''

    input_file_names = ['apple.json', 'grape.json']
    source = create_env(input_file_names)
    dest = create_env([])

    P = Pipe(source, dest, output_suffix='.csv')(touch_output)

    expected = ['apple.csv', 'grape.csv']
    result = sorted([x.name for x in dest.glob('*.csv')])

    assert result == expected

    shutil.rmtree(source)
    shutil.rmtree(dest)



test_check_output_files()
exit()
    
x = Pipe('foo', 'bar', '.json')(compute, 2)
result = Pipe(range(3))(add2)
print(result == list(range(2,5)))

def test_size():
    n = 17
    assert len(Pipe(range(n))) == n
'''
def test_compute_math():
    n = 23
    result = Pipe(range(n))(add2, 1)
    expected = list(range(2, n+2))

    assert(result == expected)
'''

#test_compute_math()
    
#Pipe('foo', 'bar', '*.json')(compute, 1)
#Pipe('foo', 'bar', '*.json', '*.csv')(compute, 1)
#print(len(Pipe('foo', 'bar', '.json')))
#Pipe([1,2,3], 'bar', '*.json', '*.csv')(compute, 1)