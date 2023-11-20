#!/usr/bin/python3
import io
import json
import struct
import sys

JSONHDR_KEY = ('byteorder', 'content-type', 'content-encoding', 'content-length')


class Protocol:
    '''
    >>> p = Protocol()
    >>> args1 = {'content': {'hello': 'world'}, 'type': 'text/json', 'encoding': 'utf-8'}
    >>> msg1 = p.encode(args1)
    >>> resp1 = p.decode(msg1)
    >>> resp1 == args1
    True
    >>> args2 = {'content': b'hello', 'type': 'binary', 'encoding': 'utf-8'}
    >>> msg2 = p.encode(args2)
    >>> resp2 = p.decode(msg2)
    >>> resp2 == args2
    True
    '''

    def encode(self, data):
        content = data['content']
        mime_typ = data['type']
        encoding = data['encoding']

        if mime_typ == 'text/json':  # text/json or binary
            content = self.json_encode(content, encoding)

        jsonhdr_val = (sys.byteorder, mime_typ, encoding, len(content))
        jsonhdr_dict = dict(zip(JSONHDR_KEY, jsonhdr_val))
        jsonhdr = self.json_encode(jsonhdr_dict)
        msg_hdr = struct.pack('>H', len(jsonhdr))
        message = msg_hdr + jsonhdr + content
        return message

    def decode(self, message):
        hdrlen = 2
        jsonhdr_len = None
        content = None

        if len(message) >= hdrlen:
            jsonhdr_len = struct.unpack('>H', message[:hdrlen])[0]
            message = message[hdrlen:]

        if jsonhdr_len is not None:
            hdrlen = jsonhdr_len
            if len(message) >= hdrlen:
                jsonhdr = self.json_decode(message[:hdrlen])
                content = message[hdrlen:]
                if set(JSONHDR_KEY) - set(jsonhdr.keys()):
                    reqhdr = (set(JSONHDR_KEY) - set(jsonhdr.keys())).pop()
                    raise ValueError('Missing required header "{}".'.format(reqhdr))

        if content is not None:
            content_len = jsonhdr['content-length']
            if not len(content) >= content_len:
                return
            content = content[:content_len]
            mime_typ = jsonhdr['content-type']
            encoding = jsonhdr['content-encoding']
            if mime_typ == 'text/json':
                content = self.json_decode(content, encoding)
            data = {'content': content, 'type': mime_typ, 'encoding': encoding}
            return data

    def json_encode(self, obj, encoding='utf-8'):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def json_decode(self, doc, encoding='utf-8'):
        tiow = io.TextIOWrapper(
            io.BytesIO(doc), encoding=encoding, newline=''
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def recv(self, sock, size=16384): 
        data = None
        msg = bytearray()
        while True:
            msg += sock.recv(size)
            data = self.decode(msg)
            if not msg or data:
                break
        return data

    def send(self, sock, data):
        msg = self.encode(data)
        sock.sendall(msg)


def proc_args(content, mime_typ='text/json', encoding='utf-8'):
    if mime_typ == 'text/json':
        upper = lambda x: str(x).upper()
        tmp = {upper(k): upper(v) for k, v in content.items()}
        for k in ('TEST_ITEM', 'MSG', 'FILE_PATH', 'NONCE', 'BOARD', 'ARGS'):
            if tmp.get(k):
                tmp[k] = content.get(k) or content[k.lower()]
        content = tmp
    return {'content': content, 'type': mime_typ, 'encoding': encoding}


if __name__ == '__main__':
    import doctest
    doctest.testmod()
