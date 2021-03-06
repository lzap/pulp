from gettext import gettext as _
import gzip
import logging
import os
import traceback

from pulp.common import error_codes
from pulp.server.exceptions import PulpCodedValidationException, PulpCodedException
from verification import CHECKSUM_FUNCTIONS

_LOG = logging.getLogger(__name__)


class MetadataFileContext(object):
    """
    Context manager class for metadata file generation.
    """

    def __init__(self, metadata_file_path, checksum_type=None):
        """
        :param metadata_file_path: full path to metadata file to be generated
        :type  metadata_file_path: str
        :param checksum_type: checksum type to be used to generate and prepend checksum
                              to the file names of files. If checksum_type is None,
                              no checksum is added to the filename
        :type checksum_type: str or None
        """

        self.metadata_file_path = metadata_file_path
        self.metadata_file_handle = None
        self.checksum_type = checksum_type
        self.checksum = None
        if self.checksum_type is not None:
            checksum_function = CHECKSUM_FUNCTIONS.get(checksum_type)
            if not checksum_function:
                raise PulpCodedValidationException(
                    [PulpCodedException(error_codes.PLP1005, checksum_type=checksum_type)])
            self.checksum_constructor = checksum_function

    def __enter__(self):

        self.initialize()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if None not in (exc_type, exc_val, exc_tb):

            err_msg = '\n'.join(traceback.format_exception(exc_type, exc_val, exc_tb))
            log_msg = _('Exception occurred while writing [%(m)s]\n%(e)s')
            # any errors here should have already been caught and logged
            _LOG.debug(log_msg % {'m': self.metadata_file_path, 'e': err_msg})

        self.finalize()

        return True

    def initialize(self):
        """
        Create the new metadata file and write the header.
        """
        if self.metadata_file_handle is not None:
            # initialize has already, at least partially, been run
            return

        self._open_metadata_file_handle()
        self._write_file_header()

    def finalize(self):
        """
        Write the footer into the metadata file and close it.
        """
        if self._is_closed(self.metadata_file_handle):
            # finalize has already been run or initialize has not been run
            return

        try:
            self._write_file_footer()

        except Exception, e:
            _LOG.exception(e)

        try:
            self._close_metadata_file_handle()

        except Exception, e:
            _LOG.exception(e)

        # Add calculated checksum to the filename
        file_name = os.path.basename(self.metadata_file_path)
        if self.checksum_type is not None:
            with open(self.metadata_file_path, 'rb') as file_handle:
                content = file_handle.read()
                checksum = self.checksum_constructor(content).hexdigest()

            self.checksum = checksum
            file_name_with_checksum = checksum + '-' + file_name
            new_file_path = os.path.join(os.path.dirname(self.metadata_file_path),
                                         file_name_with_checksum)
            os.rename(self.metadata_file_path, new_file_path)
            self.metadata_file_path = new_file_path

        # Set the metadata_file_handle to None so we don't double call finalize
        self.metadata_file_handle = None

    def _open_metadata_file_handle(self):
        """
        Open the metadata file handle, creating any missing parent directories.

        If the file already exists, this will overwrite it.
        """
        assert self.metadata_file_handle is None
        _LOG.debug('Opening metadata file: %s' % self.metadata_file_path)

        if not os.path.exists(self.metadata_file_path):

            parent_dir = os.path.dirname(self.metadata_file_path)

            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, mode=0770)

            elif not os.access(parent_dir, os.R_OK | os.W_OK | os.X_OK):
                msg = _('Insufficient permissions to write metadata file in directory [%(d)s]')
                raise RuntimeError(msg % {'d': parent_dir})

        else:

            msg = _('Overwriting existing metadata file [%(p)s]')
            _LOG.warn(msg % {'p': self.metadata_file_path})

            if not os.access(self.metadata_file_path, os.R_OK | os.W_OK):
                msg = _('Insufficient permissions to overwrite [%(p)s]')
                raise RuntimeError(msg % {'p': self.metadata_file_path})

        msg = _('Opening metadata file handle for [%(p)s]')
        _LOG.debug(msg % {'p': self.metadata_file_path})

        if self.metadata_file_path.endswith('.gz'):
            self.metadata_file_handle = gzip.open(self.metadata_file_path, 'w')

        else:
            self.metadata_file_handle = open(self.metadata_file_path, 'w')

    def _write_file_header(self):
        """
        Write any headers for the metadata file
        """
        pass

    def _write_file_footer(self):
        """
        Write any file footers for the metadata file.
        """
        pass

    def _close_metadata_file_handle(self):
        """
        Flush any cached writes to the metadata file handle and close it.
        """
        _LOG.debug('Closing metadata file: %s' % self.metadata_file_path)
        if not self._is_closed(self.metadata_file_handle):
            self.metadata_file_handle.flush()
            self.metadata_file_handle.close()

    @staticmethod
    def _is_closed(file_object):
        """
        Determine if the file object has been closed. If it is None, it is assumed to be closed.

        :param file_object: a file object
        :type  file_object: file

        :return:    True if the file object is closed or is None, otherwise False
        :rtype:     bool
        """
        if file_object is None:
            # finalize has already been run or initialize has not been run
            return True

        try:
            return file_object.closed
        except AttributeError:
            # python 2.6 doesn't have a "closed" attribute on a GzipFile,
            # so we must look deeper.
            if isinstance(file_object, gzip.GzipFile):
                return file_object.myfileobj is None or file_object.myfileobj.closed
            else:
                raise


class JSONArrayFileContext(MetadataFileContext):
    """
    Context manager for writing out units as a json array.
    """

    def __init__(self, *args, **kwargs):
        """

        :param args: any positional arguments to be passed to the superclass
        :type  args: list
        :param kwargs: any keyword arguments to be passed to the superclass
        :type  kwargs: dict
        """

        super(JSONArrayFileContext, self).__init__(*args, **kwargs)
        self.units_added = False

    def _write_file_header(self):
        """
        Write out the beginning of the json file
        """
        self.metadata_file_handle.write('[')

    def _write_file_footer(self):
        """
        Write out the end of the json file
        """
        self.metadata_file_handle.write(']')

    def add_unit_metadata(self, unit):
        """
        Add the specific metadata for this unit
        """
        if self.units_added:
            self.metadata_file_handle.write(',')
        else:
            self.units_added = True
