from subprocess import Popen, PIPE
from uuid import UUID

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics import renderPDF

from rengu.io import RenguOutput, with_templating

class RenguOutputQrcode(RenguOutput):

    def __init__(self, handler=None, fd=None):
        self._fd = fd

        args = handler.split(":")

        if len(args) > 1:
            fname = args[1]
            if "{" in fname:
                self._per_instance = fname
            if fname == "LPR":
                self._fd = Popen("/usr/bin/lpr", stdin=PIPE).stdin
            else:
                self._fd = open(fname, "wb")

    @with_templating
    def __call__(self, obj: UUID | dict):

        if self._per_instance:
            self._fd = open(self._per_instance.format(**obj), "wb")

        uid = obj.get("ID", "ffffffff-ffff-ffff-ffff-ffffffffffff")
        title = obj.get("Title", "")
        by = obj.get("By", "")
        if isinstance(by, list):
            by = " /  ".join(by)
        if not by:
            by = ""

        c = canvas.Canvas(self._fd)
        c.setPageSize((2.25 * inch, 1.25 * inch))

        qr_code = qr.QrCodeWidget(BASEURL + uid)
        d1 = Drawing(0, 0)
        d1.add(qr_code)
        renderPDF.draw(d1, c, 0, 0)

        d2 = Drawing(1.25, 1.25)
        d2.add(String(0, 0, uid[0:8].lower(), fontSize=10, fontName="Helvetica"))
        d2.add(String(0, -10, title, fontSize=6, fontName="Helvetica"))
        d2.add(String(0, -20, by, fontSize=6, fontName="Helvetica"))

        renderPDF.draw(d1, c, 0, 0)
        renderPDF.draw(d2, c, inch * 1.25, inch)

        c.showPage()

        try:
            c.save()
        except TypeError:
            print("# Aborting QRCode because output stream was not a bytestream")


