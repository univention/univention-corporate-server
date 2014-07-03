import univention.admin.uexceptions
import bz2
import zlib
from PIL import Image
import StringIO
import magic
MIME_TYPE = magic.open(magic.MAGIC_MIME_TYPE)
MIME_TYPE.load()
MIME_DESCRIPTION = magic.open(magic.MAGIC_NONE)
MIME_DESCRIPTION.load()

UMC_ICON_BASEDIR = "/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons"

compression_mime_type_handlers = {
	"application/x-gzip": lambda x: zlib.decompress(x, 16+zlib.MAX_WBITS),
	"application/x-bzip2": bz2.decompress
}

def get_mime_type(data):
	return MIME_TYPE.buffer(data)

def get_mime_description(data):
	return MIME_DESCRIPTION.buffer(data)

def compression_mime_type_of_buffer(data):
	mime_type = get_mime_type(data)
	if mime_type in compression_mime_type_handlers:
		return (mime_type, compression_mime_type_handlers[mime_type])
	else:
		raise univention.admin.uexceptions.valueError( "Not a supported compression format: %s" % (mime_type,))

def uncompress_buffer(data):
	try:
		(mime_type, compression_mime_type_handler) = compression_mime_type_of_buffer(data)
		return (mime_type, compression_mime_type_handler(data))
	except univention.admin.uexceptions.valueError:
		return (None, data)

def uncompress_file(filename):
	with open(filename, 'r') as f:
		return uncompress_buffer(f.read())

def image_mime_type_of_buffer(data):
	mime_type = get_mime_type(data)
	if mime_type in ('image/jpeg', 'image/png', 'image/svg+xml'):
		return mime_type
	else:
		raise univention.admin.uexceptions.valueError( "Not a supported image format: %s" % (mime_type,))

def imagedimensions_of_buffer(data):
	fp = StringIO.StringIO(data)
	im=Image.open(fp)
	return im.size

def imagecategory_of_buffer(data):
 	(compression_mime_type, uncompressed_data) = uncompress_buffer(data)
	mime_type = image_mime_type_of_buffer(uncompressed_data)
	if mime_type in ('image/jpeg', 'image/png'):
		return (mime_type, compression_mime_type, "%sx%s" % imagedimensions_of_buffer(uncompressed_data))
	elif mime_type in ('image/svg+xml'):
		return (mime_type, compression_mime_type, "scalable")

def default_filename_suffix_for_mime_type(mime_type, compression_mime_type):
	if mime_type == 'image/svg+xml':
		if not compression_mime_type:
			return '.svg'
		elif compression_mime_type == 'application/x-gzip':
			return '.svgz'
	elif mime_type == 'image/png':
		return '.png'
	elif mime_type == 'image/jpeg':
		return '.jpg'
	return None
