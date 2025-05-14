"""Exception classes for PDF manipulator."""


class PDFManipulatorError(Exception):
    """Base exception for all PDF manipulator errors."""
    pass


class DocumentError(PDFManipulatorError):
    """Exception raised for errors in document handling."""
    pass


class RenderError(PDFManipulatorError):
    """Exception raised for errors in rendering operations."""
    pass


class ExtractorError(PDFManipulatorError):
    """Exception raised for errors in extraction operations."""
    pass