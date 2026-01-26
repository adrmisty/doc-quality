# doctype.py
# /supported knowledge object types (for now: PDF) /
# adriana r.f.
# jan-2026
import os
from enum import Enum

class DocType(Enum):
    """Support for document extension type."""

    PDF = 'pdf'
    POWERPOINT = 'ppt'
    
    @classmethod
    def get_file_type(cls, file_name: str) -> 'DocType':
        """Decoupled selection of file type extension of a given file."""
        _, file_extension = os.path.splitext(file_name)
        file_extension = file_extension.removeprefix('.')
        match file_extension:
            case 'pdf':
                return cls.PDF
            case 'pptx':
                #TODO: extend file extensions supported
                return NotImplementedError(f'> (!) Document quality assessment for PowerPoints not yet supported!!')
            case _:
                raise NotImplementedError(f'> (!) Document quality assessment for {file_extension} not yet supported!')
