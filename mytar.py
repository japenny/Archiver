import os, sys, re

class Archiver:
    def __init__(self, args):
        self.mode = args[1] # Get command mode (i.e. c or x)
        self.files = args[2:] # Get all file paths provided

    def archive(self):

        for file in self.files:

            # Check file exists
            if not os.path.isfile(file):
                os.write(2, f"File: {file}: does not exist!\n".encode())
                sys.exit(1)

            try:
                fd = os.open(file, os.O_RDONLY)

                # Get header info: file byte size, filename length, and filename
                filename = os.path.basename(file).encode()
                filename_len = len(filename)
                filename_len = f"{filename_len:08d}".encode()
                file_stat = os.fstat(fd)
                filesize = file_stat.st_size
                filesize = f"{filesize:08d}".encode()

                # Write header of file: file byte size, filename length, and filename
                os.write(1, filesize)
                os.write(1, filename_len)
                os.write(1, filename)

                # Write the file contents to stdout
                while True:
                    chunk = os.read(fd, 4096)
                    if not chunk:
                        break
                    os.write(1, chunk)

            except Exception as e:
                os.write(2, f"Error archiving {file}: {str(e)}\n".encode())
                sys.exit(1)
            finally:
                os.close(fd)

    def extract(self):
        fd_in = 0
        iters = 0

        while True:

            # Read file size
            filesize_byte = os.read(fd_in, 8)
            if not filesize_byte or len(filesize_byte) < 8:
                if iters == 0:
                    os.write(2, f"Error reading header byte size: Got {filesize_byte}".encode())
                    sys.exit(1)
                else:
                    break
            iters += 1
            filesize = int(filesize_byte.decode())

            # Read filename length
            filename_len_byte = os.read(fd_in, 8)
            if not filename_len_byte or len(filename_len_byte) < 8:
                os.write(2, f"Error reading header filename length: Got {filesize_byte}".encode())
                sys.exit(1)
            filename_len = int(filename_len_byte.decode())

            # Read file name
            filename_byte = os.read(fd_in, filename_len)
            if not filename_byte or len(filename_byte) < 1:
                os.write(2, f"Error reading header filename: Got {filename_byte}".encode())
                sys.exit(1)
            filename = filename_byte.decode()

            try:
                # Create file (write only, create if doesnt exist, and clear if it already exists)
                fd_out = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

                # Write contents to file
                remaining = filesize
                while remaining > 0:
                    chunk_size = min(remaining, 4096)
                    chunk = os.read(fd_in, chunk_size)

                    # Unexpected end of input
                    if not chunk:
                        os.write(2, f"Error: Extracting read error: {remaining}".encode())
                        sys.exit(1)

                    os.write(fd_out, chunk)
                    remaining -= len(chunk)

            except Exception as e:
                os.write(2, f"Error creating file {filename}: {e}\n".encode())
                os.close(fd_out)
                sys.exit(1)
            finally:
                os.close(fd_out)

    def run(self):
        if self.mode == 'c':
            # Check if no files provided
            if not self.files:
                os.write(2, "Error: no files specified for archiving\n".encode())
                sys.exit(1)
            self.archive()
        elif self.mode == 'x':
            self.extract()
        else:
            os.write(2, f'tar: {self.mode}: No such archiver option'.encode())
            sys.exit(1)

# Run script
if __name__ == '__main__':
    Archiver(sys.argv).run()

