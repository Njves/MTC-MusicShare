import base64
import os
import qrcode
from qrcode import constants


def generate_link_and_qr_code(data):
    link = "https://mtc-u2hp.onrender.com/enter_room_by_url/"
    token = base64.urlsafe_b64encode(str(data).encode()).decode()
    qr = qrcode.QRCode(
        version=1,
        error_correction=constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    encode_link = link+token
    qr.add_data(encode_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # current_directory = os.getcwd()
    file_path = os.path.join("app\qrcodes", 'qr_' + str(data["id"]) + ".png")
    img.save(file_path)
    return encode_link, file_path


def decode_link(link):
    encoded_data = link.rsplit('/', 1)[-1]
    link = link.removesuffix(encoded_data)
    decoded_data = eval(base64.urlsafe_b64decode(encoded_data).decode())
    return decoded_data
