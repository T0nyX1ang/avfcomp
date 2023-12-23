"""Compression of an AVF file."""

import lzma

from .base import AVFParser


class AVFComp(AVFParser):
    """Compression of an AVF file."""

    def process_out(self, filename):
        with lzma.open(filename, "wb") as fout:  # use lzma for compression
            self.write_data(fout)

    def write_events(self, fout):
        fout.write(b"\x00\x01")

        op = []
        timestamps = []
        xpos = []
        ypos = []
        num_events = len(self.events)
        for event in self.events:
            op.append(event["type"])
            timestamps.append(event["gametime"] // 10)
            xpos.append(event["xpos"])
            ypos.append(event["ypos"])

        def get_diff(arr):
            diff_arr = [arr[0]]
            for i in range(len(arr) - 1):
                diff_arr.append(arr[i + 1] - arr[i])
            return diff_arr

        timestamps = get_diff(timestamps)
        xpos = get_diff(xpos)
        ypos = get_diff(ypos)

        zigzag = lambda x: (x << 1) ^ (x >> 31)
        xpos = list(map(zigzag, xpos))
        ypos = list(map(zigzag, ypos))

        min_bytes = lambda x: (x.bit_length() + 7) // 8 if x else 1
        byte_len_dt = min_bytes(max(timestamps))
        byte_len_dx = min_bytes(max(xpos))
        byte_len_dy = min_bytes(max(ypos))

        data = b""
        for i in range(num_events):
            data += op[i].to_bytes(1, byteorder="big")
        # EOF
        data += b"\x00"
        data += byte_len_dt.to_bytes(1, byteorder="big")
        for i in range(num_events):
            data += timestamps[i].to_bytes(byte_len_dt, byteorder="big")
        data += byte_len_dx.to_bytes(1, byteorder="big")
        for i in range(num_events):
            data += xpos[i].to_bytes(byte_len_dx, byteorder="big")
        data += byte_len_dy.to_bytes(1, byteorder="big")
        for i in range(num_events):
            data += ypos[i].to_bytes(byte_len_dy, byteorder="big")

        fout.write(data)

    def write_mines(self, fout):
        size = (self.rows * self.cols + 7) // 8
        data = bytearray(size)
        for mine in self.mines:
            idx = (mine[0] - 1) * self.cols + (mine[1] - 1)
            byte_idx = idx // 8
            bit_idx = idx % 8
            data[byte_idx] |= 1 << (7 - bit_idx)
        fout.write(data)
