import os
import base64


def generate_random_txt(filename, size_mb):
    target_size = size_mb * 1024 * 1024

    with open(filename, "w") as f:
        while f.tell() < target_size:
            data = base64.b64encode(os.urandom(768)).decode() + "\n"
            f.write(data)

    print(f"Generated {filename} ({size_mb} MB)")


generate_random_txt("random_50mb.txt", 50)
