import re
from typing import Optional


def _int_list(s):
    return [int(x) for x in re.findall(r'-?\d+', s)]

def _float_list(s):
    return [float(x) for x in re.findall(r'-?\d+\.?\d*', s)]


def is_block_start(line):
    return line.strip().startswith('seq:')


def parse_block(lines):
    data = {'cir': {}}

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        m = re.match(r'CIR\[(\d+)\]:\[(.+)\]', line)
        if m:
            anchor_idx = int(m.group(1))
            values_str = m.group(2).replace('...', '')
            data['cir'][anchor_idx] = _float_list(values_str)
            continue

        m = re.match(r'(\w+):(.*)', line)
        if not m:
            continue
        key, val = m.group(1).lower(), m.group(2).strip()

        if key == 'seq':
            data['seq_num'] = int(val)
        elif key == 'tag':
            data['tag_id'] = val
        elif key == 'anchor':
            data['anchor_ids'] = _int_list(val)
        elif key == 'dist':
            data['dist'] = _float_list(val)
        elif key == 'rsl':
            data['rsl'] = _float_list(val)
        elif key == 'fpidx':
            data['fpidx'] = _int_list(val)
        elif key == 'fprsl':
            data['fprsl'] = _float_list(val)
        elif key == 'fpns':
            data['fpns'] = _float_list(val)
        elif key == 'ppidx':
            data['ppidx'] = _int_list(val)
        elif key == 'pprsl':
            data['pprsl'] = _float_list(val)
        elif key == 'ppns':
            data['ppns'] = _float_list(val)

    required = ('seq_num', 'tag_id', 'anchor_ids', 'dist')
    if not all(k in data for k in required):
        return None

    return data
