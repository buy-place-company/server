__all__ = ['gen_boundary', 'encode_and_quote', 'MultipartParam',
           'encode_string', 'encode_file_header', 'get_body_size', 'get_headers',
           'multipart_encode']

import uuid
import urllib
import re
import os
import mimetypes


def encode_and_quote(data):
    if data is None:
        return None

    data = data.encode("utf-8")
    return urllib.parse.quote_plus(data)


def gen_boundary():
    return uuid.uuid4().hex


def _strify(s):
    if s is None:
        return None

    return s.encode("utf-8")


class MultipartParam(object):

    def __init__(self, name, value=None, filename=None, filetype=None, filesize=None, fileobj=None):
        self.name = encode_and_quote(name)
        self.value = _strify(value)
        if filename is None:
            self.filename = None
        else:
            self.filename = str(filename)
            self.filename = self.filename.encode("string_escape").replace('"', '\\"')
        self.filetype = _strify(filetype)

        self.filesize = filesize
        self.fileobj = fileobj

        if self.value is not None and self.fileobj is not None:
            raise ValueError("Only one of value or fileobj may be specified")

        if fileobj is not None and filesize is None:
            # Try and determine the file size
            try:
                self.filesize = os.fstat(fileobj.fileno()).st_size
            except (OSError, AttributeError):
                try:
                    fileobj.seek(0, 2)
                    self.filesize = fileobj.tell()
                    fileobj.seek(0)
                except:
                    raise ValueError("Could not determine filesize")

    def __cmp__(self, other):
        attrs = ['name', 'value', 'filename', 'filetype', 'filesize', 'fileobj']
        myattrs = [getattr(self, a) for a in attrs]
        oattrs = [getattr(other, a) for a in attrs]
        if myattrs == oattrs:
            return 0
        if myattrs < oattrs:
            return -1
        return 1

    @classmethod
    def from_file(cls, paramname, filename):
        """Returns a new MultipartParam object constructed from the local
        file at ``filename``.
        ``filesize`` is determined by os.path.getsize(``filename``)
        ``filetype`` is determined by mimetypes.guess_type(``filename``)[0]
        ``filename`` is set to os.path.basename(``filename``)
        """

        return cls(paramname, filename=os.path.basename(filename),
                   filetype=mimetypes.guess_type(filename)[0],
                   filesize=os.path.getsize(filename),
                   fileobj=open(filename, "rb"))

    @classmethod
    def from_params(cls, params):
        """Returns a list of MultipartParam objects from a sequence of
        name, value pairs, MultipartParam instances,
        or from a mapping of names to values
        The values may be strings or file objects."""
        if hasattr(params, 'items'):
            params = params.items()

        retval = []
        for item in params:
            if isinstance(item, cls):
                retval.append(item)
                continue
            name, value = item
            if hasattr(value, 'read'):
                # Looks like a file object
                filename = getattr(value, 'name', None)
                if filename is not None:
                    file_type = mimetypes.guess_type(filename)[0]
                else:
                    file_type = None

                retval.append(cls(name=name, filename=filename,
                                  filetype=file_type, fileobj=value))
            else:
                retval.append(cls(name, value))
        return retval

    def encode_hdr(self, boundary):
        boundary = encode_and_quote(boundary)

        headers = ["--%s" % boundary]

        if self.filename:
            disposition = 'form-data; name="%s"; filename="%s"' % (self.name,
                                                                   self.filename)
        else:
            disposition = 'form-data; name="%s"' % self.name

        headers.append("Content-Disposition: %s" % disposition)

        if self.filetype:
            file_type = self.filetype
        else:
            file_type = "text/plain; charset=utf-8"

        headers.append("Content-Type: %s" % file_type)

        if self.filesize is not None:
            headers.append("Content-Length: %i" % self.filesize)
        else:
            headers.append("Content-Length: %i" % len(self.value))

        headers.append("")
        headers.append("")

        return "\r\n".join(headers)

    def encode(self, boundary):
        if self.value is None:
            value = self.fileobj.read()
        else:
            value = self.value

        if re.search("^--%s$" % re.escape(boundary), str(value), re.M):
            raise ValueError("boundary found in encoded string")

        return "%s%s\r\n" % (self.encode_hdr(boundary), value)

    def iter_encode(self, boundary, block_size=4096):
        if self.value is not None:
            yield self.encode(boundary)
        else:
            yield self.encode_hdr(boundary)
            last_block = ""
            encoded_boundary = "--%s" % encode_and_quote(boundary)
            boundary_exp = re.compile("^%s$" % re.escape(encoded_boundary), re.M)
            while True:
                block = self.fileobj.read(block_size)
                if not block:
                    yield "\r\n"
                    break
                last_block += block
                if boundary_exp.search(last_block):
                    raise ValueError("boundary found in file data")
                last_block = last_block[-len(encoded_boundary)-2:]
                yield block

    def get_size(self, boundary):
        if self.filesize is not None:
            valuesize = self.filesize
        else:
            valuesize = len(self.value)

        return len(self.encode_hdr(boundary)) + 2 + valuesize


def encode_string(boundary, name, value):
    return MultipartParam(name, value).encode(boundary)


def encode_file_header(boundary, param_name, file_size, filename=None, file_type=None):
    return MultipartParam(param_name, filesize=file_size, filename=filename,
                          filetype=file_type).encode_hdr(boundary)


def get_body_size(params, boundary):
    """Returns the number of bytes that the multipart/form-data encoding
    of ``params`` will be."""
    size = sum(p.get_size(boundary) for p in MultipartParam.from_params(params))
    return size + len(boundary) + 6


def get_headers(params, boundary):
    """Returns a dictionary with Content-Type and Content-Length headers
    for the multipart/form-data encoding of ``params``."""
    headers = {}
    boundary = urllib.parse.quote_plus(boundary)
    headers['Content-Type'] = "multipart/form-data; boundary=%s" % boundary
    headers['Content-Length'] = get_body_size(params, boundary)
    return headers


def multipart_encode(params, boundary=None):
    if boundary is None:
        boundary = gen_boundary()
    else:
        boundary = urllib.parse.quote_plus(boundary)

    headers = get_headers(params, boundary)
    params = MultipartParam.from_params(params)

    def yielder():
        """generator function to yield multipart/form-data representation
        of parameters"""
        for param in params:
            for block in param.iter_encode(boundary):
                yield block
        yield "--%s--\r\n" % boundary

    return yielder(), headers

