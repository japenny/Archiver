import os, sys, re

class Archiver:
    def __init__(self, args):
        """
        Initialize the Archiver with command-line arguments.

        Args:
            args (list): List of command-line arguments.
                         args[1] should be the mode ('c' for create, 'x' for extract),
                         args[2:] should be the list of file paths to archive (if in 'c' mode).
        """
        self.mode = args[1]  # Archive mode: 'c' (create) or 'x' (extract)
        self.files = args[2:]  # File paths for archiving

    def archive(self):
        """
        Archives the specified files to stdout with a simple custom header format.

        Writes file size, filename length, filename, and file content to stdout.
        Exits on error.
        """
        for file in self.files:
            if not os.path.isfile(file):
                os.write(2, f"File: {file}: does not exist!\n".encode())
                sys.exit(1)

            try:
                fd = os.open(file, os.O_RDONLY)

                # Prepare header: file size (8 bytes), filename length (8 bytes), filename
                filename = os.path.basename(file).encode()
                filename_len = f"{len(filename):08d}".encode()
                filesize = f"{os.fstat(fd).st_size:08d}".encode()

                os.write(1, filesize)
                os.write(1, filename_len)
                os.write(1, filename)

                # Write file content in chunks
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
        """
        Extracts files from stdin, expecting a specific format:
        8-byte filesize, 8-byte filename length, filename, then file content.

        Creates and writes files in the current directory.
        Exits on error.
        """
        fd_in = 0  # stdin
        iters = 0  # count successful extractions

        while True:
            # Read 8-byte filesize
            filesize_byte = os.read(fd_in, 8)
            if not filesize_byte or len(filesize_byte) < 8:
                if iters == 0:
                    os.write(2, f"Error reading header byte size: Got {filesize_byte}".encode())
                    sys.exit(1)
                else:
                    break
            filesize = int(filesize_byte.decode())
            iters += 1

            # Read 8-byte filename length
            filename_len_byte = os.read(fd_in, 8)
            if not filename_len_byte or len(filename_len_byte) < 8:
                os.write(2, f"Error reading header filename length: Got {filesize_byte}".encode())
                sys.exit(1)
            filename_len = int(filename_len_byte.decode())

            # Read filename
            filename_byte = os.read(fd_in, filename_len)
            if not filename_byte or len(filename_byte) < 1:
                os.write(2, f"Error reading header filename: Got {filename_byte}".encode())
                sys.exit(1)
            filename = filename_byte.decode()

            try:
                fd_out = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

                # Read and write file content in chunks
                remaining = filesize
                while remaining > 0:
                    chunk = os.read(fd_in, min(remaining, 4096))
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
        """
        Runs the appropriate operation based on mode ('c' or 'x').

        Exits with error if mode is invalid or if files are missing in archive mode.
        """
        if self.mode == 'c':
            if not self.files:
                os.write(2, "Error: no files specified for archiving\n".encode())
                sys.exit(1)
            self.archive()
        elif self.mode == 'x':
            self.extract()
        else:
            os.write(2, f'tar: {self.mode}: No such archiver option'.encode())
            sys.exit(1)

# Entry point
if __name__ == '__main__':
    Archiver(sys.argv).run()


