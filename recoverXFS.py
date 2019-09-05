import os

def main():
	fs_path = input("Enter File System Path(Partition File):")
	
	# Set default File System configuration
	fs_conf = {'blocksize': 4096, 'inodesize': 512, 'agblocks': 1024, 'agblklog': 10, 'dblocks': 4096}
	
	# Get File System configuration
	xfs_db_out = os.popen("xfs_db -r -c \"sb 0\" -c \"p\" {}".format(fs_path)).read()

	for line in xfs_db_out.split('\n'):
		if any(substring in line for substring in fs_conf.keys()):
			if "fdblocks" in line:
				continue
			keyvalue = line.split(" = ")
			fs_conf[keyvalue[0]] = int(keyvalue[1])
	
	# Run over the entire File System 
	with open("{}".format(fs_path), 'rb') as fs:
		
		# Read the FS block by block
		for block in range(0, fs_conf.get("dblocks")):
			block_data = fs.read(fs_conf.get("blocksize"))

			# Run over all potential inodes in the block
			for block_offset in range(0, fs_conf.get("blocksize"), fs_conf.get("inodesize")):
				# Check if the inode is unused/deleted by a magic number. this magic number is 7 bytes long from the begining of the inode.
				if block_data[block_offset:block_offset+8] == b'IN\x00\x00\x03\x02\x00\x00':
					# Deleted inode found!!
					# Get inode number. the inode number is located at offset 152-159 of inode
					inumber = int.from_bytes(block_data[block_offset+152:block_offset+160], byteorder='big', signed=False)
					print("Deleted inode {} found!!".format(inumber))

					# Time for data. We are looking for data extents, extents are inode's range of data blocks. The more fragmented a file, the more extents it has.
					# Extents are 16 bytes long. they're located at inode offset 176-end_of_inode.
					for inode_offset in range(176, fs_conf.get("inodesize"), 16):
						extent = block_data[block_offset+inode_offset:block_offset+inode_offset+15]
						# Ignore empty extents
						if extent == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
							continue
						# Now we can go over the data extents, they're written in binary, so we need to convert our bytes to bits.
						extent_bits = bin(int.from_bytes(extent, byteorder='big', signed=False))
						# Ignoring preallocated, unwritten extents.
						if extent_bits == '0b100000000000000000':
							continue
						
						# Some Vars
						ag = "0b{}".format(extent_bits[57:106-fs_conf.get("agblklog")])
						print(ag)
						ablock = "0b{}".format(extent_bits[107-fs_conf.get("agblklog"):106])
						count = "0b{}".format(extent_bits[107:127])
						skip = int(ag[2:], 2)*fs_conf.get("agblklog")+ablock
						print(int(skip))
						print(int(count))
						# Ignore extents beyond the filesystem.
						if int(skip)+int(count) >= fs_conf.get("dblocks"):
							continue

						print(extent_bits)
if __name__== "__main__":
	main()
